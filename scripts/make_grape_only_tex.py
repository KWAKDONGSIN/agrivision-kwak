# -*- coding: utf-8 -*-
"""팀 공동 논문(main.tex)에서 **포도 부분만 남긴 단독 판본**을 만든다.

왜 별도 파일인가
  `main.tex` 는 4작물(블루베리·복숭아·사과·포도) **팀 공동 원고**다. 거기서 남의 작물을
  지우면 팀 원고의 범위를 혼자 바꾸는 셈이 된다. 그래서 **원본은 건드리지 않고**
  `main_grape_only.tex` 를 따로 만든다. 팀·교수님이 분리에 동의하면 그때 바꿔치면 된다.

무엇을 빼는가
  - 블루베리/복숭아/사과 데이터셋 표·예시사진·교차 일반화(leave-one-dataset-out)
  - 4작물이 다 모여야 채워지는 Results 템플릿 절과 부록의 9x7 빈 행렬
무엇을 남기는가
  - 서론·Related work·Method(공통 프로토콜) — 포도 기준으로 문장만 고침
  - 곽동신이 실제로 낸 결과 전부: 파일럿 4조합 / 54조합 그리드 / 통계 / 효율성 / 정성분석

사용:  $PY tools/make_grape_only_tex.py
"""
import re
from pathlib import Path

PAPER = Path('/data/project/2026summer/kds0206/문서/260730_논문초안_LaTeX')
SRC = PAPER / 'main.tex'
DST = PAPER / 'main_grape_only.tex'


def block(text, start, end=None):
    """start 앵커부터 end 앵커 직전까지 잘라낸다."""
    i = text.index(start)
    j = text.index(end, i) if end else len(text)
    return text[i:j]


s = SRC.read_text(encoding='utf-8')

# ── 1. 프리앰블 (제목·저자·초록만 포도용으로 교체) ────────────────────────────
pre = block(s, s[:200].splitlines()[0], '\\section{Introduction}')

pre = re.sub(
    r'\\title\[[^\]]*\]\{[^}]*\}',
    r'\\title[Head--backbone benchmark for grape-bunch segmentation]{Which segmentation '
    r'head and which backbone for dense grape-bunch segmentation? A capacity-controlled '
    r'54-combination benchmark on the CERTH grape dataset}',
    pre, count=1)

# 저자: 포도 담당 + 지도교수만. 팀 공동 원고와 명단이 다르다는 점을 주석으로 남긴다.
pre = re.sub(
    r'(\\author\[1\]\{\\fnm\{Jaehun\}.*?)(?=\\affil)',
    '\\\\author*[1]{\\\\fnm{Dongshin} \\\\sur{Kwak}}\\\\email{author@example.com}\n'
    '\\\\author[1]{\\\\fnm{Hongryul} \\\\sur{Ahn}}\\\\email{corresponding.author@example.com}\n'
    '% [KDS] 이 판본은 포도 단독본이라 저자를 축소했다. 팀 공동 원고(main.tex)의 명단과 다르다.\n'
    '% \\\\todo{저자 명단·순서는 지도교수님 확인 필요}\n\n',
    pre, count=1, flags=re.S)

abstract = r"""\abstract{
\textbf{Purpose:} Dense fruit segmentation from hand-held orchard imagery differs from conventional scene segmentation because each image generally contains a single target class but many small, touching, and partially occluded fruits. A named segmentation model bundles a backbone, a decoder head, a pretraining source, and an input-resolution policy, so comparing complete models cannot reveal which component drives a gain. This study isolates the two components on one crop: dense grape bunches.
\textbf{Methods:} Nine modular segmentation heads (FCN, U-Net, FPN, PSPNet, DeepLabv3+, UPerNet, a SegFormer-inspired All-MLP head, FaPN, and CCASeg) are crossed with six ImageNet-1K-pretrained backbones (ResNet-50, ConvNeXt-T, Swin-T, MiT-B2, PVTv2-B2, and UniFormer-S), giving 54 combinations trained under an identical protocol on the CERTH grape dataset. All runs share the split, crop policy, augmentation, optimizer, loss, budget, checkpoint rule, and evaluation. Because the same test images are segmented by every combination, comparisons are paired and are analysed with blocked Friedman tests, decomposed into head and backbone main effects to preserve statistical power. Accuracy is reported jointly with parameters, FLOPs, and inference latency.
\textbf{Results:} All 54 runs completed without failure. U-Net + ConvNeXt-T attained the highest test foreground IoU (0.859). The head main effect exceeded the backbone main effect (range 0.079 versus 0.057); both Friedman tests rejected equality ($p=2.6\times10^{-88}$ and $p=5.6\times10^{-40}$). Parameters varied by a factor of 1.5 across the grid while FLOPs varied by 2.3 and latency by 3.0, so parameter count is a poor proxy for computational cost. The most accurate combination was also among the fastest.
\textbf{Conclusion:} On dense grape imagery the decoder head matters more than the backbone, which reverses the ordering the same protocol produces on blueberry imagery and argues against transferring a single recommended architecture across crops without re-evaluation. \todo{Confirm against the full-resolution, multi-split grape study before submission; the present results use 100 images and one split.}}
"""
i, j = pre.index('\\abstract{'), pre.index('\\keywords{')
pre = pre[:i] + abstract + '\n' + pre[j:]

