"""학습 로그에서 **학습시간·RAM·VRAM**을 뽑아 CSV로 만든다.

왜 필요한가 (교수님 0720 지시 ④, 0727 재확인)
  결과 제시 순서가 Loss → Precision/Recall → Dice/IoU → **학습시간 + GPU 메모리** → 정성분석
  인데, `train.py`는 이 값들을 **화면(stdout)에만** 찍고 TensorBoard에는 안 남긴다.
  그래서 `aggregate_results.py`(TensorBoard를 읽음)로는 이 열을 만들 수 없다.
  → 스윕 로그를 직접 긁어서 채운다.

로그 구조
    config : configs/blueberry_ccaseg_resnet_50_bcedice_cv1.yaml   <- 런 시작 표시
    ... (학습 진행) ...
    Total Training Time  00:57:48                                   <- 런 종료 통계
    Average Epoch Time   49.11 s
    Average RAM Usage    123.04 GB
    Average VRAM Usage   413.69 MB
    Peak VRAM Usage      518.94 MB

  한 로그 파일에 여러 런이 이어 붙어 있으므로, `config :` 줄을 만나면 그 다음
  `config :` 전까지를 그 런의 구간으로 본다.

주의
  같은 런이 여러 로그에 중복으로 나올 수 있다(재실행 흔적).
  그때는 **가장 최근에 수정된 로그 파일의 값**을 채택한다.

사용 예
  $PY tools/parse_run_cost.py                       # logs/ 전체 → output/run_cost.csv
  $PY tools/parse_run_cost.py --fold 1              # cv1만
"""
import argparse
import csv
import re
import shlex
import subprocess
from pathlib import Path

CFG_RE = re.compile(r'config\s*:\s*\S*?([\w.\-]+)\.yaml')
# 옛 스윕 로그(2026-07-20 이전)에는 'config :' 줄이 없고 아래 배너만 있다.
#   ========== upernet + ResNetD-50 START ==========
# 이때는 배너의 헤더·백본 + **파일명의 cv 번호**로 런 이름을 복원한다.
BANNER_RE = re.compile(r'=+\s*([a-z0-9]+)\s*\+\s*([A-Za-z0-9._-]+)\s+START')
FOLD_IN_FILENAME_RE = re.compile(r'cv(\d+)')
# 배너 표기 -> config 파일에서 쓰는 백본 이름
BACKBONE_ALIAS = {
    'ResNet-50': 'resnet_50', 'ResNetD-50': 'resnetd_50',
    'ConvNeXt-T': 'convnext_t', 'UniFormer-S': 'uniformer_s',
    'PoolFormer-S36': 'poolformer_s36', 'SwinTransformer-T': 'swin_t',
    'Swin-T': 'swin_t', 'PVTv2-B2': 'pvtv2_b2', 'MiT-B2': 'mit_b2',
}
STAT_RES = {
    'total_time':     re.compile(r'Total Training Time\s+(\d+:\d+:\d+)'),
    'avg_epoch_sec':  re.compile(r'Average Epoch Time\s+([\d.]+)\s*s'),
    'avg_ram_gb':     re.compile(r'Average RAM Usage\s+([\d.]+)\s*GB'),
    'avg_vram_mb':    re.compile(r'Average VRAM Usage\s+([\d.]+)\s*MB'),
    'peak_vram_mb':   re.compile(r'Peak VRAM Usage\s+([\d.]+)\s*MB'),
}
# blueberry_<head>_<backbone>_bcedice_cv<N>
NAME_RE = re.compile(r'^blueberry_(.+?)_(bcedice)_cv(\d+)$')
HEADS = ('ccaseg', 'mask2former', 'oneformer', 'upernet', 'lightham',
         'bisenetv2', 'fpn', 'condnet', 'fapn', 'birefnet')


def split_head_backbone(mid: str):
    """'ccaseg_resnet_50' -> ('ccaseg', 'resnet_50'). 헤더 이름은 알려진 목록으로 맞춘다."""
    for h in sorted(HEADS, key=len, reverse=True):
        if mid == h:
            return h, ''
        if mid.startswith(h + '_'):
            return h, mid[len(h) + 1:]
    head, _, backbone = mid.partition('_')      # 모르는 헤더면 첫 토큰을 헤더로
    return head, backbone


def hms_to_sec(s: str) -> int:
    h, m, sec = (int(x) for x in s.split(':'))
    return h * 3600 + m * 60 + sec


# 로그가 3.2GB인데 tqdm이 줄바꿈 대신 '\r'를 쓰기 때문에, 파이썬으로 읽으면
# 한 '줄'이 100MB가 되어 매우 느리다. tr로 \r을 \n으로 바꾼 뒤 grep으로 필요한
# 줄만 걸러서 받는다 (C 속도라 수백 배 빠르다).
GREP_PAT = r'config[[:space:]]*:|START ==========|Total Training Time|Average Epoch Time|'\
           r'Average RAM Usage|Average VRAM Usage|Peak VRAM Usage'


