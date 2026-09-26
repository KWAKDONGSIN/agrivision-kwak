# C23 도우미 _ex_tile(본보기 둘레 칸 자르기)이 칸보다 큰 본보기에서도 터지지 않는지 GPU 없이 확인한다
import ast, sys
from pathlib import Path
import cv2, numpy as np

SRC = Path(__file__).resolve().parents[2] / "ai_helper/sam_server.py"
if len(sys.argv) > 1:
    SRC = Path(sys.argv[1])
tree = ast.parse(SRC.read_text(encoding="utf-8"))
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_ex_tile")
ns = {"cv2": cv2, "np": np}
exec(compile(ast.Module([fn], []), str(SRC), "exec"), ns)
_ex_tile = ns["_ex_tile"]

def T_of(em):
    A = int(em.sum()); d = float(np.sqrt(4 * A / np.pi))
    return d

bad = 0
def check(name, H, W, ex0, ey0, em, want_piece=None):
    global bad
    d = T_of(em); T = int(min(max(10 * d, 256), 1024, W, H))
    try:
        fx, fy, big = _ex_tile(em, ex0, ey0, W, H, T)
    except Exception as e:
        print("실패", name, e); bad += 1; return
    ok = big.shape == (T, T) and 0 <= fx <= W - T and 0 <= fy <= H - T and big.sum() > 0
    # 칸 안의 본보기 픽셀은 사진 좌표 그대로 옮겨졌는가
    ys, xs = np.nonzero(big)
    ok &= bool(em[ys + fy - ey0, xs + fx - ex0].all())
    if want_piece is not None:
        ok &= int(big.sum()) == want_piece
    print("통과" if ok else "실패", name, "T=%d fx=%d fy=%d 칸 안 %d/%d" % (T, fx, fy, big.sum(), em.sum()))
    bad += not ok

# 1) 재현 사례: H1500·W2000, 본보기 네모 60×800 안에 30×30 조각 둘(위·아래 끝)
em = np.zeros((800, 60), bool); em[:30, :30] = True; em[-30:, -30:] = True
check("떨어진 두 조각(세로)", 1500, 2000, 900, 300, em, want_piece=900)
# 2) 가로로 떨어진 두 조각, 크기가 다르면 큰 조각이 칸 안에
em = np.zeros((60, 1500), bool); em[:20, :20] = True; em[:, -50:] = True
check("떨어진 두 조각(가로·큰 쪽)", 1500, 2000, 100, 700, em, want_piece=3000)
# 3) 평범한 한 조각(옛 동작과 같아야 함)
em = np.zeros((40, 40), bool); cv2.circle(em.view(np.uint8), (20, 20), 18, 1, -1); em = em.astype(bool)
check("한 조각", 1500, 2000, 500, 500, em, want_piece=int(em.sum()))
# 4) 사진 모서리에 붙은 본보기
check("모서리", 1500, 2000, 1960, 1460, em, want_piece=int(em.sum()))
print("C23 확인", "통과" if not bad else "실패 %d" % bad)
sys.exit(1 if bad else 0)
