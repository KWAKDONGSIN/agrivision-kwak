"""StrawDI_Db1(딸기) 원본을 이 레포의 데이터셋 규칙으로 재배치한다.

왜 필요한가
  `semseg/datasets/blueberry.py` 는 `<ROOT>/{train,val,test}/{images,masks}` 구조만 읽는다.
  StrawDI 원본은 `<raw>/{train,val,test}/{img,label}` 이라 폴더 이름이 다르다.
  → 이름만 맞춰주면 코드 수정 없이 그대로 학습에 쓸 수 있다.

마스크에 대해
  StrawDI 의 `label/*.png` 는 **개체 번호**가 픽셀값으로 들어 있다 (0=배경, 1..N=딸기 개체).
  `BlueberryDataset` 이 `mask[mask>0] = 1` 로 자동 이진화하므로 값 변환은 필요 없다.
  (MinneApple 때와 완전히 같은 상황)

해상도
  원본 1008x756. 학습 시 config 의 IMAGE_SIZE(512x512)로 리사이즈되므로 미리 줄이지 않는다.
  (JPEG/PNG 디코딩 실측 32ms/장 → num_workers 80 이면 병목 아님)

파일명 충돌 주의
  원본은 train/val/test 각각 `1.png` 부터 다시 번호가 시작된다.
  나중에 `tools/make_folds.py` 가 세 split 을 한 통에 모아 다시 7:1:2 로 뽑기 때문에,
  이름이 겹치면 서로를 덮어쓴다. → `<원split>_<번호>.png` 로 접두어를 붙여 유일하게 만든다.

출력은 전부 **심볼릭 링크**라서 디스크 추가 사용량은 0 이다.

사용 예
  $PY tools/prepare_strawdi_semseg.py \
      --raw-root /data/project/2026summer/kds0206/_서버업로드용/strawdi_raw/StrawDI_Db1 \
      --out      /data/project/2026summer/kds0206/dataset_strawdi
"""
import argparse
import json
from pathlib import Path

SPLITS = ('train', 'val', 'test')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw-root', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    raw, out = Path(args.raw_root), Path(args.out)
    if not raw.is_dir():
        raise SystemExit(f'원본 폴더가 없습니다: {raw}')

    manifest = {'raw_root': str(raw), 'out': str(out), 'splits': {}}
    total = 0

    for split in SPLITS:
        img_dir, lbl_dir = raw / split / 'img', raw / split / 'label'
        if not img_dir.is_dir() or not lbl_dir.is_dir():
            raise SystemExit(f'구조가 다릅니다: {img_dir} / {lbl_dir}')

        pairs = []
        for img in sorted(img_dir.iterdir(), key=lambda p: (len(p.stem), p.stem)):
            if img.suffix.lower() not in ('.png', '.jpg', '.jpeg'):
                continue
            hits = sorted(lbl_dir.glob(f'{img.stem}.*'))
            if not hits:
                print(f'  ⚠️ 마스크 없음, 제외: {img}')
                continue
            pairs.append((img, hits[0]))

        dst_img, dst_mask = out / split / 'images', out / split / 'masks'
        if not args.dry_run:
            dst_img.mkdir(parents=True, exist_ok=True)
            dst_mask.mkdir(parents=True, exist_ok=True)

        for img, mask in pairs:
            name = f'{split}_{img.stem}'          # 파일명 충돌 방지
            for src, dst in ((img, dst_img / f'{name}{img.suffix}'),
                             (mask, dst_mask / f'{name}{mask.suffix}')):
                if args.dry_run:
                    continue
                if dst.exists() or dst.is_symlink():
                    dst.unlink()
                dst.symlink_to(src.resolve())

        manifest['splits'][split] = len(pairs)
        total += len(pairs)
        print(f'{split:5s}: {len(pairs)}쌍 → {dst_img}')

    print(f'합계 {total}쌍')
    manifest['total'] = total

    if not args.dry_run:
        (out / 'prepare_manifest.json').write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        # 짝 검증
        for split in SPLITS:
            n_i = len(list((out / split / 'images').iterdir()))
            n_m = len(list((out / split / 'masks').iterdir()))
            assert n_i == n_m == manifest['splits'][split], f'{split} 개수 불일치'
        print('✅ 이미지-마스크 개수 검증 통과')


if __name__ == '__main__':
    main()