def relevant_lines(path: Path):
    """로그에서 우리가 쓰는 줄만 **순서대로** 뽑아 온다."""
    cmd = f"tr '\\r' '\\n' < {shlex.quote(str(path))} | grep -aE {shlex.quote(GREP_PAT)} || true"
    try:
        res = subprocess.run(['bash', '-c', cmd], capture_output=True, text=True,
                             errors='replace', timeout=600)
    except (subprocess.SubprocessError, OSError):
        return []
    return res.stdout.splitlines()


def run_name_from_banner(line: str, path: Path):
    """'========== upernet + ResNetD-50 START ==========' + 파일명 cv1
       -> 'blueberry_upernet_resnetd_50_bcedice_cv1'"""
    m = BANNER_RE.search(line)
    if not m:
        return None
    head, disp = m.group(1), m.group(2)
    backbone = BACKBONE_ALIAS.get(disp)
    fm = FOLD_IN_FILENAME_RE.search(path.name)
    if not backbone or not fm:                  # 알 수 없는 표기·폴드 → 버린다(추측 금지)
        return None
    return f'blueberry_{head}_{backbone}_bcedice_cv{fm.group(1)}'


def parse_log(path: Path):
    """한 로그 파일에서 [(config_stem, {stat: value}), ...] 를 뽑는다."""
    lines = relevant_lines(path)
    marks = []
    for i, ln in enumerate(lines):
        if m := CFG_RE.search(ln):              # 새 형식이 우선
            marks.append((i, m.group(1)))
        elif (name := run_name_from_banner(ln, path)):
            marks.append((i, name))
    # 3차 대체 — 마커가 아예 없는 '런 1개짜리 로그'는 **파일명**이 곧 런 이름이다.
    #   logs/chain_260723_1332/stage1_blueberry_upernet_mit_b2_bcedice_cv1.log
    # 안전한 이유: 이런 파일은 런 하나만 담고 있어 구간을 나눌 필요가 없다.
    if not marks:
        stem = re.sub(r'^(stage\d+_|run_)', '', path.stem)
        if NAME_RE.match(stem):
            marks = [(0, stem)]

    out = []
    for idx, (start, name) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        chunk = '\n'.join(lines[start:end])
        stats = {}
        for key, rex in STAT_RES.items():
            m = rex.search(chunk)
            if m:
                stats[key] = m.group(1)
        if 'total_time' in stats:               # 끝까지 간 런만 채택
            out.append((name, stats))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--logs-dir', default='logs')
    ap.add_argument('--out', default='output/run_cost.csv')
    ap.add_argument('--fold', type=int, default=None, help='이 폴드만 (예: 1)')
    args = ap.parse_args()

    logdir = Path(args.logs_dir)
    files = sorted(logdir.rglob('*.log'), key=lambda p: p.stat().st_mtime)
    print(f'[스캔] 로그 파일 {len(files)}개')

    found = {}                                   # config_stem -> (stats, 출처)
    for f in files:                              # 오래된 것부터 → 최신이 덮어씀
        for name, stats in parse_log(f):
            found[name] = (stats, str(f))

    rows = []
    for name, (stats, src) in sorted(found.items()):
        m = NAME_RE.match(name)
        if m:
            head, backbone = split_head_backbone(m.group(1))
            fold = int(m.group(3))
        else:                                    # 벤치마크 밖 런(fruitseg/minneapple 등)
            head = backbone = ''
            fold = None
        if args.fold is not None and fold != args.fold:
            continue
        rows.append({
            'run': name, 'head': head, 'backbone': backbone, 'fold': fold,
            'total_time': stats.get('total_time', ''),
            'total_sec': hms_to_sec(stats['total_time']) if 'total_time' in stats else '',
            'avg_epoch_sec': stats.get('avg_epoch_sec', ''),
            'avg_ram_gb': stats.get('avg_ram_gb', ''),
            'avg_vram_mb': stats.get('avg_vram_mb', ''),
            'peak_vram_mb': stats.get('peak_vram_mb', ''),
            'log_source': src,
        })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ['run'])
        w.writeheader()
        w.writerows(rows)
    n_bench = sum(1 for r in rows if r['head'] and r['fold'])
    print(f'[저장] {out}  — 총 {len(rows)}런 (벤치마크 형식 {n_bench}런)')
    miss = [r['run'] for r in rows if not r['peak_vram_mb']]
    if miss:
        print(f'[주의] Peak VRAM이 없는 런 {len(miss)}개 (옛 로그 형식): {miss[:3]} ...')


if __name__ == '__main__':
    main()