# ── 2. 서론 — 연구질문·기여를 포도 단독 기준으로 다시 씀 ──────────────────────
intro_src = block(s, '\\section{Introduction}', '\\section{Related work}')
keep = intro_src.split('\n\n')
intro = '\n\n'.join([keep[0], keep[1], keep[2], keep[3]])          # 1~4문단 유지
intro = intro.replace(
    'AgriVision DB-1 contains 1,195 manually reviewed high-resolution smartphone images and '
    '51,145 blueberry instances under dense and occluded greenhouse conditions '
    '\\citep{owais2025agrivision}. The peach dataset contains 125 orchard images and 1,077 '
    'annotated fruit instances, with a strong emphasis on small and obscured peaches '
    '\\citep{seo2024peach}. MinneApple provides approximately 1,000 high-resolution orchard '
    'images and more than 41,000 apple instances with polygonal masks '
    '\\citep{hani2020minneapple}. The CERTH grape dataset contains 2,502 images and 9,832 '
    'annotated grape bunches collected under varying illumination, viewpoints, and maturity '
    'stages \\citep{blekos2023grape}.',
    'Grape imagery is a representative instance of this regime: the CERTH grape dataset '
    'contains 2,502 images and 9,832 annotated bunches collected under varying illumination, '
    'viewpoints, and maturity stages \\citep{blekos2023grape}. A bunch is a compound target '
    'whose berries touch one another, whose boundary is frequently interrupted by leaves and '
    'canes, and whose colour in the veraison stage is close to that of the surrounding '
    'foliage. Comparable dense single-class datasets exist for blueberry '
    '\\citep{owais2025agrivision}, peach \\citep{seo2024peach} and apple '
    '\\citep{hani2020minneapple}, and are used here only as points of reference.')

intro += r"""
This study therefore reports a controlled head--backbone benchmark for dense grape-bunch
segmentation. The research questions are:

\begin{enumerate}
    \item Which segmentation head and which backbone give the highest accuracy on dense grape imagery when every other factor is held fixed?
    \item Which of the two components dominates, and is the ordering strong enough to survive a paired statistical test?
    \item Is the accuracy ranking compatible with the computational-cost ranking, or must accuracy be traded against latency and operations?
\end{enumerate}

The contributions are threefold. First, nine modular heads and six hierarchical backbones are
crossed in a capacity-controlled factorial design and trained to completion under one shared
protocol, so that a difference between two cells can be attributed to the architectural
difference between them. Second, the paired structure of the design is used deliberately:
rather than testing all 54 combinations against too few blocks, the analysis is decomposed
into head and backbone main effects, which is what makes the post-hoc comparison informative.
Third, accuracy is reported together with parameters, FLOPs, and measured latency, which shows
that parameter count --- the fairness criterion most often used in this literature --- is the
least informative of the three.

\todo{[KDS] 이 파일은 팀 공동 원고 \texttt{main.tex} 에서 포도 부분만 뽑아낸 단독 판본이다.
어느 쪽을 최종본으로 할지는 지도교수님·팀 결정 사항이다.}

"""

# ── 3. Method — 범위·데이터셋 절을 포도용으로 새로 씀 ─────────────────────────
related = block(s, '\\section{Related work}', '\\section{Materials and methods}')

