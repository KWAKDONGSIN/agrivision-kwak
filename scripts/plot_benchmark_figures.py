"""Publication figures for the 6-fold blueberry segmentation benchmark.

Reads output/results_summary.csv and writes to reports/figures/:
  fig_backbone_bars.{pdf,png}   -- backbone marginal fg_IoU, sorted, with std
  fig_head_backbone_heatmap.{pdf,png} -- head x backbone fg_IoU grid

Color follows the dataviz method: one sequential blue hue for magnitude.
Light theme only (print on white). Values direct-labeled so identity is never
color-alone.
"""
import csv
import statistics as st
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

REPO = Path(__file__).resolve().parent.parent
CSV = REPO / 'output' / 'results_summary.csv'
OUT = REPO / 'reports' / 'figures'
OUT.mkdir(parents=True, exist_ok=True)

HEADS = ['ccaseg', 'mask2former', 'oneformer', 'upernet']
HNAME = {'ccaseg': 'CCASeg', 'mask2former': 'Mask2Former',
         'oneformer': 'OneFormer', 'upernet': 'UPerNet'}
BB = ['convnext_t', 'mit_b2', 'pvtv2_b2', 'uniformer_s',
      'poolformer_s36', 'swin_t', 'resnetd_50', 'resnet_50']
BNAME = {'resnet_50': 'ResNet-50', 'resnetd_50': 'ResNetD-50',
         'convnext_t': 'ConvNeXt-T', 'swin_t': 'Swin-T', 'mit_b2': 'MiT-B2',
         'pvtv2_b2': 'PVTv2-B2', 'poolformer_s36': 'PoolFormer-S36',
         'uniformer_s': 'UniFormer-S'}

# dataviz sequential blue ramp (references/palette.md)
BLUE = ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#184f95']
CMAP = LinearSegmentedColormap.from_list('seqblue', ['#eef5fd'] + BLUE)
BAR = '#2a78d6'          # single-hue bars (categorical slot 1)
LOW = '#e34948'         # relief highlight for the outlier bar
INK = '#0b0b0b'
MUTE = '#52514e'
GRID = '#e6e6e2'

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 10,
    'axes.edgecolor': MUTE, 'axes.linewidth': 0.8,
    'text.color': INK, 'axes.labelcolor': INK,
    'xtick.color': MUTE, 'ytick.color': MUTE,
    'figure.dpi': 150, 'savefig.bbox': 'tight',
})


def load():
    rows = [r for r in csv.DictReader(open(CSV))
            if r['head'] in HEADS and r['backbone'] in BB and r['fg_IoU']]
    iou = {(r['head'], r['backbone'], r['fold']): float(r['fg_IoU']) for r in rows}
    return iou


def backbone_stats(iou):
    out = {}
    for b in BB:
        v = [iou[k] for k in iou if k[1] == b]
        out[b] = (st.mean(v), st.pstdev(v), len(v))
    return dict(sorted(out.items(), key=lambda kv: kv[1][0]))  # ascending -> barh bottom=lowest


def fig_backbone_bars(iou):
    data = backbone_stats(iou)
    names = [BNAME[b] for b in data]
    means = [data[b][0] for b in data]
    stds = [data[b][1] for b in data]
    colors = [LOW if b == 'resnet_50' else BAR for b in data]

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    y = range(len(names))
    ax.barh(list(y), means, height=0.62, color=colors, zorder=3,
            error_kw=dict(ecolor=MUTE, lw=1.1, capsize=3, capthick=1.1),
            xerr=stds)
    # rounded data-ends: overlay a thin marker not needed; keep flat but clean
    for i, (m, s) in enumerate(zip(means, stds)):
        ax.text(m + s + 0.004, i, f'{m:.4f}', va='center', ha='left',
                fontsize=9, color=INK)

    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=9.5)
    ax.set_xlabel('Foreground IoU  (mean ± std over 4 heads × 6 folds)')
    ax.set_xlim(0.78, 0.905)
    ax.set_title('Backbone marginal performance', fontsize=12, weight='bold',
                 loc='left', color=INK, pad=10)
    ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for sp in ('top', 'right', 'left'):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0)
    fig.text(0.01, -0.02,
             'ResNet-50 (red) trails the next backbone by 0.033–0.038 — an order of '
             'magnitude larger than any head-level gap.',
             fontsize=8, color=MUTE)
    for ext in ('pdf', 'png'):
        fig.savefig(OUT / f'fig_backbone_bars.{ext}')
    plt.close(fig)


