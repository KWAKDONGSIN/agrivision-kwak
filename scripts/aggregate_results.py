"""Aggregate TensorBoard scalars from output/ into a single CSV + pivot tables.

Each run directory is named <head>_<backbone>_bcedice_cv<N> and holds logs/ with
one or more event files. Early stopping monitors val_loss, so the reported row is
the epoch with the lowest val/loss -- the epoch whose weights are in *_best.pth.

Usage:
    python tools/aggregate_results.py                      # all runs -> output/results_summary.csv
    python tools/aggregate_results.py --folds 1 2 3        # only cv1..cv3
    python tools/aggregate_results.py --metric fg_Dice     # pivot on a different metric
"""
import argparse
import csv
import re
import statistics
from collections import defaultdict
from pathlib import Path

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

RUN_RE = re.compile(r'^(?P<head>[^_]+)_(?P<backbone>.+)_bcedice_cv(?P<fold>\d+)$')

# Foreground metrics first: mIoU/mDice average in a ~0.99 background class and
# hide the differences between combinations.
METRICS = [
    'val/fg_IoU', 'val/fg_Dice', 'val/fg_Precision', 'val/fg_Recall',
    'val/mIoU', 'val/mDice', 'val/loss',
]


def read_scalars(log_dir):
    """Return {tag: {step: value}}, keeping the latest value per step.

    A run that was restarted leaves several event files in the same directory and
    their steps overlap, so later wall_times must win.
    """
    ea = EventAccumulator(str(log_dir), size_guidance={'scalars': 0})
    ea.Reload()
    available = set(ea.Tags()['scalars'])

    out = {}
    for tag in METRICS:
        if tag not in available:
            continue
        by_step = {}
        for ev in sorted(ea.Scalars(tag), key=lambda e: e.wall_time):
            by_step[ev.step] = ev.value
        out[tag] = by_step
    return out


def summarize_run(run_dir):
    """Pick the best-val_loss epoch and return one flat record, or None."""
    scalars = read_scalars(run_dir / 'logs')
    losses = scalars.get('val/loss')
    if not losses:
        return None

    best_step = min(losses, key=lambda s: losses[s])

    record = {
        'best_epoch': best_step + 1,  # steps are 0-indexed in train.py
        'epochs_logged': max(losses) + 1,
        'n_val_points': len(losses),
    }
    for tag in METRICS:
        key = tag.split('/', 1)[1]
        record[key] = scalars.get(tag, {}).get(best_step)

    # Peak fg_IoU regardless of the val_loss criterion -- useful to spot runs
    # where val_loss and fg_IoU disagree about which epoch was best.
    fg = scalars.get('val/fg_IoU')
    record['peak_fg_IoU'] = max(fg.values()) if fg else None
    return record


def collect(output_dir, folds):
    rows, skipped = [], []
    for run_dir in sorted(p for p in output_dir.iterdir() if p.is_dir()):
        m = RUN_RE.match(run_dir.name)
        if not m:
            continue
        fold = int(m.group('fold'))
        if folds and fold not in folds:
            continue
        if not (run_dir / 'logs').is_dir():
            skipped.append((run_dir.name, 'no logs/'))
            continue

        record = summarize_run(run_dir)
        if record is None:
            skipped.append((run_dir.name, 'no val/loss scalars'))
            continue

        rows.append({
            'run': run_dir.name,
            'head': m.group('head'),
            'backbone': m.group('backbone'),
            'fold': fold,
            'has_best_ckpt': bool(list(run_dir.glob('*_best.pth'))),
            **record,
        })
    return rows, skipped


def fmt(value, width=7, prec=4):
    return f'{value:{width}.{prec}f}' if isinstance(value, float) else ' ' * (width - 1) + '-'


def print_pivot(rows, metric):
    """head x backbone table of mean+-std across folds."""
    grouped = defaultdict(list)
    for r in rows:
        if isinstance(r.get(metric), float):
            grouped[(r['head'], r['backbone'])].append(r[metric])

    if not grouped:
        print(f'\n(no data for {metric})')
        return

    heads = sorted({h for h, _ in grouped})
    backbones = sorted({b for _, b in grouped})
    width = max(len(b) for b in backbones) + 2

    print(f'\n=== {metric} : mean +- std across folds ===')
    print('backbone'.ljust(width) + ''.join(h.center(18) for h in heads))
    for b in backbones:
        line = b.ljust(width)
        for h in heads:
            vals = grouped.get((h, b), [])
            if not vals:
                cell = '-'
            elif len(vals) == 1:
                cell = f'{vals[0]:.4f} (n=1)'
            else:
                cell = f'{statistics.mean(vals):.4f}+-{statistics.stdev(vals):.4f}'
            line += cell.center(18)
        print(line)

    print('\n--- head averages ---')
    for h in heads:
        vals = [v for (hh, _), vs in grouped.items() if hh == h for v in vs]
        print(f'  {h:<14} {statistics.mean(vals):.4f}  (n={len(vals)})')

    best = max(grouped.items(), key=lambda kv: statistics.mean(kv[1]))
    print(f'\n  best combination: {best[0][0]} + {best[0][1]} '
          f'= {statistics.mean(best[1]):.4f} (n={len(best[1])})')


def main():
    repo = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--output-dir', type=Path, default=repo / 'output')
    ap.add_argument('--csv', type=Path, default=repo / 'output' / 'results_summary.csv')
    ap.add_argument('--folds', type=int, nargs='*', default=None,
                    help='restrict to these fold numbers (default: all)')
    ap.add_argument('--metric', default='fg_IoU',
                    help='metric for the pivot table (default: fg_IoU)')
    args = ap.parse_args()

    rows, skipped = collect(args.output_dir, set(args.folds) if args.folds else None)
    if not rows:
        print(f'No runs found under {args.output_dir}')
        return

    fields = ['run', 'head', 'backbone', 'fold', 'best_epoch', 'epochs_logged',
              'n_val_points', 'has_best_ckpt', 'peak_fg_IoU'] + \
             [t.split('/', 1)[1] for t in METRICS]
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f'Wrote {len(rows)} runs -> {args.csv}')
    folds_seen = sorted({r['fold'] for r in rows})
    print(f'folds: {folds_seen}   heads: {sorted({r["head"] for r in rows})}')

    if skipped:
        print(f'\nskipped {len(skipped)} run(s):')
        for name, why in skipped:
            print(f'  {name}: {why}')

    # Short runs (early stopped, interrupted, or still training) sit in the same
    # table as full 100-epoch runs and would otherwise skew the fold averages.
    partial = [r for r in rows if r['n_val_points'] < 5]
    if partial:
        print(f'\n{len(partial)} short run(s) -- early stopped, interrupted, or in progress:')
        for r in partial:
            print(f"  {r['run']}: {r['n_val_points']} val points, "
                  f"last epoch {r['epochs_logged']}, best fg_IoU {r['peak_fg_IoU']:.4f}")

    print_pivot(rows, args.metric)


if __name__ == '__main__':
    main()