methods_head = r"""\section{Materials and methods}

\subsection{Benchmark scope and task definition}

The task is binary semantic segmentation of grape bunches in hand-held vineyard imagery. For
an image $x\in\mathbb{R}^{H\times W\times3}$ a model predicts a foreground probability map
$p\in[0,1]^{H\times W}$; bunch pixels form the foreground class and all remaining pixels the
background class. Instance annotations are unioned into a binary target $y\in\{0,1\}^{H\times
W}$. Original instance identifiers are retained for density and size diagnostics but are never
used as training targets.

The benchmark is a complete factorial design of nine modular segmentation heads and six
hierarchical backbones, giving $9\times6=54$ combinations. The head set is FCN, a U-Net-style
head, FPN, PSPNet, DeepLabv3+, UPerNet, a SegFormer-inspired All-MLP head, FaPN, and CCASeg.
The backbone set is ResNet-50, ConvNeXt-T, Swin-T, MiT-B2, PVTv2-B2, and UniFormer-S.
MambaVision-T was specified during design but is excluded for the hardware reason given in
Section~\ref{sec:audit}.

The design estimates the main effect of the head, the main effect of the backbone, and their
interaction. Every combination uses the same split, input policy, augmentation policy,
pretraining level, optimization budget, checkpoint-selection rule, and evaluation procedure,
so a difference between cells is attributable to architecture rather than to unequal training
conditions.

\subsection{Dataset}

The CERTH grape dataset \citep{blekos2023grape} comprises 2,502 vineyard images with 9,832
annotated bunches, released with COCO run-length instance masks and a 2,000/251/251 partition.
Masks were decoded to binary PNG and unioned per image. The present study uses a
randomly drawn 100-image subset of the released training partition (seed 42) re-split
$70/10/20$, which is the scale at which the protocol was exercised before committing to the
full study; Section~\ref{sec:pilot} states the resulting limitations explicitly.

Measured on that subset, the foreground occupies 12.96\,\% of image area on average
(0.52--39.92\,\%) with 4.14 bunches per image (1--12) and no empty masks. The foreground
fraction is roughly five times that of dense blueberry or apple imagery, so mean IoU over both
classes remains partially informative here; foreground IoU and foreground Dice are nevertheless
used as the primary metrics for comparability with the denser datasets.

\begin{figure}[t]
\centering
\begin{minipage}[t]{0.47\linewidth}\centering\figcell{figures/datasets/grape_image.jpg}{CERTH grape image}\\[-1mm]\textbf{(a) Input}\end{minipage}
\begin{minipage}[t]{0.47\linewidth}\centering\figcell{figures/datasets/grape_mask.png}{CERTH grape mask}\\[-1mm]\textbf{(b) Binary mask}\end{minipage}
\caption{Representative CERTH grape image and the corresponding binary semantic mask after
union of the released instance annotations. Both panels show the centre $512\times512$ crop of
the normalised image, which is the region actually scored.}\label{fig:dataset}
\end{figure}

"""

methods_mid = block(s, '\\subsection{Segmentation head selection}',
                    '\\subsection{Cross-dataset generalization}')
stats = block(s, '\\subsection{Statistical analysis}', '\\section{Pilot experiment}')

# methods_mid·stats 에 남은 "4개 데이터셋 / 63조합" 표현을 포도 단독 기준으로 고친다
FIXES = [
    ('all 63 combinations', 'all 54 combinations'),
    ('for all 63 combinations', 'for all 54 combinations'),
    ('the 63 combinations', 'the 54 combinations'),
    ('63 combinations', '54 combinations'),
    ("""A fixed crop size alone, however, is not sufficient to make the
four datasets comparable, because their native resolutions differ by a large factor.""",
     """A fixed crop size alone, however, is not sufficient to compare
results across datasets whose native resolutions differ by a large factor."""),
    ("""The fraction of the frame covered by one crop after
normalisation will be reported per dataset so that the comparability of the crop policy can be
verified rather than assumed.""",
     """The fraction of the frame covered by one crop after
normalisation is reported so that the crop policy can be verified rather than assumed."""),
    ("""At the time of writing this normalisation has been applied to the grape dataset only. The
remaining three datasets are prepared by other authors and retain their native resolution, so
the crop policy is not yet uniform across the benchmark. This is a known limitation rather than
an oversight: cross-dataset statements --- in particular any claim that one head--backbone
combination transfers across crops --- require the identical policy on all four datasets and
must therefore wait until the normalisation is applied throughout. Within-dataset comparisons
are unaffected, because every architecture sees the same images.
\\todo{[KDS] Agree the normalisation policy with the other dataset owners and re-state which
results were produced before and after it was adopted.} """,
     """All comparisons in this study are within-dataset and are therefore
unaffected by resolution differences between crops: every architecture sees exactly the same
images. Comparing these results against another crop would additionally require the identical
normalisation policy on that crop.
"""),
]
for a, b in FIXES:
    methods_mid = methods_mid.replace(a, b)
    stats = stats.replace(a, b)