def fig_heatmap(iou):
    # rows = backbones (best at top), cols = heads
    order = sorted(BB, key=lambda b: -st.mean([iou[k] for k in iou if k[1] == b]))
    grid = []
    ncell = {}
    for b in order:
        row = []
        for h in HEADS:
            v = [iou[k] for k in iou if k[0] == h and k[1] == b]
            row.append(st.mean(v) if v else float('nan'))
            ncell[(b, h)] = len(v)
        grid.append(row)

    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    vmin = min(v for r in grid for v in r)
    vmax = max(v for r in grid for v in r)
    im = ax.imshow(grid, cmap=CMAP, vmin=vmin, vmax=vmax, aspect='auto')

    best = max(((i, j) for i in range(len(order)) for j in range(len(HEADS))),
               key=lambda ij: grid[ij[0]][ij[1]])
    for i in range(len(order)):
        for j in range(len(HEADS)):
            val = grid[i][j]
            # text ink adapts to cell darkness for contrast
            frac = (val - vmin) / (vmax - vmin + 1e-9)
            tc = '#ffffff' if frac > 0.6 else INK
            lbl = f'{val:.4f}'
            if ncell[(order[i], HEADS[j])] < 6:
                lbl += '*'
            ax.text(j, i, lbl, ha='center', va='center', fontsize=9, color=tc)
            if (i, j) == best:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                           edgecolor='#0b0b0b', lw=2.2, zorder=5))

    ax.set_xticks(range(len(HEADS)))
    ax.set_xticklabels([HNAME[h] for h in HEADS], fontsize=9.5)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([BNAME[b] for b in order], fontsize=9.5)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    # 2px surface gap between cells
    ax.set_xticks([x - 0.5 for x in range(len(HEADS) + 1)], minor=True)
    ax.set_yticks([y - 0.5 for y in range(len(order) + 1)], minor=True)
    ax.grid(which='minor', color='#fcfcfb', lw=2)
    ax.tick_params(which='minor', length=0)

    ax.set_title('Foreground IoU by head × backbone', fontsize=12, weight='bold',
                 loc='left', color=INK, pad=10)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label('Foreground IoU', fontsize=9, color=MUTE)
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, labelsize=8)
    fig.text(0.01, -0.01,
             'Black box = overall best (UPerNet + ConvNeXt-T).  '
             '* = n<6 folds (UPerNet+MiT-B2 cv1 not trained).',
             fontsize=8, color=MUTE)
    for ext in ('pdf', 'png'):
        fig.savefig(OUT / f'fig_head_backbone_heatmap.{ext}')
    plt.close(fig)


def fig_variance_box(iou):
    """Two-panel boxplot: distribution by head (why head=noise) and by fold
    (why single-fold rankings flip). Individual runs overlaid as jittered dots."""
    import math
    fig, (axh, axf) = plt.subplots(1, 2, figsize=(10.4, 4.6),
                                   gridspec_kw=dict(width_ratios=[4, 6], wspace=0.22))

    def _box(ax, groups, labels, title, xlabel):
        data = [groups[g] for g in labels]
        bp = ax.boxplot(data, vert=True, widths=0.58, patch_artist=True,
                        showfliers=False, zorder=2,
                        medianprops=dict(color=INK, lw=1.6),
                        whiskerprops=dict(color=MUTE, lw=1.0),
                        capprops=dict(color=MUTE, lw=1.0),
                        boxprops=dict(facecolor='#dcebfb', edgecolor=BAR, lw=1.2))
        # deterministic jitter (no RNG): spread points evenly within the box slot
        for i, vals in enumerate(data, start=1):
            n = len(vals)
            for j, v in enumerate(sorted(vals)):
                dx = ((j / max(n - 1, 1)) - 0.5) * 0.34
                ax.plot(i + dx, v, 'o', ms=4.2, mfc=BAR, mec='#fcfcfb',
                        mew=0.5, alpha=0.75, zorder=3)
        # mean marker (diamond)
        for i, vals in enumerate(data, start=1):
            ax.plot(i, sum(vals) / len(vals), 'D', ms=7, mfc=LOW,
                    mec='#fcfcfb', mew=0.8, zorder=4)
        ax.set_xticks(range(1, len(labels) + 1))
        # long head labels collide in the narrow panel -> rotate; short fold labels stay flat
        rot = 20 if max(len(x) for x in labels) > 4 else 0
        ax.set_xticklabels(labels, fontsize=9.5, rotation=rot,
                           ha='right' if rot else 'center')
        ax.set_title(title, fontsize=11.5, weight='bold', loc='left',
                     color=INK, pad=8)
        ax.yaxis.grid(True, color=GRID, lw=0.8, zorder=0)
        ax.set_axisbelow(True)
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
        ax.tick_params(length=0)

    by_head = {HNAME[h]: [iou[k] for k in iou if k[0] == h] for h in HEADS}
    _box(axh, by_head, [HNAME[h] for h in HEADS],
         'Distribution by head', 'n≈47–48 runs each')
    axh.set_ylabel('Foreground IoU', fontsize=9.5, color=INK)

    by_fold = {f'cv{f}': [iou[k] for k in iou if k[2] == f] for f in '123456'}
    _box(axf, by_fold, [f'cv{f}' for f in '123456'],
         'Distribution by fold', 'n≈31–32 runs each')

    fig.text(0.01, -0.03,
             'Box = IQR, line = median, red diamond = mean, dots = individual runs.  '
             'Left: heads overlap heavily (differences not significant).  '
             'Right: folds differ systematically — cv1 is hardest, cv2 easiest — '
             'which is why a single fold reshuffles the head ranking.',
             fontsize=8, color=MUTE)
    for ext in ('pdf', 'png'):
        fig.savefig(OUT / f'fig_variance_box.{ext}')
    plt.close(fig)


if __name__ == '__main__':
    iou = load()
    fig_backbone_bars(iou)
    fig_heatmap(iou)
    fig_variance_box(iou)
    print(f'Wrote figures to {OUT}')
    for f in sorted(OUT.iterdir()):
        print(f'  {f.name}  ({f.stat().st_size} B)')
