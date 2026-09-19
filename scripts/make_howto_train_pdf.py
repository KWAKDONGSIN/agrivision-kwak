# -*- coding: utf-8 -*-
"""「학습 돌리는 법 — 완전 가이드」 PDF 생성.

곽동신 님이 터미널을 처음 쓴다고 가정하고, 명령어를 그대로 복사해 붙여넣으면
학습 한 번이 끝까지 돌아가도록 단계별로 씁니다.

- 명령어와 출력은 전부 **서버에서 실제로 실행/확인한 것**입니다.
- 교수님 녹취록(`0723교수님미팅.txt`) 원문을 인용해 "왜 이 순서인가"를 설명합니다.
- 개념 그림은 `reports/figures/textbook/`의 기존 그림을 재사용합니다.

짝 문서(복사·붙여넣기용 원본): 문서/260727_학습_돌리는법_완전가이드.md

사용:  $PY tools/make_howto_train_pdf.py
"""
import sys
from pathlib import Path

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
BASE = Path('/data/project/2026summer/kds0206')
sys.path.insert(0, str(REPO / 'tools'))
from pdfdoc import Doc                                      # noqa: E402

TB = REPO / 'reports/figures/textbook'
FIG = REPO / 'reports/figures'
GAL = FIG / 'gallery'
OUT = REPO / 'reports/학습_돌리는법_완전가이드.pdf'

PROF = '안홍렬 교수님 (2026-07-23 미팅 녹취록)'