# ── 4. 결과 — 기존 Pilot/그리드/효율성을 그대로 Results 로 승격 ───────────────
results = block(s, '\\section{Pilot experiment}', '\\section{Results}')
results = results.replace('\\section{Pilot experiment}', '\\section{Results}', 1)
results = results.replace(
    '\\todo{[KDS] Add the equivalent grid for blueberry, peach and apple once the other dataset\n'
    'owners have run it, then move the cross-crop comparison into the Results section.}',
    '\\todo{[KDS] Replace the 100-image subset with the full 2,502-image dataset and repeat over '
    'five splits before submission. The blueberry comparison quoted in the discussion comes from '
    'a separate study using the same protocol and should be cited rather than restated here.}')

discussion = r"""\section{Discussion}

The head main effect exceeds the backbone main effect on this dataset (0.079 against 0.057 in
IoU), and the gap survives a paired rank test with a wide margin. The practical reading is that
for a compound, boundary-dominated target such as a grape bunch, how the decoder recovers
resolution matters more than which encoder produced the features. This is consistent with the
error structure in Figure~\ref{fig:qualgrape}: the residual error is concentrated at cluster
boundaries and on partially occluded berries rather than on whole missed bunches, and boundary
recovery is precisely what distinguishes the decoders.

Two extremes dominate the ordering rather than a smooth gradient. FCN is clearly last among
heads and ResNet-50 clearly last among backbones, while the remaining five backbones lie within
0.014 IoU of one another. The useful contrast among encoders is therefore not ``convolutional
versus attention'' but ``the older residual encoder versus everything more recent'', and the
choice among modern encoders can be driven by cost rather than accuracy.

The efficiency measurements argue against the fairness criterion most often used in this
literature. Across the grid, parameters vary by a factor of 1.5, FLOPs by 2.3, and median
latency by 3.0. A capacity band expressed in parameters therefore does not constrain
computational cost, and deployability claims require measured latency and memory on the target
device. On this dataset accuracy and efficiency were not in tension at the top of the ranking:
the most accurate combination was also among the fastest.

The reversal against blueberry deserves emphasis. Under the same protocol and code base, the
blueberry data produce the opposite ordering, with the backbone spread several times the head
spread. If this reversal holds at full scale, a single recommended architecture cannot be
transferred between crops without re-evaluation, which is a direct argument for crop-specific
benchmarking rather than for a universal recommendation.

Three limitations bound every statement above. The experiments use 100 images, which is
4\,\% of the available grape data; a single split gives no estimate of between-split variance;
and evaluation uses a centre crop covering about 44\,\% of each normalised image, so peripheral
bunches are neither scored nor penalised. The binary formulation also merges touching bunches,
so pixel accuracy should not be read as bunch-counting accuracy. \todo{Repeat at full scale
over repeated splits, and add whole-image or sliding-window evaluation, before any of the above
is stated as a finding.}

\section{Conclusion}

Nine modular segmentation heads were crossed with six ImageNet-pretrained backbones and trained
to completion under one shared protocol on dense grape imagery, giving 54 comparable cells. The
decoder head, not the backbone, dominated accuracy; U-Net + ConvNeXt-T was the most accurate
combination and was also among the fastest; and parameter count proved a poor proxy for
computational cost. Because the same protocol yields the opposite component ordering on
blueberry imagery, architecture recommendations for dense fruit segmentation should be reported
per crop rather than as a single ranking. \todo{Restate with full-scale, multi-split numbers
before submission.}

"""

decl = block(s, '\\backmatter', '\\begin{appendices}' if '\\begin{appendices}' in s else '\\end{document}')

out = (pre + intro + related + methods_head + methods_mid + stats
       + results + discussion + decl + '\n\\end{document}\n')

DST.write_text(out, encoding='utf-8')

# ── 검증 ──────────────────────────────────────────────────────────────────────
refs = re.findall(r'\\fig(?:cell|wide)\{([^}]+)\}', out)
missing = [r for r in dict.fromkeys(refs) if not (PAPER / r).exists()]
banned = [w for w in ('peach', 'MinneApple', 'blueberry_image', 'apple_image',
                      'leave-one-dataset-out') if w in out]
print(f'[+] {DST}')
print(f'    {len(out.splitlines()):,}줄 / 원본 {len(s.splitlines()):,}줄')
print(f'    그림 참조 {len(refs)}개, 빈 액자 {len(missing)}개 -> {missing}')
print(f'    남아 있는 타작물 흔적: {banned or "없음"}')
for tag in ('\\begin{document}', '\\end{document}', '\\maketitle'):
    print(f'    {tag}: {out.count(tag)}회')
print(f'    빨간 TODO: {out.count(chr(92) + "todo{")}개')
