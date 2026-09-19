# 작성: 2026-07-30
"""포도(CERTH) 토이 실험 4조합의 결과를 한 번에 정리한다.

0730 교수님 지시
  녹취록 45:42  "로스부터 해가지고 모델 비교하는 플롯부터 해가지고 나름 통계도
                한번 돌려보고 결과를 한번 다 채워보라고요"

하는 일
  1) 4조합 각각의 best 체크포인트로 **test 20장을 사진 한 장씩** 평가
     -> 사진별 전경 IoU/Dice/Precision/Recall  (통계 검정의 블록이 된다)
  2) 표: output/grape_toy_results.csv  +  reports/grape_toy/260730_포도토이_결과표.md
  3) 통계: Friedman 검정(4조합 x 20장 블록) + 유의하면 Wilcoxon 사후검정(Holm 보정)
  4) 그림 4장 -> reports/grape_toy/figures/
       fig_loss_curves.png       학습/검증 loss 곡선 (4조합 한 판, y축 공유)
       fig_val_fg_iou.png        에폭별 검증 전경 IoU
       fig_test_bar.png          test 전경 IoU 막대 (오차막대 = 사진별 표준편차)
       fig_per_image_box.png     사진별 IoU 분포 박스플롯

왜 사진 단위인가
  토이 실험은 분할이 1개(cv1)뿐이라 폴드 평균을 낼 수 없다. 대신 test 20장을
  **대응 블록**으로 보면 같은 사진을 4조합이 각각 맞히므로 대응표본 검정이 성립한다.
  (0723 미팅에서 확정된 원칙 — 모델 비교는 대응표본으로 한다)
"""
import csv
import json
import sys
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml
from torch.nn import functional as F
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semseg.models import *          # noqa: E402,F401,F403
from semseg.datasets import *        # noqa: E402,F401,F403
from semseg.augmentations import get_val_augmentation   # noqa: E402

CFG_DIR = ROOT / "configs" / "grape_toy_0730"
OUT_DIR = ROOT / "output" / "grape_toy_runs"
REP_DIR = ROOT / "reports" / "grape_toy"
FIG_DIR = REP_DIR / "figures"

# 사람이 읽을 이름 (그림·표에 쓸 것)
PRETTY = {
    "grape_unet_resnet50_bcedice_cv1":     "U-Net + ResNet-50",
    "grape_unet_convnext_t_bcedice_cv1":   "U-Net + ConvNeXt-T",
    "grape_fapn_resnet50_bcedice_cv1":     "FaPN + ResNet-50",
    "grape_fapn_convnext_t_bcedice_cv1":   "FaPN + ConvNeXt-T",
}
ORDER = list(PRETTY)


def _resolve_model_name(name: str) -> str:
    return name.replace("-", "").replace("_", "")


def _binary(loss_cfg) -> bool:
    return loss_cfg["NAME"] in {"BinaryCrossEntropy", "BCEDice", "IoUFocal"}


def build_model(cfg, n_classes, device):
    m_cfg, loss_cfg = cfg["MODEL"], cfg["LOSS"]
    out_ch = 1 if _binary(loss_cfg) else n_classes
    model = eval(_resolve_model_name(m_cfg["NAME"]))(m_cfg["BACKBONE"], out_ch)
    return model.to(device)


def find_ckpt(run: str):
    d = OUT_DIR / run
    if not d.is_dir():
        return None
    best = sorted(d.glob("*_best.pth"))
    if best:
        return best[0]
    any_ckpt = sorted(d.glob("*.pth"))
    return any_ckpt[0] if any_ckpt else None


@torch.no_grad()
def per_image_metrics(model, dataset, device, loss_cfg):
    """사진 한 장씩 전경(포도) IoU/Dice/Precision/Recall 을 낸다."""
    model.eval()
    loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=2)
    rows = []
    for idx, (img, lbl) in enumerate(loader):
        img, lbl = img.to(device), lbl.to(device)
        logits = model(img)
        if logits.ndim == 3:
            logits = logits.unsqueeze(1)
        if logits.shape[-2:] != lbl.shape[-2:]:
            logits = F.interpolate(logits, size=lbl.shape[-2:],
                                   mode="bilinear", align_corners=False)
        if _binary(loss_cfg):
            pred = (torch.sigmoid(logits) >= 0.5).squeeze(1).long()
        else:
            pred = logits.softmax(dim=1).argmax(dim=1)

        valid = lbl != dataset.ignore_label
        p = (pred == 1) & valid
        g = (lbl == 1) & valid
        tp = float((p & g).sum())
        fp = float((p & ~g).sum())
        fn = float((~p & g).sum())
        eps = 1e-9
        rows.append({
            "image": Path(dataset.files[idx]).name,
            "fg_IoU":       tp / (tp + fp + fn + eps),
            "fg_Dice":      2 * tp / (2 * tp + fp + fn + eps),
            "fg_Precision": tp / (tp + fp + eps),
            "fg_Recall":    tp / (tp + fn + eps),
            "gt_fg_ratio":  float(g.sum()) / max(1.0, float(valid.sum())),
        })
    return rows


