"""붙어 있는 과실을 «한 알씩» 쪼개는 알고리즘 (거리변환 + watershed).

━━ 왜 필요한가 (0810 랩미팅 재검토, 2026-08-10) ━━
교수님 04:02 "오브젝트가 우리가 개수 셀 수 있나요? ... 오브젝트 디텍션이면 바운딩 박스가
있어서 몇 개가 들어가는지 알 수 있는데 얘는 그게 없잖아요"
교수님 05:06 "그냥 알고리즘적으로 만들 수 있을 것 같긴 하거든요 ... 아니면 오브젝트
디텍션을 돌리던가"
교수님 13:11 "정확하게 디텍션 알고리즘을 테스트할 건 아니기 때문에 그냥 알고리즘 돌려서
나온 결과를 기반으로 플롯만 만들면 된다"

즉 요구사항의 핵심은 **«과일 하나하나가 구별돼야 개수를 셀 수 있다»** 이다.
connected components(붙은 흰 덩어리 = 1개)만으로는 이 요구를 못 채운다.
사과 1,001장 전수 실측: 정답 장당 40.4개인데 CC 는 33.1개 = **18.2% 적게** 셌다.
이 방법(watershed)은 40.7개(+0.7%)로 거의 일치한다.

━━ 방법 ━━
1. 마스크를 이진화한다.
2. 거리변환(distance transform) — 각 전경 픽셀에서 «가장 가까운 배경까지의 거리».
   열매 한 알의 **중심일수록 값이 커진다**. 즉 이 값의 봉우리 = 열매 한 알의 중심.
3. 그 봉우리들을 찾는다(peak_local_max). 봉우리 사이 최소 간격은 열매 반지름에 비례해
   자동으로 정한다(사진마다 열매 크기가 다르므로 고정값을 쓰면 안 됨).
4. 봉우리를 씨앗(marker)으로 watershed 를 돌려 덩어리를 알알이 나눈다.

━━ 정확도 (사과 정답 = 마스크 인스턴스 ID 로 실측) ━━
`tools/validate_instance_split.py` 참고. PEAK_FRAC 값은 그 검증으로 골랐다.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage
from skimage.feature import peak_local_max
from skimage.segmentation import watershed

MIN_AREA = 10        # 이보다 작은 조각은 잡티로 보고 버린다
PEAK_FRAC = 1.1      # 봉우리 사이 최소 간격 = 추정 반지름 × 이 값 (사과 정답으로 튜닝)
RADIUS_PCT = 90      # 반지름 추정 = 거리변환 값의 상위 백분위수

# 🔴 과일마다 «개체»를 어떻게 얻는지가 다르다.
# 2026-08-10 갱신 — 정답 인스턴스가 있는 데이터셋이 3개로 늘었다.
#   사과   마스크 픽셀값 = 인스턴스 ID
#   복숭아 peach-data COCO 폴리곤 (125장 977개)          → tools/peach_gt.py
#   포도   CERTH COCO RLE, 송이 단위 (2,502장 9,832송이) → tools/grape_gt.py
#   블루베리 정답 없음(원본이 이진 마스크뿐) → 분리 알고리즘 + 각주로 한계 명시
PRIMARY = {"blueberry": "watershed", "apple": "gt", "peach": "gt", "grape": "gt"}

# 정답을 못 쓸 때(파일이 없을 때) 물러설 방법. 포도는 라벨이 송이 단위라 쪼개면 안 된다.
FALLBACK = {"blueberry": "watershed", "apple": "watershed",
            "peach": "watershed", "grape": "cc"}

_S8 = np.ones((3, 3), int)


def label_cc(binary: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """connected components (옛 방법). 반환 = (라벨맵, 살아남은 라벨 번호들)"""
    lab, n = ndimage.label(binary, structure=_S8)
    if n == 0:
        return lab, np.zeros(0, int)
    areas = np.bincount(lab.ravel())[1:]
    idx = np.nonzero(areas >= MIN_AREA)[0] + 1
    return lab, idx


def split_instances(binary: np.ndarray,
                    peak_frac: float = PEAK_FRAC) -> tuple[np.ndarray, np.ndarray]:
    """붙은 덩어리를 알알이 쪼갠 라벨맵을 만든다. 반환 = (라벨맵, 살아남은 라벨 번호들)

    binary 가 비어 있으면 빈 결과를 돌려준다.
    """
    if not binary.any():
        return np.zeros(binary.shape, np.int32), np.zeros(0, int)

    dist = ndimage.distance_transform_edt(binary)
    r = float(np.percentile(dist[binary], RADIUS_PCT))     # 전형적인 열매 «반지름»
    min_dist = max(2, int(round(r * peak_frac)))

    peaks = peak_local_max(dist, min_distance=min_dist, labels=binary,
                           exclude_border=False)
    if len(peaks) == 0:
        return label_cc(binary)

    markers = np.zeros(binary.shape, np.int32)
    markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)
    lab = watershed(-dist, markers, mask=binary)

    areas = np.bincount(lab.ravel())
    idx = np.nonzero(areas[1:] >= MIN_AREA)[0] + 1
    return lab, idx


def label_gt(raw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """마스크 픽셀값이 곧 인스턴스 ID인 경우(사과). 라벨을 그대로 개체로 쓴다."""
    ids, cnts = np.unique(raw, return_counts=True)
    keep = (ids > 0) & (cnts >= MIN_AREA)
    return raw.astype(np.int32), ids[keep].astype(int)


def label_instances(raw: np.ndarray, fruit: str, stem: str | None = None,
                    prefer_gt: bool = True) -> tuple[np.ndarray, np.ndarray, str]:
    """그림·통계에서 «개체»를 뽑는 단일 창구. 반환 = (라벨맵, 라벨번호들, 방법이름)

    prefer_gt=True 면 정답 어노테이션이 있는 과일은 정답을 쓴다.
    prefer_gt=False 면 4과일을 같은 알고리즘 잣대로 재고 싶을 때 쓴다(비교·검증용).
    """
    binary = raw > 0
    H, W = raw.shape

    if prefer_gt:
        if fruit == "apple":
            # ⚠️ 예전에는 `raw.max() > 1` 일 때만 정답으로 봤는데, 열매가 «1번» 하나뿐인
            #    사진이 정답 대신 watershed 로 새어 나가 개수가 4개 어긋났다(2026-08-10).
            #    MinneApple 마스크는 만들 때부터 인스턴스 ID라 조건 없이 정답으로 쓴다.
            lab, idx = label_gt(raw)
            return lab, idx, "라벨의 인스턴스 ID (정답)"
        if fruit == "peach" and stem:
            import peach_gt
            if peach_gt.has(stem):
                lab, idx = peach_gt.label_map(stem, H, W)
                return lab, idx, "COCO 폴리곤 (정답)"
        if fruit == "grape" and stem:
            import grape_gt
            if grape_gt.has(stem):
                lab, idx = grape_gt.label_map(stem, H, W)
                return lab, idx, "CERTH 인스턴스 마스크 (정답, 송이 단위)"

    if FALLBACK[fruit] == "watershed":
        lab, idx = split_instances(binary)
        return lab, idx, "거리변환+watershed 분리"
    lab, idx = label_cc(binary)
    return lab, idx, "덩어리 그대로"


def centroids_of(lab: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """라벨맵에서 각 개체의 중심 좌표 (N,2). idx 가 비면 (0,2)."""
    if len(idx) == 0:
        return np.zeros((0, 2))
    return np.array(ndimage.center_of_mass(lab > 0, lab, idx))


def areas_of(lab: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """각 개체의 픽셀 넓이."""
    if len(idx) == 0:
        return np.zeros(0, int)
    return np.bincount(lab.ravel())[idx].astype(int)
