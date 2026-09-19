# 작성: 2026-08-02
"""포도 54조합을 cv2~cv5 에서도 돌리기 위한 config 생성기.

왜 필요한가
  0731 그리드는 cv1 **단일 분할**만 돌렸다. 그래서 논문이
    - "분할 간 분산을 추정할 수 없다"를 한계로 안고 있고
    - 표 3의 "Five 70/10/20 repetitions"가 계획값(거짓)으로 남아 있으며
    - Friedman 블록이 같은 test 20장의 반복이라 exploratory 로 내려야 한다.
  cv2~cv5 를 채우면 위 세 개가 전부 해결된다.

무엇을 하는가
  configs/grape_grid_0731/*.yaml (54개, cv1) 를 읽어 cv2~cv5 판을 만든다.
  바꾸는 줄은 **딱 2줄** — DATASET.ROOT 와 SAVE_DIR. 하이퍼파라미터는 손대지 않는다.
  기존 cv1 결과는 건드리지 않는다(출력 폴더가 다름).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "configs" / "grape_grid_0731"
DST = ROOT / "configs" / "grape_grid5_0802"
DATA = "/data/project/2026summer/kds0206/dataset_certh_grape_toy100_5fold"

DST.mkdir(parents=True, exist_ok=True)
n = 0
for src in sorted(SRC.glob("grape_*_cv1.yaml")):
    stem = src.stem[:-4]                       # grape_unet_convnext_t
    text = src.read_text(encoding="utf-8")
    for k in (2, 3, 4, 5):
        out = text
        out = re.sub(r"(DATASET:\n(?:.*\n)*?\s+ROOT\s*:\s*')[^']+(')",
                     lambda m: f"{m.group(1)}{DATA}/cv{k}{m.group(2)}", out, count=1)
        out = re.sub(r"(SAVE_DIR\s*:\s*')[^']+(')",
                     lambda m: f"{m.group(1)}output/grape_grid5_runs/{stem}_cv{k}{m.group(2)}",
                     out, count=1)
        p = DST / f"{stem}_cv{k}.yaml"
        p.write_text(out, encoding="utf-8")
        n += 1
print(f"생성 {n}개 -> {DST}")