def load_history(run: str):
    p = OUT_DIR / run / "training_history.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return []


def friedman_and_posthoc(mat, names):
    """mat: (n_block, n_model). Friedman -> 유의하면 Wilcoxon 쌍대비교 + Holm 보정."""
    from scipy.stats import friedmanchisquare, wilcoxon

    n_block, n_model = mat.shape
    stat, p = friedmanchisquare(*[mat[:, j] for j in range(n_model)])
    # 평균 순위 (값이 클수록 좋으므로 부호를 뒤집어 순위를 매긴다 -> 1위가 가장 좋음)
    ranks = np.apply_along_axis(
        lambda r: len(r) + 1 - (np.argsort(np.argsort(r)) + 1), 1, mat)
    mean_rank = ranks.mean(axis=0)

    out = {"n_blocks": int(n_block), "n_models": int(n_model),
           "friedman_stat": float(stat), "friedman_p": float(p),
           "mean_rank": {names[j]: float(mean_rank[j]) for j in range(n_model)},
           "posthoc": []}

    if p < 0.05:
        pairs = list(combinations(range(n_model), 2))
        raw = []
        for i, j in pairs:
            d = mat[:, i] - mat[:, j]
            if np.allclose(d, 0):
                raw.append(1.0)
            else:
                raw.append(float(wilcoxon(mat[:, i], mat[:, j]).pvalue))
        # Holm 보정
        order = np.argsort(raw)
        adj = np.empty(len(raw))
        running = 0.0
        for k, o in enumerate(order):
            val = (len(raw) - k) * raw[o]
            running = max(running, val)
            adj[o] = min(1.0, running)
        for (i, j), r, a in zip(pairs, raw, adj):
            out["posthoc"].append({
                "a": names[i], "b": names[j],
                "median_diff": float(np.median(mat[:, i] - mat[:, j])),
                "wilcoxon_p": r, "holm_p": float(a),
                "significant": bool(a < 0.05),
            })
    return out


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    runs, per_img, summary, hist = [], {}, {}, {}
    for run in ORDER:
        cfg_p = CFG_DIR / f"{run}.yaml"
        ckpt = find_ckpt(run)
        if not cfg_p.is_file() or ckpt is None:
            print(f"[건너뜀] {run} — config 또는 체크포인트 없음")
            continue
        cfg = yaml.safe_load(cfg_p.read_text(encoding="utf-8"))
        ds = eval(cfg["DATASET"]["NAME"])(
            cfg["DATASET"]["ROOT"], "test",
            get_val_augmentation(cfg["EVAL"]["IMAGE_SIZE"]))
        model = build_model(cfg, ds.n_classes, device)
        state = torch.load(ckpt, map_location="cpu")
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        model.load_state_dict(state)
        rows = per_image_metrics(model, ds, device, cfg["LOSS"])
        per_img[run] = rows
        hist[run] = load_history(run)
        summary[run] = {k: float(np.mean([r[k] for r in rows]))
                        for k in ("fg_IoU", "fg_Dice", "fg_Precision", "fg_Recall")}
        summary[run]["fg_IoU_std"] = float(np.std([r["fg_IoU"] for r in rows]))
        summary[run]["n_test"] = len(rows)
        summary[run]["checkpoint"] = str(ckpt.relative_to(ROOT))
        if hist[run]:
            summary[run]["epochs_run"] = len(hist[run])
            summary[run]["total_minutes"] = round(
                sum(h["epoch_seconds"] for h in hist[run]) / 60, 1)
            vl = [(h["epoch"], h["val_loss"]) for h in hist[run] if h.get("val_loss") is not None]
            if vl:
                be = min(vl, key=lambda t: t[1])
                summary[run]["best_epoch"] = be[0]
                summary[run]["best_val_loss"] = round(be[1], 6)
        runs.append(run)
        print(f"[완료] {PRETTY[run]}  test fg_IoU {summary[run]['fg_IoU']:.4f}")

    if not runs:
        print("🔴 평가할 런이 하나도 없습니다.")
        return

    REP_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "output" / "grape_toy_per_image.json").write_text(
        json.dumps(per_img, ensure_ascii=False, indent=2), encoding="utf-8")

    with (ROOT / "output" / "grape_toy_results.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["run", "combo", "fg_IoU", "fg_IoU_std", "fg_Dice",
                    "fg_Precision", "fg_Recall", "best_epoch", "best_val_loss",
                    "epochs_run", "total_minutes", "n_test"])
        for r in runs:
            s = summary[r]
            w.writerow([r, PRETTY[r], round(s["fg_IoU"], 4), round(s["fg_IoU_std"], 4),
                        round(s["fg_Dice"], 4), round(s["fg_Precision"], 4),
                        round(s["fg_Recall"], 4), s.get("best_epoch", ""),
                        s.get("best_val_loss", ""), s.get("epochs_run", ""),
                        s.get("total_minutes", ""), s["n_test"]])

    # ---------------- 통계 ----------------
    stats = {}
    if len(runs) >= 3:
        common = set(r["image"] for r in per_img[runs[0]])
        for r in runs[1:]:
            common &= set(x["image"] for x in per_img[r])
        common = sorted(common)
        for metric in ("fg_IoU", "fg_Dice"):
            mat = np.array([[next(x[metric] for x in per_img[r] if x["image"] == im)
                             for r in runs] for im in common])
            stats[metric] = friedman_and_posthoc(mat, [PRETTY[r] for r in runs])
        (ROOT / "output" / "grape_toy_stats.json").write_text(
            json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------------- 그림 ----------------
    colors = plt.cm.tab10(np.linspace(0, 1, 10))

    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)
    for k, r in enumerate(runs):
        h = hist[r]
        if not h:
            continue
        ep = [x["epoch"] for x in h]
        ax[0].plot(ep, [x["train_loss"] for x in h], color=colors[k], label=PRETTY[r])
        v = [(x["epoch"], x["val_loss"]) for x in h if x.get("val_loss") is not None]
        if v:
            ax[1].plot([a for a, _ in v], [b for _, b in v], color=colors[k], label=PRETTY[r])
    ax[0].set(title="Training loss", xlabel="Epoch", ylabel="Loss")
    ax[1].set(title="Validation loss", xlabel="Epoch")
    for a in ax:
        a.grid(alpha=0.25)
        a.set_ylim(bottom=0)
    ax[1].legend(fontsize=9)
    fig.suptitle("CERTH grape toy (100 images, 70/10/20) — loss curves")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_loss_curves.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    for k, r in enumerate(runs):
        v = [(x["epoch"], x["val_fg_iou"]) for x in hist[r] if x.get("val_fg_iou") is not None]
        if v:
            ax.plot([a for a, _ in v], [b for _, b in v], color=colors[k], label=PRETTY[r])
    ax.set(xlabel="Epoch", ylabel="Validation foreground IoU", ylim=(0, 1))
    ax.grid(alpha=0.25)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_val_fg_iou.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    names = [PRETTY[r] for r in runs]
    vals = [summary[r]["fg_IoU"] for r in runs]
    errs = [summary[r]["fg_IoU_std"] for r in runs]
    bars = ax.bar(names, vals, yerr=errs, capsize=4,
                  color=[colors[k] for k in range(len(runs))])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.015, f"{v:.3f}",
                ha="center", fontsize=9)
    ax.set(ylabel="Test foreground IoU", ylim=(0, 1))
    ax.grid(axis="y", alpha=0.25)
    plt.setp(ax.get_xticklabels(), rotation=12, ha="right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_test_bar.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    bp_kw = {"showmeans": True}
    # matplotlib 3.9 에서 labels -> tick_labels 로 이름이 바뀌었습니다. 둘 다 지원하도록.
    try:
        ax.boxplot([[x["fg_IoU"] for x in per_img[r]] for r in runs],
                   tick_labels=names, **bp_kw)
    except TypeError:
        ax.boxplot([[x["fg_IoU"] for x in per_img[r]] for r in runs],
                   labels=names, **bp_kw)
    ax.set(ylabel="Per-image foreground IoU", ylim=(0, 1))
    ax.grid(axis="y", alpha=0.25)
    plt.setp(ax.get_xticklabels(), rotation=12, ha="right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_per_image_box.png", dpi=180)
    plt.close(fig)

    # ---------------- 표 (마크다운) ----------------
    L = ["<!-- 스크립트 생성물. 손으로 고치지 마세요: tools/analyze_grape_toy_0730.py -->",
         "# 포도(CERTH) 토이 실험 결과 — 4조합", "",
         "> 데이터: CERTH Grape train 2,000장에서 **100장 무작위 추출**(seed 42), "
         "7:1:2 = 70/10/20, 576x1024로 리사이즈(비율 유지, 화소수는 768x768과 동일)",
         "> 설정: 200 epoch · early stopping 끔 · validation 매 epoch · "
         "512x512 랜덤크롭 · batch 2 x ACCUM 4 · BCEDice · AdamW 1e-4", "",
         "## 1. test 성적 (20장 평균)", "",
         "| 조합 | 전경 IoU | 전경 Dice | Precision | Recall | best epoch | 학습시간(분) |",
         "|---|---|---|---|---|---|---|"]
    best = max(runs, key=lambda r: summary[r]["fg_IoU"])
    for r in runs:
        s = summary[r]
        mark = " **★**" if r == best else ""
        L.append(f"| {PRETTY[r]}{mark} | {s['fg_IoU']:.4f} ± {s['fg_IoU_std']:.4f} | "
                 f"{s['fg_Dice']:.4f} | {s['fg_Precision']:.4f} | {s['fg_Recall']:.4f} | "
                 f"{s.get('best_epoch','-')} | {s.get('total_minutes','-')} |")
    L += ["", f"최고 조합: **{PRETTY[best]}** (전경 IoU {summary[best]['fg_IoU']:.4f})", ""]

    if stats:
        L += ["## 2. 통계 검정 (사진 20장을 대응 블록으로 본 Friedman)", ""]
        for metric, st in stats.items():
            sig = "차이 있음" if st["friedman_p"] < 0.05 else "차이 없다고 볼 수 없음"
            L += [f"### {metric}", "",
                  f"- Friedman χ² = {st['friedman_stat']:.4f}, "
                  f"p = {st['friedman_p']:.4g} (블록 {st['n_blocks']}장 × 조합 {st['n_models']}개) → **{sig}**",
                  "- 평균 순위(1위가 가장 좋음): " +
                  ", ".join(f"{k} {v:.2f}" for k, v in
                            sorted(st["mean_rank"].items(), key=lambda x: x[1])), ""]
            if st["posthoc"]:
                L += ["| 비교 | 중앙값 차 | Wilcoxon p | Holm 보정 p | 유의? |", "|---|---|---|---|---|"]
                for ph in st["posthoc"]:
                    L.append(f"| {ph['a']} vs {ph['b']} | {ph['median_diff']:+.4f} | "
                             f"{ph['wilcoxon_p']:.4g} | {ph['holm_p']:.4g} | "
                             f"{'✅' if ph['significant'] else '—'} |")
                L.append("")

    L += ["## 3. 그림", "",
          "| 파일 | 내용 |", "|---|---|",
          "| `figures/fig_loss_curves.png` | 학습/검증 loss 곡선 (y축 공유) |",
          "| `figures/fig_val_fg_iou.png` | 에폭별 검증 전경 IoU |",
          "| `figures/fig_test_bar.png` | test 전경 IoU 막대 (오차막대=사진별 표준편차) |",
          "| `figures/fig_per_image_box.png` | 사진별 IoU 분포 |", "",
          "## 4. 원자료", "",
          "- `output/grape_toy_results.csv` — 조합별 요약",
          "- `output/grape_toy_per_image.json` — 사진 20장 × 4조합 전부",
          "- `output/grape_toy_stats.json` — 검정 결과",
          "", "## 5. 한계 (논문에 반드시 적을 것)", "",
          "- 분할이 **1개(cv1)뿐**이므로 폴드 간 분산을 모릅니다. 통계는 **사진 단위 대응표본**입니다.",
          "- 100장은 전체 2,502장의 **4%** 입니다. 본 실험 수치가 아니라 파이프라인 점검용입니다.",
          "- 평가는 `CenterCrop(512)` 이라 **사진 가운데 512×512만 채점**됩니다(코드 현행 방식).",
          "  576×1024 기준으로 화면의 약 44%입니다. 전체 화면 평가로 바꾸려면 코드 수정이 필요합니다.",
          ]
    (REP_DIR / "260730_포도토이_결과표.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\n[출력] {REP_DIR/'260730_포도토이_결과표.md'}")
    print(f"[출력] 그림 4장 -> {FIG_DIR}")


if __name__ == "__main__":
    main()