def build():
    d = Doc(OUT, '학습 돌리는 법 — 완전 가이드',
            '터미널을 처음 쓰는 사람이 복사·붙여넣기만으로 학습 한 번을 끝까지 돌리는 법',
            '실습편', footer='학습 돌리는 법 — 완전 가이드 · 2026-07-27',
            date='2026-07-27')

    d.cover(['이 문서의 회색 상자는 전부 그대로 복사해서 터미널에 붙여넣으면 됩니다.',
             '명령어와 화면 출력은 모두 이 서버에서 실제로 실행해 확인한 것입니다.',
             '',
             '복사·붙여넣기 원본(마크다운):',
             '문서/260727_학습_돌리는법_완전가이드.md'],
            badge='작성 2026-07-27 · 곽동신용')

    d.toc([
        (0, '큰 그림 — 학습 한 번은 이렇게 생겼다', '0단계부터 8단계까지, 각 단계가 몇 분 걸리는지.'),
        (1, '터미널 열고 준비물 설정', '터미널을 새로 열 때마다 필요한 4줄.'),
        (2, '빈 GPU 확인하기', '이걸 안 하면 남의 학습을 망칩니다. 10초.'),
        (3, 'yaml 설정파일 만들기', '학습의 설명서. 딱 3줄만 바꾸면 됩니다.'),
        (4, '2에폭 연습 학습 (스모크 테스트)', '교수님이 콕 집어 지시하신 "한 케이스 먼저".'),
        (5, '진짜 학습 걸어놓기 (nohup)', '터미널을 닫아도 죽지 않게 떼어놓기.'),
        (6, '진행 상황 구경하기', '지금 잘 되고 있나? 로그 읽는 법.'),
        (7, '끝났는지 확인 + test 점수 뽑기', '발표에 쓸 진짜 점수는 여기서 나옵니다.'),
        (8, 'loss 그래프 그리기', '발표자료 ④.'),
        (9, '에러가 났을 때 / 절대 하지 말 것', '자주 나는 에러 6가지와 사고 방지 체크리스트.'),
    ])

    # ================================================================ 0장
    d.chapter(0, '큰 그림 — 학습 한 번은 이렇게 생겼다',
              '먼저 전체 흐름을 봅니다. 각 단계가 뭘 하고 얼마나 걸리는지 알면 '
              '중간에 길을 잃지 않습니다.')

    d.h1('0.1 전체 흐름 한 장')
    d.table(['단계', '무엇을 하나', '걸리는 시간', '중요도'],
            [['0', '터미널 열고 준비물 설정', '30초', '필수'],
             ['1', '빈 GPU 확인 (nvidia-smi)', '10초', '★ 안 하면 사고'],
             ['2', 'yaml 설정파일 만들기', '2분', '★ 3줄만 바꿈'],
             ['3', '2에폭 연습 학습 (스모크)', '약 4분', '★ 교수님 지시'],
             ['4', '진짜 학습 걸어놓기 (nohup)', '거는 데 10초', '필수'],
             ['5', '진행 상황 구경', '언제든', '선택'],
             ['6', '끝 확인 + test 점수', '2분', '★ 발표에 쓸 숫자'],
             ['7', 'loss 그래프', '10초', '발표자료 ④']],
            [.07, .40, .28, .25])

    d.h1('0.2 꼭 알아야 할 개념 하나')
    d.p('우리 학습 프로그램은 **명령줄 옵션이 `--cfg` 딱 하나뿐**입니다. '
        '학습률·에폭 수·어떤 데이터를 쓸지 같은 **모든 설정이 yaml 파일 안에** 들어 있습니다.')
    d.tip('그래서 "학습을 돌린다"는 것은 사실상 **"yaml 파일 하나 만들고 그걸 가리키는 것"**입니다. '
          '코드는 한 글자도 안 고칩니다.')
    d.fig(TB / 'tb_yaml_map.png', 0.30,
          'yaml 파일의 각 부분이 학습의 어디를 담당하는지 보여주는 지도입니다.')

    d.h1('0.3 학습이 실제로 하는 일')
    d.p('컴퓨터는 사진을 보고 "이 점은 과일, 이 점은 배경"이라고 **찍습니다.** 처음엔 엉망입니다. '
        '정답과 비교해 얼마나 틀렸는지를 숫자(**loss**)로 재고, 그 숫자가 줄어드는 방향으로 '
        '자기 내부 값들을 아주 조금씩 고칩니다. 이걸 수십만 번 반복하는 것이 "학습"입니다.')
    d.fig(TB / 'tb_train_loop.png', 0.28,
          '학습 한 걸음(iteration). 이 고리를 691번 돌면 1에폭, 200에폭이면 약 14만 번 돕니다.')

    d.h1('0.4 왜 이 순서를 지켜야 하나 — 교수님 말씀')
    d.quote('"한 케이스 정도 먼저 따로 따로 떼서 한번 돌려보세요. '
            '그러니까 다 돌리지 말고 한 케이스 정도 따로따로 떼서 돌려보고…"', PROF)
    d.quote('"왜냐하면은 돌렸는데 중간에 \'아 이거 실수했네\' 이러면은 또 다 다시 돌려야 되잖아요. '
            '그러니까 돌리기 전에 일단… 몇 번 해보고 결과까지 몇 개 그냥 테스트를 좀 내보고 '
            '\'잘 나오네\' 이렇게, 그다음에 이제 쭉 전체 돌려달라고 시켜야지."', PROF)
    d.p('그래서 이 문서는 **3장에서 4분짜리 연습 학습을 먼저** 하고, 그게 성공한 다음에야 '
        '4장에서 3~4시간짜리 진짜 학습을 겁니다. 순서를 건너뛰지 마세요.')

    # ================================================================ 1장
    d.chapter(1, '터미널 열고 준비물 설정',
              'VS Code로 서버에 접속한 상태에서 시작합니다. 터미널을 새로 열 때마다 '
              '이 4줄이 필요합니다.')

    d.h1('1.1 터미널 열기')
    d.steps(['VS Code 위쪽 메뉴에서 Terminal → New Terminal 을 누릅니다.',
             '(단축키는 Ctrl 과 백틱( ` ) 을 같이 누르기)',
             '아래쪽에 까만 창이 열리고 커서가 깜빡이면 준비 완료입니다.'])

    d.h1('1.2 준비물 4줄 — 통째로 복사해서 붙여넣기')
    d.code('export PY=/home/kds0206/.conda/envs/kwak/bin/python\n'
           'export REPO=/data/project/2026summer/kds0206/semantic-segmentation\n'
           'export PYTHONPATH=$REPO:$PYTHONPATH\n'
           'cd $REPO\n'
           'pwd', '터미널에 붙여넣고 Enter')

    d.h2('한 줄씩 무슨 뜻인가')
    d.table(['줄', '뜻'],
            [['export PY=...',
              '앞으로 $PY 라고 쓰면 저 긴 파이썬 경로를 뜻하게 하는 별명. 서버에 파이썬이 '
              '여러 개라 꼭 kwak 환경 것을 써야 torch가 있습니다.'],
             ['export REPO=...', '코드가 있는 폴더 별명'],
             ['export PYTHONPATH=...',
              '파이썬이 semseg 폴더(우리가 만든 모델 코드)를 찾게 알려주기. 이거 없으면 '
              "ModuleNotFoundError: No module named 'semseg' 에러가 납니다."],
             ['cd $REPO', '그 폴더로 이동'],
             ['pwd', '지금 내가 어디 있는지 출력 (확인용)']],
            [.26, .74])

    d.h2('이렇게 나오면 성공')
    d.code('/data/project/2026summer/kds0206/semantic-segmentation', '화면에 나오는 결과')

    d.warn('터미널을 새로 열 때마다 이 4줄을 **다시** 해야 합니다. 컴퓨터를 껐다 켜도, '
           'VS Code를 새로 켜도 마찬가지입니다. export 는 그 터미널 창에서만 유효한 '
           '임시 별명이기 때문입니다.')

    d.h1('1.3 폴더 지도 — 지금 내가 어디 있는가')
    d.fig(TB / 'tb_folder_map.png', 0.31,
          '방금 cd 로 들어간 곳이 semantic-segmentation 폴더입니다. '
          'configs(설명서), tools(프로그램), output(결과)이 그 안에 있습니다.')

    # ================================================================ 2장
    d.chapter(2, '빈 GPU 확인하기',
              '우리 서버에는 GPU가 8장(0~7번) 있고 랩 사람들이 나눠 씁니다. '
              '남이 쓰는 GPU에 내 학습을 또 올리면 둘 다 느려지거나 메모리 부족으로 죽습니다.')

    d.h1('2.1 명령어')
    d.code('nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv',
           '빈 GPU 확인 — 학습 전 반드시')

    d.h2('실제 출력 (2026-07-27)')
    d.code('index, name, memory.used [MiB], memory.total [MiB], utilization.gpu [%]\n'
           '0, Tesla V100-SXM2-32GB, 5 MiB, 32768 MiB, 0 %\n'
           '1, Tesla V100-SXM2-32GB, 5 MiB, 32768 MiB, 0 %\n'
           '2, Tesla V100-SXM2-32GB, 5 MiB, 32768 MiB, 0 %\n'
           '...\n'
           '7, Tesla V100-SXM2-32GB, 5 MiB, 32768 MiB, 0 %')

    d.h1('2.2 읽는 법')
    d.bullets(['memory.used 가 **5 MiB 정도면 비어 있는 것**입니다. 써도 됩니다.',
               'memory.used 가 **수천~수만 MiB면 남이 쓰는 중**입니다. 그 번호는 피하세요.',
               '위 예시는 8장 전부 비어 있으므로 아무거나 골라도 됩니다. '
               '이 문서에서는 앞으로 **2번**을 예로 씁니다.'])
    d.p('누가 쓰는지까지 보고 싶으면 옵션 없이 `nvidia-smi` 만 치면 됩니다. '
        '아래쪽 Processes 표에 사용자 이름과 GPU 번호가 나옵니다.')

    d.warn('**남의 프로세스를 kill / pkill 하지 마세요.** 남의 몇 시간짜리 학습이 통째로 '
           '날아갑니다. 빈 GPU가 없으면 기다리거나 물어보세요.', head='절대 금지')

    # ================================================================ 3장
    d.chapter(3, 'yaml 설정파일 만들기',
              'yaml은 학습의 설명서입니다. "어떤 모델로, 어떤 데이터를, 몇 번 반복해서, '
              '어떻게 학습해라"가 전부 글자로 적혀 있습니다.')

    d.h1('3.1 교수님이 강조하신 부분')
    d.quote('"나중에는 그러니까 야물 파일에서 그 부분만 바꿔서 그냥 돌리면 되거든요. '
            '그러면 이제 그게 다 돌아가는지 이런 것들도 좀 확인해 봐야 되는 거고"', PROF)
    d.quote('"여기 아까 야물 파일 있잖아요. 이 옵션은 뭐 하는 거냐 이렇게 물어보면서, '
            '아까 전에 그 모델에 관련된 거냐 아니면은 뭐 데이터셋에 관련된 거냐, '
            '그리고 그 데이터셋 중에서도 프리프로세싱이라고 있어요."', PROF)

    d.h1('3.2 0에서 쓰지 말고 기존 파일을 복사한다')
    d.code('cp configs/fruitseg_upernet_resnet_50_bcedice_200ep.yaml configs/<내이름>_test.yaml\n'
           'ls -la configs/<내이름>_test.yaml',
           '<내이름> 자리에 예: kwak → configs/kwak_test.yaml')
    d.note('꺾쇠 `< >` 로 감싼 부분은 **내가 값을 바꿔 넣어야 하는 자리**입니다. '
           '꺾쇠는 지우고 씁니다.')

    d.h1('3.3 바꿔야 하는 줄은 딱 3개')
    d.h2('① SAVE_DIR — 결과를 어디에 저장할지')
    d.code("SAVE_DIR : 'output/fruitseg_runs/<내가지을이름>'")
    d.bullets(['학습된 모델(.pth)과 기록이 여기에 쌓입니다.',
               '**이걸 안 바꾸면 예전 학습 결과를 덮어씁니다.** 몇 시간짜리가 날아갑니다.',
               '반드시 output/ 바로 아래가 아니라 **한 단계 더 들어간 폴더**'
               '(output/fruitseg_runs/... 처럼)에 두세요. output/ 바로 밑에 두면 '
               'aggregate_results.py 가 이걸 **32조합 벤치마크 성적표에 가짜 결과로 섞어 넣습니다.**'])

    d.h2('② DATASET.ROOT — 어떤 데이터로 학습할지')
    d.code("DATASET:\n"
           "  ROOT : '/data/project/2026summer/kds0206/dataset_fruitseg30'")
    d.table(['지금 서버에 있는 데이터 폴더', '내용'],
            [['dataset_fruitseg30', 'FruitSeg30 (내 담당). train 1383 / val 196 / test 390'],
             ['dataset_6fold/cv1', '블루베리 1번 폴드. train 796 / val 199 / test 200'],
             ['dataset_minneapple', 'MinneApple 사과. train 536 / val 134 / test 331']],
            [.34, .66])
    d.p('세 폴더 모두 안이 `train/images`, `train/masks`, `val/...`, `test/...` 구조입니다. '
        '**이 구조만 맞으면 어떤 데이터든 코드 수정 없이 돌아갑니다.**')
    d.fig(TB / 'tb_split.png', 0.24,
          'train / val / test 를 나누는 이유. 시험 문제를 미리 보여주면 실력이 아니라 '
          '암기가 되기 때문에, test 는 학습 중 절대 보여주지 않습니다.')

    d.h2('③ TEST.MODEL_PATH — 나중에 평가할 때 쓸 모델 파일 위치')
    d.code("TEST:\n"
           "  MODEL_PATH : '/data/project/.../output/fruitseg_runs/<내가지은이름>/\n"
           "                UPerNet_ResNet-50_BlueberryDataset_best.pth'")
    d.bullets(['①에서 정한 SAVE_DIR 과 **같은 폴더**를 가리켜야 합니다.',
               '파일 이름은 코드가 자동으로 만듭니다. 규칙은 '
               '`<헤더>_<백본>_<데이터셋클래스>_best.pth` 입니다.',
               '데이터가 FruitSeg30인데도 이름에 BlueberryDataset 이 들어가는 이유: '
               '데이터를 읽는 코드 클래스 이름이 BlueberryDataset 이고, 이 클래스가 범용이라 '
               '다른 과일에도 그대로 쓰기 때문입니다.'])

    d.h1('3.4 나머지 줄들은 무엇인가')
    d.table(['yaml 줄', '뜻', '지금 값'],
            [['MODEL.NAME', '헤더(디코더). 특징을 모아 픽셀 판정을 내리는 부분', 'UPerNet'],
             ['MODEL.BACKBONE', '백본(인코더). 사진에서 특징을 뽑는 부분', 'ResNet-50'],
             ['MODEL.PRETRAINED', '미리 학습된 가중치. 맨땅에서 시작하지 않게 함', 'resnet50_a1.pth'],
             ['TRAIN.IMAGE_SIZE', '학습할 때 사진 크기. 크면 정확하지만 느림', '[512, 512]'],
             ['TRAIN.BATCH_SIZE', '한 번에 GPU에 올리는 사진 장수', '2'],
             ['TRAIN.EPOCHS', '데이터 전체를 몇 바퀴 돌 것인가', '200'],
             ['TRAIN.ACCUM_STEPS', '4번 모아 한 번 업데이트 → 실질 배치 8 효과', '4'],
             ['TRAIN.AUGMENTATIONS', '데이터 증강(뒤집기·회전 등) 목록', '4종 켜짐'],
             ['LOSS.NAME', '채점 방식(손실 함수). 틀린 정도를 숫자로', 'BCEDice'],
             ['OPTIMIZER.LR', '학습률. 한 번에 얼마나 크게 고칠지', '0.0001'],
             ['EARLY_STOP.ENABLE', '성능이 안 오르면 일찍 멈출지', 'False'],
             ['EARLY_STOP.CHECK_INTERVAL', '몇 에폭마다 val 점수를 잴지', '5']],
            [.30, .52, .18], size=8.6)

    d.warn('7/27 랩미팅 기준 **팀 규칙**: 조합은 UPerNet + ResNet-50 **고정**, '
           '하이퍼파라미터(512×512 / batch 2 / ACCUM 4 / BCEDice / AdamW 1e-4) **변경 금지**입니다. '
           '데이터셋만 바꿔 비교하는 실험이라 다른 걸 건드리면 공정 비교가 깨집니다.',
           head='팀 규칙')

    d.fig(TB / 'tb_batch_accum.png', 0.25,
          'BATCH_SIZE 2 와 ACCUM_STEPS 4 의 관계. 2장씩 4번 모아 8장짜리 한 걸음처럼 '
          '움직입니다. GPU 메모리를 아끼는 기법입니다.')
    d.fig(TB / 'tb_augment.png', 0.25,
          'TRAIN.AUGMENTATIONS 가 하는 일. 같은 사진을 뒤집고 돌려서 데이터를 늘리는 효과를 냅니다. '
          '0723 교수님 지시로 이 목록이 코드가 아닌 yaml 로 나왔습니다.')

    d.note('yaml 한 줄 한 줄의 자세한 설명은 **문서/교재/ 4권 「yaml 완전해부」(31쪽)**에 있습니다.')

    # ================================================================ 4장
    d.chapter(4, '2에폭 연습 학습 (스모크 테스트)',
              '3~4시간짜리를 걸어놓고 자러 갔는데 오타 하나로 5분 만에 죽어 있으면 하루를 '
              '날립니다. 그래서 에폭 수만 2로 줄인 config 로 먼저 4분짜리 시험 주행을 합니다.')

    d.h1('4.1 명령어')
    d.p('이미 만들어둔 스모크용 파일이 있습니다: `configs/fruitseg_smoke_test.yaml` '
        '(200에폭짜리와 EPOCHS·SAVE_DIR·WARMUP 만 다릅니다).')
    d.code('CUDA_VISIBLE_DEVICES=2 $PY tools/train.py --cfg configs/fruitseg_smoke_test.yaml',
           '약 4분. 끝날 때까지 터미널을 그대로 두고 봅니다.')

    d.h2('명령어 해부')
    d.table(['조각', '뜻'],
            [['CUDA_VISIBLE_DEVICES=2', '"2번 GPU만 써라". 2장에서 확인한 빈 번호를 넣습니다.'],
             ['$PY', '1장에서 만든 파이썬 별명'],
             ['tools/train.py', '학습 프로그램'],
             ['--cfg configs/....yaml', '설명서 파일 지정. **명령줄 옵션은 이거 하나뿐입니다.**']],
            [.32, .68])

    d.h1('4.2 성공하면 이렇게 나옵니다 (실제 로그)')
    d.code('==============================\n'
           ' >>> SYSTEM CHECK <<<\n'
           ' 1. CUDA Available: True\n'
           ' 2. Target GPU: Tesla V100-SXM2-32GB (Default)\n'
           ' 3. Total System RAM: 251.5 GB\n'
           '==============================\n'
           '\n'
           '[AUGMENT] HORIZONTAL_FLIP(p=0.5) -> ROTATION(degrees=60, p=0.3) -> RANDOM_CROP -> NORMALIZE\n'
           '[BlueberryDataset] Found 1383 train images\n'
           'Detected backbone output channels: [256, 512, 1024, 2048]\n'
           '[BaseModel] Loaded 318/318 backbone keys from .../weights/resnet50_a1.pth\n'
           '[BaseModel] missing=0 unexpected=0\n'
           '[Train] Gradient accumulation enabled: ACCUM_STEPS=4 (effective batch = 8)\n'
           '[BlueberryDataset] Found 196 val images\n'
           'Epoch: [1/2] Iter: [1/691] LR: 0.00001001 Loss: 3.33876705 ...')

    d.h2('한 줄씩 무슨 뜻인지')
    d.table(['나오는 줄', '확인할 것'],
            [['CUDA Available: True',
              'GPU를 찾았다. False 면 CPU로 가서 100배 느려집니다.'],
             ['[AUGMENT] ...',
              '데이터 증강 목록. **논문 Methods 에 그대로 쓸 문장**입니다.'],
             ['Found 1383 train images',
              '학습 사진 장수. **0이면 DATASET.ROOT 경로가 틀린 것**입니다.'],
             ['Loaded 318/318 backbone keys',
              '사전학습 가중치를 전부 불러왔다. missing 이 크면 가중치 파일이 안 맞는 것.'],
             ['effective batch = 8',
              '배치 2를 4번 모아 8장처럼 학습. GPU 메모리를 아끼는 기법.'],
             ['Epoch: [1/2] Iter: [1/691]',
              '1바퀴 중 691걸음 중 1걸음째. Loss 숫자가 **점점 줄면 정상**입니다.']],
            [.30, .70])

    d.h1('4.3 합격 기준 3가지')
    d.steps(['빨간 에러 없이 Epoch: [2/2] 까지 도달했다.',
             'Loss 숫자가 처음보다 줄었다.',
             '.pth 파일이 실제로 생겼다 — 아래 명령으로 확인.'])
    d.code('ls -la output/fruitseg_runs/_smoke_test/')
    d.tip('이 3개가 다 되면 다음 장(진짜 학습)으로 넘어갑니다. 하나라도 안 되면 '
          '9장의 에러 대처를 보세요.')
    d.note('실측 참고: 이 스모크 테스트는 **3분 31초**, GPU 메모리 **464MB**만 썼고 '
           '2에폭만에 val 과일 IoU 0.805 가 나왔습니다 (2026-07-25 실행).')

    # ================================================================ 5장
    d.chapter(5, '진짜 학습 걸어놓기 (nohup)',
              '그냥 돌리면 터미널 창을 닫거나 인터넷이 끊기는 순간 학습이 죽습니다. '
              '3시간짜리가 날아갑니다.')

    d.h1('5.1 nohup 이 무엇인가')
    d.p('`nohup` 은 **no hangup**(끊겨도 계속)의 줄임말입니다. 이걸 붙여 실행하면 '
        '학습이 내 터미널에서 **떨어져 나가** 서버가 알아서 계속 돌립니다. '
        'VS Code를 꺼도, 집에 가도, 인터넷이 끊겨도 계속 돕니다.')

    d.h1('5.2 명령어')
    d.code('nohup env CUDA_VISIBLE_DEVICES=2 $PY tools/train.py \\\n'
           '  --cfg configs/fruitseg_upernet_resnet_50_bcedice_200ep.yaml \\\n'
           '  > logs/내학습_$(date +%m%d_%H%M).log 2>&1 &',
           '줄 끝의 \\ 는 "다음 줄에 계속됨" 이라는 뜻. 통째로 붙여넣으면 그대로 동작합니다.')

    d.h2('조각 해부')
    d.table(['조각', '뜻'],
            [['nohup', '터미널이 닫혀도 계속 돌게 함'],
             ['env CUDA_VISIBLE_DEVICES=2',
              'GPU 지정. nohup 은 A=B 형태를 직접 못 읽어서 **env 를 껴 넣어야 합니다.**'],
             ['\\  (줄 끝)', '"다음 줄에 계속됨"'],
             ['> logs/....log', '화면에 나올 내용을 전부 파일로 저장'],
             ['2>&1', '에러 메시지도 같은 파일에 저장. **빠뜨리면 왜 죽었는지 못 봅니다.**'],
             ['&  (맨 끝)', '백그라운드로 보내고 터미널을 곧장 돌려받기'],
             ['$(date +%m%d_%H%M)',
              '지금 시각을 파일명에 자동으로 박기(예: 내학습_0727_1530.log). '
              '이전 로그를 덮어쓰지 않게 해줍니다.']],
            [.30, .70])

    d.h2('바로 나오는 결과')
    d.code('[1] 1700401')
    d.p('`[1]` 은 작업 번호, `1700401` 은 **프로세스 번호(PID)** 입니다. '
        '이 숫자가 나왔다면 성공적으로 걸린 것입니다.')

    d.h1('5.3 학습 → 평가 → 그래프를 한 번에 이어 돌리기')
    d.p('이미 만들어둔 자동 체인 스크립트가 있습니다. 이걸 쓰면 7·8장을 따로 안 해도 됩니다.')
    d.code('nohup bash scripts/run_fruitseg30_pipeline.sh 2 > logs/fruitseg30_pipeline.log 2>&1 &',
           '끝의 2 가 GPU 번호입니다.')

    # ================================================================ 6장
    d.chapter(6, '진행 상황 구경하기',
              '걸어놓은 학습이 잘 되고 있는지 확인하는 방법 4가지.')

    d.h1('6.1 지금 돌고 있나?')
    d.code('ps -ef | grep train.py | grep -v grep')
    d.bullets(['줄이 나오면 **돌고 있는 것**. 맨 앞이 사용자 이름, 두 번째가 PID 입니다.',
               '아무것도 안 나오면 **끝났거나 죽은 것**입니다.'])

    d.h1('6.2 로그 실시간으로 보기')
    d.code('tail -f logs/<내로그파일>.log')
    d.bullets(['화면이 계속 흘러갑니다. 구경을 그만두려면 **Ctrl + C**.',
               '여기서 Ctrl+C 를 눌러도 **학습은 안 죽습니다.** 구경만 그만두는 겁니다. '
               'nohup 으로 떼어놨기 때문입니다.'])
    d.tip('이게 5장에서 nohup 을 쓴 이유입니다. 학습과 내 터미널이 분리돼 있어서 '
          '내가 뭘 해도 학습은 계속 돕니다.')

    d.h1('6.3 중요한 줄만 골라 보기 (추천)')
    d.p('로그에는 진행률 막대가 수만 줄 쌓여서 눈이 아픕니다. '
        '**5에폭마다 찍히는 val 점수만** 뽑아 보는 게 훨씬 낫습니다.')
    d.code('tr \'\\r\' \'\\n\' < logs/<내로그파일>.log | grep -E "Val Loss|New Best|No Improvement" | tail -20')

    d.h2('실제 출력 (FruitSeg30 학습 로그)')
    d.code(' Val Loss: 2.729252 | mIoU: 0.9125 | mDice: 0.9541 | mPrec: 0.9507 | mRecall: 0.9580\n'
           ' >>> New Best Model Saved! (val_loss: 2.729252)\n'
           ' Val Loss: 0.685079 | mIoU: 0.9410 | mDice: 0.9695 | mPrec: 0.9712 | mRecall: 0.9680\n'
           ' >>> New Best Model Saved! (val_loss: 0.685079)\n'
           ' Val Loss: 0.696316 | mIoU: 0.9382 | ...\n'
           ' No Improvement. Epochs since best: 5/10 (Best: 0.685079)')

    d.h2('읽는 법')
    d.table(['나오는 말', '뜻'],
            [['Val Loss',
              '학습에 안 쓴 사진(val)으로 매긴 틀린 정도. **작을수록 좋음.** 줄면 잘 되고 있는 것'],
             ['New Best Model Saved!',
              '지금까지 중 최고 성적 → _best.pth 파일을 갱신했다'],
             ['No Improvement. 5/10',
              '5에폭째 최고 기록을 못 깼다. early stop 이 켜져 있으면 10에서 멈춥니다. '
              '지금 config 는 꺼져 있어서 200에폭을 끝까지 돕니다.'],
             ['mIoU', '배경까지 포함한 평균 점수']],
            [.28, .72])

    d.warn('**mIoU 에 속지 마세요.** 블루베리는 화면의 2.4%뿐이라 배경만 다 맞혀도 mIoU 가 '
           '0.9를 넘습니다. 그래서 우리는 **과일만 따로 본 fg_IoU** 를 씁니다. '
           'FruitSeg30 은 과일이 화면의 35.8%라 mIoU 도 그럭저럭 쓸 만합니다.')
    d.fig(TB / 'tb_fg_compare.png', 0.24,
          '전경 비율 비교. 블루베리는 화면의 아주 일부라 배경 점수가 전체를 가려버립니다.')

    d.h1('6.4 GPU 를 실제로 쓰고 있나')
    d.code('nvidia-smi')
    d.p('내 GPU 번호의 memory.used 가 수백~수천 MiB 면 정상 작동 중입니다.')

    d.h1('6.5 얼마나 걸리나 (실측)')
    d.table(['데이터셋', '에폭당', '전체'],
            [['FruitSeg30 (1383장)', '약 58.5초', '200에폭 = **3시간 42분**'],
             ['블루베리 cv1 (796장)', '약 1분 20초', '100에폭 = 약 2시간']],
            [.32, .24, .44])

    # ================================================================ 7장
    d.chapter(7, '끝났는지 확인 + test 점수 뽑기',
              '지금까지 본 점수는 전부 val(연습용 채점)입니다. 한 번도 안 보여준 test 사진으로 '
              '매기는 것이 논문·발표에 쓰는 진짜 점수입니다.')

    d.h1('7.1 정상 종료 확인')
    d.code('ls -la output/fruitseg_runs/<내가지은이름>/')
    d.h2('이렇게 나오면 성공')
    d.code('UPerNet_ResNet-50_BlueberryDataset.pth        <- 마지막 에폭 모델\n'
           'UPerNet_ResNet-50_BlueberryDataset_best.pth   <- ★ val_loss 가 가장 낮았던 순간\n'
           'logs/                                          <- TensorBoard 기록')
    d.tip('앞으로 쓸 건 **_best.pth** 쪽입니다. _best 가 안 붙은 건 그냥 마지막 에폭이라 '
          '과적합돼 있을 수 있습니다.')

    d.h2('에러가 났는지 확인')
    d.code('grep -i "error\\|Traceback\\|CUDA out of memory" logs/<내로그파일>.log | head')
    d.p('아무것도 안 나오면 깨끗한 것입니다.')

    d.h1('7.2 test 세트로 최종 점수 매기기')
    d.code('CUDA_VISIBLE_DEVICES=2 $PY tools/val.py \\\n'
           '  --cfg configs/fruitseg_upernet_resnet_50_bcedice_200ep.yaml \\\n'
           '  --split test \\\n'
           '  --model-path output/fruitseg_runs/upernet_resnet_50_bcedice_200ep/\\\n'
           'UPerNet_ResNet-50_BlueberryDataset_best.pth')
    d.table(['옵션', '뜻'],
            [['--cfg', '학습에 썼던 것과 **같은** yaml'],
             ['--split test', 'train / val / test 중 test 로 채점'],
             ['--model-path', '채점할 모델 파일. **_best.pth 를 지정**']],
            [.24, .76])

    d.h2('실제 출력 (FruitSeg30 최종 결과)')
    d.code('[BlueberryDataset] Found 390 test images\n'
           'Evaluating .../UPerNet_ResNet-50_BlueberryDataset_best.pth...\n'
           '[Info] Running on GPU: Tesla V100-SXM2-32GB\n'
           '\n'
           'Class            IoU      Dice    Precision    Recall\n'
           '----------  --------  --------  -----------  --------\n'
           'background  0.978759  0.989266     0.986819  0.991724\n'
           'blueberry   0.962151  0.980711     0.985099  0.976361')

    d.h1('7.3 이 표를 읽는 법 — 이게 곧 발표 슬라이드 ③')
    d.table(['항목', '뜻', '이 결과'],
            [['blueberry 줄', '과일(전경) 성적. **여기만 보면 됩니다**', '—'],
             ['IoU', '정답과 예측이 **겹친 넓이 ÷ 합친 넓이**. 1이 만점', '**0.9622**'],
             ['Dice', 'IoU 와 비슷하나 겹친 부분을 두 번 세는 방식', '0.9807'],
             ['Precision', '과일이라 찍은 것 중 실제 과일 비율 (헛짚지 않았나)', '0.9851'],
             ['Recall', '실제 과일 중 찾아낸 비율 (놓치지 않았나)', '0.9764'],
             ['background 줄', '배경 성적. 항상 높아서 **논문에 안 씀**', '0.9788']],
            [.20, .58, .22])
    d.note('여기서 `blueberry` 라는 이름이 나오는 건 데이터를 읽는 코드 클래스 이름이 '
           '그래서입니다. 실제로는 **과일 30종 전체**를 뜻합니다.')

    d.fig(TB / 'tb_iou.png', 0.26,
          'IoU 를 그림으로. 정답 영역과 예측 영역이 겹친 넓이를 합친 넓이로 나눈 값입니다.')
    d.fig(TB / 'tb_precision_recall.png', 0.24,
          'Precision 은 "헛짚지 않았나", Recall 은 "놓치지 않았나". 둘은 보통 서로 반대로 움직입니다.')

    # ================================================================ 8장
    d.chapter(8, 'loss 그래프 그리기',
              '학습이 어떻게 흘러갔는지 한 장으로 보여주는 그림. 발표자료 ④입니다.')

    d.h1('8.1 명령어')
    d.code('$PY tools/plot_loss_curves.py \\\n'
           '  --logdir output/fruitseg_runs/upernet_resnet_50_bcedice_200ep/logs \\\n'
           '  --labels "FruitSeg30 UPerNet+ResNet-50" \\\n'
           '  --out reports/figures/fig_fruitseg30_loss.png')
    d.table(['옵션', '뜻'],
            [['--logdir', '학습이 남긴 TensorBoard 기록 폴더 (SAVE_DIR/logs)'],
             ['--labels', '그래프 범례에 쓸 이름'],
             ['--out', '저장할 그림 파일 경로']],
            [.20, .80])
    d.h2('나오는 결과')
    d.code('[plot] saved reports/figures/fig_fruitseg30_loss.png')
    d.p('VS Code 왼쪽 탐색기에서 그 파일을 클릭하면 그림이 바로 보입니다.')

    d.h1('8.2 실제로 나온 그래프')
    d.fig(FIG / 'fig_fruitseg30_loss.png', 0.34,
          'FruitSeg30 200에폭 학습 곡선. 실제로 뽑힌 발표자료 ④입니다.')

    d.h1('8.3 그래프 읽는 법')
    d.bullets(['train loss 가 **내려가면** → 배우고 있다',
               'val loss 도 같이 **내려가면** → 진짜로 잘 배우고 있다',
               'train 은 내려가는데 **val 이 올라가면** → **과적합**. 외워버린 것'])
    d.p('우리 FruitSeg30 은 **80에폭에서 val loss 가 최저(0.0682)** 였고 이후 소폭 오르내렸습니다. '
        '그래서 `_best.pth` 는 80에폭 시점의 모델입니다.')
    d.fig(TB / 'tb_overfit.png', 0.26,
          '과적합의 모습. 두 선이 벌어지기 시작하는 지점이 "그만 배워도 되는" 지점입니다.')

    # ================================================================ 9장
    d.chapter(9, '에러가 났을 때 / 절대 하지 말 것',
              '자주 나는 에러 6가지와, 사고를 막는 체크리스트.')

    d.h1('9.1 자주 나는 에러 6가지')

    d.h2("① ModuleNotFoundError: No module named 'semseg'")
    d.p('**원인**: 1장의 PYTHONPATH 설정을 안 했거나 폴더가 다름')
    d.code('export PYTHONPATH=/data/project/2026summer/kds0206/semantic-segmentation:$PYTHONPATH\n'
           'cd /data/project/2026summer/kds0206/semantic-segmentation')

    d.h2('② Found 0 train images')
    d.p('**원인**: DATASET.ROOT 경로가 틀렸거나 그 안에 train/images 구조가 없음')
    d.code('ls /data/project/2026summer/kds0206/dataset_fruitseg30/train/images | head -3\n'
           'ls /data/project/2026summer/kds0206/dataset_fruitseg30/train/masks  | head -3')
    d.p('이미지와 마스크는 **확장자를 빼고 이름이 같아야** 짝으로 인식됩니다 '
        '(apple__1.jpg ↔ apple__1.png). 하나라도 이름이 다르면 그 장은 버려집니다.')

    d.h2('③ CUDA out of memory')
    d.p('**원인**: GPU 메모리 부족. 대개 **남이 이미 쓰는 GPU를 골랐을 때** 납니다. '
        'nvidia-smi 로 진짜 빈 번호를 다시 고르세요. 그래도 나면 yaml 에서 '
        'TRAIN.BATCH_SIZE 를 2 → 1 로 줄입니다(단, 팀 비교 실험에서는 바꾸면 안 됩니다).')

    d.h2('④ FileNotFoundError: .../weights/resnet50_a1.pth')
    d.p('**원인**: MODEL.PRETRAINED 경로가 틀림. 있는 가중치 목록을 확인하세요.')
    d.code('ls /data/project/2026summer/kds0206/weights/')

    d.h2('⑤ 아무 반응 없이 프롬프트만 돌아옴 (nohup 실행 후)')
    d.p('**정상입니다.** 백그라운드로 갔기 때문입니다. 로그로 확인하세요.')
    d.code('tail -20 logs/<내로그파일>.log')

    d.h2('⑥ CUDA Available: False')
    d.p('**원인**: 파이썬을 잘못 골랐음(kwak 환경이 아닌 시스템 파이썬)')
    d.code('echo $PY\n'
           '$PY -c "import torch; print(torch.__version__, torch.cuda.is_available())"')
    d.p('`2.9.1+cu128 True` 가 나와야 정상입니다.')

    d.pagebreak()
    d.h1('9.2 절대 하지 말 것')
    d.table(['하지 말 것', '왜'],
            [['SAVE_DIR 을 안 바꾸고 학습', '기존 체크포인트를 **덮어씀**. 몇 시간~며칠치가 날아감'],
             ['SAVE_DIR 을 output/ 바로 아래에 두기',
              'aggregate_results.py 가 32조합 벤치마크 성적표에 **가짜 결과로 섞음**'],
             ['남의 GPU 프로세스를 kill / pkill',
              '남의 몇 시간짜리 학습이 통째로 날아감. 빈 GPU가 없으면 **기다립니다**'],
             ['nvidia-smi 확인 없이 학습 시작', '남과 충돌해 둘 다 느려지거나 죽음'],
             ['nohup 없이 긴 학습 실행', '터미널 닫는 순간 죽음'],
             ['스모크 테스트 없이 200에폭 걸기',
              '교수님이 콕 집어 지적하신 부분. 오타 하나로 하루 날림'],
             ['output/ 의 .pth 파일 삭제', '재학습에 몇 시간'],
             ['config 파일 이름 규칙 바꾸기', '집계 스크립트가 정규식으로 이름을 읽음']],
            [.36, .64])

    d.h1('9.3 학습 걸기 전 30초 체크리스트')
    d.steps(['nvidia-smi 로 빈 GPU 번호를 확인했다.',
             'yaml 의 SAVE_DIR 을 새 이름으로 바꿨다. (기존 폴더와 겹치지 않는다)',
             'SAVE_DIR 이 output/ 바로 아래가 아니라 한 단계 아래 폴더다.',
             'DATASET.ROOT 폴더가 실제로 존재한다. (ls 로 확인)',
             'TEST.MODEL_PATH 가 SAVE_DIR 과 같은 폴더를 가리킨다.',
             '2에폭 스모크 테스트가 에러 없이 끝났다.',
             'nohup 과 2>&1 을 붙였다.'])

    # ================================================================ 부록
    d.chapter(10, '부록 — 용어 정리와 지금까지의 결과',
              '자주 나오는 말 14개와, 서버에 이미 쌓여 있는 학습 결과들.')

    d.h1('10.1 용어 30초 정리')
    for w, e, m in [
        ('에폭', 'epoch', '데이터 전체를 한 바퀴 다 본 것. 200에폭 = 1383장을 200번 반복'),
        ('배치', 'batch', '한 번에 GPU에 올리는 사진 묶음. 우리는 2장'),
        ('이터레이션', 'iteration', '배치 한 묶음을 처리한 것. 1383 ÷ 2 = 691 iter 가 1에폭'),
        ('손실', 'loss', '얼마나 틀렸는지를 나타내는 숫자. 작을수록 좋음'),
        ('체크포인트', 'checkpoint (.pth)', '학습된 모델 파일. 신경망의 가중치 숫자 뭉치'),
        ('베스트 모델', '_best.pth', 'val loss 가 가장 낮았던 순간에 저장한 모델. 이걸 씁니다'),
        ('백본', 'backbone', '사진에서 특징을 뽑는 앞부분. 우리는 ResNet-50'),
        ('헤더', 'head', '뽑은 특징으로 픽셀 판정을 내리는 뒷부분. 우리는 UPerNet'),
        ('사전학습', 'pretrained', '남이 큰 데이터로 미리 학습해둔 가중치에서 출발하는 것'),
        ('증강', 'augmentation', '뒤집기·회전으로 데이터를 뻥튀기하는 것'),
        ('전경 IoU', 'fg_IoU', '전경(과일)만 본 IoU. 배경이 압도적일 때 필수'),
        ('노허프', 'nohup', '터미널이 꺼져도 계속 돌게 하는 명령'),
        ('피아이디', 'PID', '프로세스 번호. nohup 실행 시 나오는 그 숫자'),
        ('과적합', 'overfitting', '학습 데이터를 외워버려서 새 사진에는 못 하는 상태'),
    ]:
        d.term(w, e, m)

    d.pagebreak()
    d.h1('10.2 지금 서버에 있는 학습 결과들')
    d.table(['폴더', '내용', '결과'],
            [['output/<헤더>_<백본>_bcedice_cv<N>/', '블루베리 32조합 × 6폴드 = 191런',
              '최고 fg_IoU 0.8900'],
             ['output/fruitseg_runs/upernet_resnet_50_bcedice_200ep/',
              '**FruitSeg30 (내 담당)**', 'test IoU **0.9622**'],
             ['output/minneapple_runs/', 'MinneApple 사과 1런', 'test fg_IoU 0.687'],
             ['output/verify_runs/', 'augmentation yaml화 검증런', 'test fg_IoU 0.863'],
             ['output/fruitseg_runs/_smoke_test/', '2에폭 연습', 'val fg_IoU 0.805']],
            [.44, .34, .22], size=8.4)
    d.tip('같은 계열 모델인데 데이터셋에 따라 0.687 ~ 0.962 로 크게 다릅니다. 이게 '
          '**"데이터셋이 다르면 최적 모델도 다르다"** 는 우리 논문 주장의 근거입니다.')

    d.h1('10.3 더 알고 싶을 때 볼 문서')
    d.table(['궁금한 것', '볼 문서'],
            [['yaml 한 줄 한 줄 전부', '문서/교재/ 4권 yaml완전해부 (31쪽)'],
             ['학습이 왜 되는지 원리', '문서/교재/ 3권 학습의원리'],
             ['명령어 → 코드 내부에서 무슨 일이', '문서/교재/ 5권 코드가도는순서'],
             ['IoU 를 손으로 계산하는 법', '문서/교재/ 7권 채점하는법'],
             ['교수님 예상 질문 대비', '문서/260726_교수님_예상질문_대비_용어집.pdf (51쪽)'],
             ['FruitSeg30 결과 전체', 'reports/FruitSeg30_학습결과_설명서.pdf (33쪽)'],
             ['서버 다시 접속하는 법', 'reports/서버_재접속_안내서.pdf'],
             ['발표할 PPT', '문서/260726_FruitSeg30_랩미팅_발표.pptx (30슬라이드)'],
             ['발표 멘트', '문서/260725_FruitSeg30_발표슬라이드_정리.md'],
             ['**이 문서의 복붙용 원본**', '**문서/260727_학습_돌리는법_완전가이드.md**']],
            [.36, .64], size=8.8)

    d.save()


if __name__ == '__main__':
    build()
