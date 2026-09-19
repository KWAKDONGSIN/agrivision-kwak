# 작성: 2026-07-31
"""포도 전체 그리드(헤더 9 × 백본 6 = 54조합) 결과 분석.

이 스크립트의 핵심 — **통계 검정력 문제를 설계로 푼다**

팀 논문 초안은 Friedman 블록을 20개(4데이터셋×5반복), 비교대상을 63개로 잡았습니다.
비교대상 k 가 블록 N 보다 3배 많으면 Nemenyi 임계차 CD 가 커져서
웬만한 순위차가 전부 "유의하지 않음"으로 나옵니다.

그래서 여기서는 **주효과를 분리해서** 검정합니다.

    ① 헤더 주효과 : 블록 = (백본 6 × 테스트사진 20) = 120블록, k = 9   ← 검정력 충분
    ② 백본 주효과 : 블록 = (헤더 9 × 테스트사진 20) = 180블록, k = 6   ← 검정력 충분
    ③ 54조합 전체 : 블록 = 사진 20, k = 54                              ← 참고용(약함)

①②가 주 분석, ③은 부록입니다. 교수님이 말씀하신 "그룹핑"(녹취록 17:24)과도 맞습니다.

산출물
  reports/grape_grid/260731_포도그리드_결과표.md
  reports/grape_grid/figures/  (히트맵·주효과·loss·박스플롯)
  output/grape_grid_{results.csv,per_image.json,stats.json}
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

CFG_DIR = ROOT / "configs" / "grape_grid_0731"
OUT_DIR = ROOT / "output" / "grape_grid_runs"
REP_DIR = ROOT / "reports" / "grape_grid"
FIG_DIR = REP_DIR / "figures"

HEADS = [("fcn", "FCN"), ("unet", "U-Net"), ("fpn", "FPN"), ("psp", "PSPNet"),
         ("deeplabv3p", "DeepLabv3+"), ("upernet", "UPerNet"), ("allmlp", "All-MLP"),
         ("fapn", "FaPN"), ("ccaseg", "CCASeg")]
BBS = [("resnet50", "ResNet-50"), ("convnext_t", "ConvNeXt-T"),
       ("swin_t", "Swin-T"), ("mit_b2", "MiT-B2"),
       ("pvtv2_b2", "PVTv2-B2"), ("uniformer_s", "UniFormer-S")]


def _resolve(name):
    return name.replace("-", "").replace("_", "")


def _binary(loss_cfg):
    return loss_cfg["NAME"] in {"BinaryCrossEntropy", "BCEDice", "IoUFocal"}


@torch.no_grad()
def per_image_metrics(model, dataset, device, loss_cfg):
    model.eval()
    loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=2)
    rows = []
    for idx, (img, lbl) in enumerate(loader):
        img, lbl = img.to(device), lbl.to(device)
        logits = model(img)
        if logits.ndim == 3:
            logits = logits.unsqueeze(1)
        if logits.shape[-2:] != lbl.shape[-2:]:
            logits = F.interpolate(logits, size=lbl.shape[-2:], mode="bilinear", align_corners=False)
        pred = ((torch.sigmoid(logits) >= 0.5).squeeze(1).long() if _binary(loss_cfg)
                else logits.softmax(dim=1).argmax(dim=1))
        valid = lbl != dataset.ignore_label
        p, g = (pred == 1) & valid, (lbl == 1) & valid
        tp, fp, fn = float((p & g).sum()), float((p & ~g).sum()), float((~p & g).sum())
        eps = 1e-9
        rows.append({"image": Path(dataset.files[idx]).name,
                     "fg_IoU": tp / (tp + fp + fn + eps),
                     "fg_Dice": 2 * tp / (2 * tp + fp + fn + eps),
                     "fg_Precision": tp / (tp + fp + eps),
                     "fg_Recall": tp / (tp + fn + eps)})
    return rows


def friedman_nemenyi(mat, names, alpha=0.05):
    """mat: (N블록, k방법). Friedman + Nemenyi 임계차."""
    from scipy.stats import friedmanchisquare
    N, k = mat.shape
    stat, p = friedmanchisquare(*[mat[:, j] for j in range(k)])
    ranks = np.apply_along_axis(lambda r: k + 1 - (np.argsort(np.argsort(r)) + 1), 1, mat)
    mean_rank = ranks.mean(axis=0)
    try:                                     # Nemenyi 임계차
        from scipy.stats import studentized_range
        q = studentized_range.ppf(1 - alpha, k, np.inf) / np.sqrt(2)
        cd = float(q * np.sqrt(k * (k + 1) / (6 * N)))
    except Exception:
        cd = None
    out = {"n_blocks": int(N), "k": int(k), "friedman_stat": float(stat),
           "friedman_p": float(p), "critical_difference": cd,
           "mean_rank": {names[j]: float(mean_rank[j]) for j in range(k)},
           "nemenyi": []}
    if cd is not None and p < alpha:
        for i, j in combinations(range(k), 2):
            d = abs(mean_rank[i] - mean_rank[j])
            out["nemenyi"].append({"a": names[i], "b": names[j],
                                   "rank_diff": float(d), "significant": bool(d > cd)})
    return out


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    per_img, summary, hist = {}, {}, {}
    for hs, hn in HEADS:
        for bs, bn in BBS:
            run = f"grape_{hs}_{bs}_cv1"
            cfg_p, d = CFG_DIR / f"{run}.yaml", OUT_DIR / run
            ck = sorted(d.glob("*_best.pth")) if d.is_dir() else []
            if not cfg_p.is_file() or not ck:
                print(f"[건너뜀] {run}")
                continue
            cfg = yaml.safe_load(cfg_p.read_text(encoding="utf-8"))
            ds = eval(cfg["DATASET"]["NAME"])(cfg["DATASET"]["ROOT"], "test",
                                              get_val_augmentation(cfg["EVAL"]["IMAGE_SIZE"]))
            model = eval(_resolve(cfg["MODEL"]["NAME"]))(cfg["MODEL"]["BACKBONE"], 1).to(device)
            st = torch.load(ck[0], map_location="cpu")
            model.load_state_dict(st["state_dict"] if isinstance(st, dict) and "state_dict" in st else st)
            rows = per_image_metrics(model, ds, device, cfg["LOSS"])
            per_img[(hn, bn)] = rows
            summary[(hn, bn)] = {m: float(np.mean([r[m] for r in rows]))
                                 for m in ("fg_IoU", "fg_Dice", "fg_Precision", "fg_Recall")}
            summary[(hn, bn)]["fg_IoU_std"] = float(np.std([r["fg_IoU"] for r in rows]))
            summary[(hn, bn)]["params_M"] = sum(p.numel() for p in model.parameters()) / 1e6
            hp = d / "training_history.json"
            hist[(hn, bn)] = json.loads(hp.read_text(encoding="utf-8")) if hp.is_file() else []
            if hist[(hn, bn)]:
                summary[(hn, bn)]["minutes"] = round(
                    sum(h["epoch_seconds"] for h in hist[(hn, bn)]) / 60, 1)
            print(f"[완료] {hn:11s} + {bn:12s}  fg_IoU {summary[(hn,bn)]['fg_IoU']:.4f}", flush=True)
            del model
            torch.cuda.empty_cache()

    if not per_img:
        print("🔴 평가할 런이 없습니다.")
        return
    REP_DIR.mkdir(parents=True, exist_ok=True)

    head_names = [hn for _, hn in HEADS if any((hn, bn) in per_img for _, bn in BBS)]
    bb_names = [bn for _, bn in BBS if any((hn, bn) in per_img for _, hn in HEADS)]
    images = sorted({r["image"] for rows in per_img.values() for r in rows})
    full = all((h, b) in per_img for h in head_names for b in bb_names)

    def score(h, b, im, metric="fg_IoU"):
        return next(r[metric] for r in per_img[(h, b)] if r["image"] == im)

    # ── 표 (9x6 평균) ────────────────────────────────────────────
    M = np.full((len(head_names), len(bb_names)), np.nan)
    for i, h in enumerate(head_names):
        for j, b in enumerate(bb_names):
            if (h, b) in summary:
                M[i, j] = summary[(h, b)]["fg_IoU"]

    with (ROOT / "output" / "grape_grid_results.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["head", "backbone", "fg_IoU", "fg_IoU_std", "fg_Dice",
                    "fg_Precision", "fg_Recall", "params_M", "minutes"])
        for h in head_names:
            for b in bb_names:
                if (h, b) in summary:
                    s = summary[(h, b)]
                    w.writerow([h, b, round(s["fg_IoU"], 4), round(s["fg_IoU_std"], 4),
                                round(s["fg_Dice"], 4), round(s["fg_Precision"], 4),
                                round(s["fg_Recall"], 4), round(s["params_M"], 2),
                                s.get("minutes", "")])
    (ROOT / "output" / "grape_grid_per_image.json").write_text(
        json.dumps({f"{h}|{b}": v for (h, b), v in per_img.items()},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 통계 ─────────────────────────────────────────────────────
    stats = {}
    if full:
        # ① 헤더 주효과 — 블록 = 백본 × 사진
        blocks = [[score(h, b, im) for h in head_names] for b in bb_names for im in images]
        stats["head_main_effect"] = friedman_nemenyi(np.array(blocks), head_names)
        # ② 백본 주효과 — 블록 = 헤더 × 사진
        blocks = [[score(h, b, im) for b in bb_names] for h in head_names for im in images]
        stats["backbone_main_effect"] = friedman_nemenyi(np.array(blocks), bb_names)
        # ③ 전체 54조합 — 블록 = 사진 (참고용)
        combos = [(h, b) for h in head_names for b in bb_names]
        blocks = [[score(h, b, im) for h, b in combos] for im in images]
        stats["all_combinations"] = friedman_nemenyi(
            np.array(blocks), [f"{h}+{b}" for h, b in combos])
        (ROOT / "output" / "grape_grid_stats.json").write_text(
            json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 그림 ─────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(8.6, 8.0))
    im_ = ax.imshow(M, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(bb_names)), bb_names, rotation=30, ha="right")
    ax.set_yticks(range(len(head_names)), head_names)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if not np.isnan(M[i, j]):
                ax.text(j, i, f"{M[i,j]:.3f}", ha="center", va="center", fontsize=8,
                        color="white" if M[i, j] < np.nanmean(M) else "black")
    fig.colorbar(im_, ax=ax, label="Test foreground IoU", shrink=0.8)
    ax.set_title("CERTH grape toy — head x backbone (test fg IoU)")
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_heatmap.png", dpi=180); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    hm = np.nanmean(M, axis=1); bm = np.nanmean(M, axis=0)
    o = np.argsort(-hm)
    axes[0].bar([head_names[i] for i in o], hm[o], color="tab:blue")
    axes[0].set(title="Head main effect (mean over backbones)", ylabel="Test fg IoU")
    plt.setp(axes[0].get_xticklabels(), rotation=30, ha="right")
    o = np.argsort(-bm)
    axes[1].bar([bb_names[i] for i in o], bm[o], color="tab:orange")
    axes[1].set(title="Backbone main effect (mean over heads)")
    plt.setp(axes[1].get_xticklabels(), rotation=30, ha="right")
    for a in axes:
        a.grid(axis="y", alpha=0.25)
        a.set_ylim(max(0, np.nanmin(M) - 0.05), min(1, np.nanmax(M) + 0.03))
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_main_effects.png", dpi=180); plt.close(fig)

    # ── 마크다운 표 ──────────────────────────────────────────────
    L = ["<!-- 스크립트 생성물: tools/analyze_grape_grid_0731.py -->",
         "# 포도(CERTH) 전체 그리드 결과 — 헤더 9 × 백본 6", "",
         "> 데이터: CERTH train 2,000장에서 100장(seed 42), 7:1:2, 576×1024",
         "> 설정: 200 epoch · early stop 끔 · val 매 epoch · 512 랜덤크롭 · batch 2×ACCUM 4",
         "> ⚠️ MambaVision-T 제외 — V100(sm_70)에서 mamba_ssm 커널이 동작하지 않음", "",
         "## 1. test 전경 IoU (20장 평균)", "",
         "| 헤더 \\ 백본 | " + " | ".join(bb_names) + " | **평균** |",
         "|---" * (len(bb_names) + 2) + "|"]
    for i, h in enumerate(head_names):
        cells = [f"{M[i,j]:.4f}" if not np.isnan(M[i, j]) else "—" for j in range(len(bb_names))]
        L.append(f"| **{h}** | " + " | ".join(cells) + f" | **{np.nanmean(M[i]):.4f}** |")
    L.append("| **평균** | " + " | ".join(f"**{np.nanmean(M[:,j]):.4f}**"
                                          for j in range(len(bb_names))) + " | |")
    best = np.unravel_index(np.nanargmax(M), M.shape)
    L += ["", f"최고 조합: **{head_names[best[0]]} + {bb_names[best[1]]}** "
              f"(fg_IoU {M[best]:.4f})",
          f"헤더 폭 {np.nanmax(np.nanmean(M,1))-np.nanmin(np.nanmean(M,1)):.4f} / "
          f"백본 폭 {np.nanmax(np.nanmean(M,0))-np.nanmin(np.nanmean(M,0)):.4f}"
          "  ← 큰 쪽이 성능을 더 좌우합니다", ""]

    if stats:
        L += ["## 2. 통계 검정", "",
              "> **주효과를 분리해서 검정했습니다.** 54조합을 한꺼번에 비교하면 "
              "블록(20)보다 비교대상(54)이 많아 사후검정이 거의 안 나옵니다.", ""]
        for key, title in [("head_main_effect", "① 헤더 주효과 (블록 = 백본 × 사진)"),
                           ("backbone_main_effect", "② 백본 주효과 (블록 = 헤더 × 사진)"),
                           ("all_combinations", "③ 54조합 전체 (참고용 — 검정력 낮음)")]:
            st = stats[key]
            sig = "차이 있음" if st["friedman_p"] < 0.05 else "차이 없다고 볼 수 없음"
            L += [f"### {title}", "",
                  f"- Friedman χ² = {st['friedman_stat']:.3f}, p = {st['friedman_p']:.4g} "
                  f"(블록 **{st['n_blocks']}** × 대상 **{st['k']}**) → **{sig}**",
                  f"- Nemenyi 임계차 CD = "
                  + (f"{st['critical_difference']:.3f}" if st["critical_difference"] else "계산 불가"),
                  "- 평균순위(1위가 최고): " + ", ".join(
                      f"{k} {v:.2f}" for k, v in sorted(st["mean_rank"].items(),
                                                        key=lambda x: x[1])[:10]), ""]
            sigs = [n for n in st["nemenyi"] if n["significant"]]
            if sigs:
                L += [f"- 유의한 쌍 {len(sigs)}개 (상위 10개):", ""]
                for n in sorted(sigs, key=lambda x: -x["rank_diff"])[:10]:
                    L.append(f"  - {n['a']} vs {n['b']} — 순위차 {n['rank_diff']:.2f} ✅")
                L.append("")
            elif st["nemenyi"]:
                L += ["- 사후검정에서 유의한 쌍 **없음** (CD 가 큼)", ""]

    L += ["## 3. 그림", "",
          "| 파일 | 내용 |", "|---|---|",
          "| `figures/fig_heatmap.png` | 헤더×백본 9×6 히트맵 |",
          "| `figures/fig_main_effects.png` | 헤더 주효과 / 백본 주효과 막대 |", "",
          "## 4. 한계", "",
          "- 100장(전체의 4%) · 분할 1개(cv1)뿐 → **본 실험이 아니라 파이프라인·설계 검증용**",
          "- 평가가 `CenterCrop(512)` 이라 576×1024 기준 화면의 약 44%만 채점됩니다",
          "- MambaVision-T 미포함(하드웨어 제약) → 7백본이 아닌 **6백본**",
          ]
    (REP_DIR / "260731_포도그리드_결과표.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\n[출력] {REP_DIR/'260731_포도그리드_결과표.md'}")


if __name__ == "__main__":
    main()
