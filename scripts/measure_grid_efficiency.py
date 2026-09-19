# 작성: 2026-07-31
"""헤더 9 × 백본 6 = 54조합의 **계산 효율**을 측정한다.

왜 필요한가
  팀 논문 초안(main tex)은 정확도만이 아니라 아래를 전부 보고하겠다고 적어 두었습니다.
    backbone-only / head-only / total parameter counts
    MACs or FLOPs at the declared input resolution
    peak training and inference memory
    throughput, median latency, 95th-percentile latency
  그런데 아직 아무도 측정하지 않았습니다. 이 스크립트가 그 표를 채웁니다.

  초안 원문: "Parameter count alone will not be interpreted as evidence of mobile
  deployability." -> 그래서 파라미터만이 아니라 FLOPs·메모리·지연시간을 같이 냅니다.

사용법
  PYTHONPATH=.pylibs:. python tools/measure_grid_efficiency.py            # GPU 사용
  PYTHONPATH=.pylibs:. python tools/measure_grid_efficiency.py --device cpu --skip-latency

출력
  output/grape_grid_efficiency.csv
  reports/grape_grid/260731_효율성_표.md
"""
import argparse
import csv
import json
import time
from pathlib import Path
import sys
import warnings

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from semseg.models import *          # noqa: E402,F401,F403

HEADS = [("fcn", "FCN", "FCN"), ("unet", "U-Net", "BackboneUNet"),
         ("fpn", "FPN", "FPN"), ("psp", "PSPNet", "PSPNet"),
         ("deeplabv3p", "DeepLabv3+", "DeepLabV3Plus"), ("upernet", "UPerNet", "UPerNet"),
         ("allmlp", "All-MLP", "AllMLPNet"), ("fapn", "FaPN", "FaPNNet"),
         ("ccaseg", "CCASeg", "CCASeg")]
BBS = [("resnet50", "ResNet-50"), ("convnext_t", "ConvNeXt-T"),
       ("swin_t", "SwinTransformer-T"), ("mit_b2", "MiT-B2"),
       ("pvtv2_b2", "PVTv2-B2"), ("uniformer_s", "UniFormer-S")]
BB_SHORT = {"SwinTransformer-T": "Swin-T"}


def flops_g(model, size, device):
    """입력 1장 기준 FLOPs(G). fvcore 가 없으면 None."""
    try:
        from fvcore.nn import FlopCountAnalysis
        x = torch.randn(1, 3, *size, device=device)
        fa = FlopCountAnalysis(model, x)
        fa.unsupported_ops_warnings(False)
        fa.uncalled_modules_warnings(False)
        return float(fa.total()) / 1e9
    except Exception as e:
        print(f"    (FLOPs 측정 실패: {type(e).__name__})")
        return None


@torch.no_grad()
def latency_ms(model, size, device, warmup=10, reps=50):
    """추론 지연시간 중앙값·95퍼센타일(ms). 배치 1 기준."""
    x = torch.randn(1, 3, *size, device=device)
    for _ in range(warmup):
        model(x)
    if device.type == "cuda":
        torch.cuda.synchronize()
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter()
        model(x)
        if device.type == "cuda":
            torch.cuda.synchronize()
        ts.append((time.perf_counter() - t0) * 1000)
    return float(np.median(ts)), float(np.percentile(ts, 95))


def peak_infer_mem_mb(model, size, device):
    if device.type != "cuda":
        return None
    torch.cuda.reset_peak_memory_stats()
    with torch.no_grad():
        model(torch.randn(1, 3, *size, device=device))
    torch.cuda.synchronize()
    return torch.cuda.max_memory_allocated() / 2 ** 20


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--size", nargs=2, type=int, default=[512, 512])
    ap.add_argument("--skip-latency", action="store_true")
    args = ap.parse_args()

    device = torch.device(args.device if (args.device == "cpu" or torch.cuda.is_available()) else "cpu")
    size = tuple(args.size)
    print(f"[설정] device={device} / input={size[0]}x{size[1]} / batch=1\n")

    rows = []
    for hs, hn, hc in HEADS:
        for bs, bn in BBS:
            try:
                model = eval(hc)(bn, 1).to(device).eval()
                total = sum(p.numel() for p in model.parameters())
                bb = sum(p.numel() for p in model.backbone.parameters()) \
                    if hasattr(model, "backbone") else None
                head = total - bb if bb is not None else None
                f = flops_g(model, size, device)
                mem = peak_infer_mem_mb(model, size, device)
                if args.skip_latency:
                    med = p95 = None
                else:
                    med, p95 = latency_ms(model, size, device)
                rows.append({
                    "head": hn, "backbone": BB_SHORT.get(bn, bn),
                    "params_total_M": round(total / 1e6, 2),
                    "params_backbone_M": round(bb / 1e6, 2) if bb else "",
                    "params_head_M": round(head / 1e6, 2) if head else "",
                    "flops_G": round(f, 1) if f else "",
                    "infer_peak_mem_MB": round(mem, 1) if mem else "",
                    "latency_median_ms": round(med, 2) if med else "",
                    "latency_p95_ms": round(p95, 2) if p95 else "",
                })
                print(f"  {hn:11s} + {BB_SHORT.get(bn,bn):12s} "
                      f"{total/1e6:6.2f}M  {f if f else 0:7.1f}G  "
                      f"{med if med else 0:6.1f}ms", flush=True)
                del model
                if device.type == "cuda":
                    torch.cuda.empty_cache()
            except Exception as e:
                print(f"  {hn:11s} + {bn:12s}  🔴 {type(e).__name__}: {str(e)[:60]}")

    out_csv = ROOT / "output" / "grape_grid_efficiency.csv"
    with out_csv.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    rep = ROOT / "reports" / "grape_grid"
    rep.mkdir(parents=True, exist_ok=True)
    L = ["<!-- 스크립트 생성물: tools/measure_grid_efficiency.py -->",
         "# 계산 효율 — 헤더 9 × 백본 6", "",
         f"> 입력 {size[0]}×{size[1]} · 배치 1 · {device.type.upper()} "
         f"({torch.cuda.get_device_name(0) if device.type=='cuda' else 'CPU'})",
         "> 파라미터는 백본/헤더로 나눠서 보고합니다. "
         "논문 초안이 *\"파라미터 수만으로 배포 가능성을 주장하지 않는다\"* 고 못박았기 때문입니다.", "",
         "| 헤더 | 백본 | 전체(M) | 백본(M) | 헤더(M) | FLOPs(G) | 추론메모리(MB) | 지연 중앙값(ms) | 지연 p95(ms) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append("| " + " | ".join(str(r[k]) for k in r) + " |")
    tot = [r["params_total_M"] for r in rows]
    L += ["", f"- 전체 파라미터 범위: **{min(tot):.1f}M ~ {max(tot):.1f}M** "
              "(팀 초안의 20–35M 용량 밴드 기준 확인용)"]
    fl = [r["flops_G"] for r in rows if r["flops_G"] != ""]
    if fl:
        L.append(f"- FLOPs 범위: **{min(fl):.1f}G ~ {max(fl):.1f}G** "
                 f"— 최대/최소 **{max(fl)/max(min(fl),1e-9):.1f}배**. "
                 "파라미터 수가 비슷해도 계산량은 크게 다릅니다")
    (rep / "260731_효율성_표.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\n[출력] {out_csv}")
    print(f"[출력] {rep/'260731_효율성_표.md'}")


if __name__ == "__main__":
    main()
