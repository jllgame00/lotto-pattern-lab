"""Small terminal interface; no web server or frontend."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.series import binary_series
from src.analysis.statistics import inspect_number
from src.backtest.engine import run_backtest
from src.backtest.metrics import summarize
from src.collect.collector import atomic_write, collect_history, import_history
from src.collect.dataset import load_history
from src.models.base import TargetDrawContext
from src.models.random_model import RandomModel

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data/raw/lotto_history.csv"


def _guard_outputs(data_path: Path, *outputs: Path) -> None:
    protected = [data_path, data_path.with_suffix('.metadata.json'), data_path.parent / 'sources.json']
    for output in outputs:
        for source in protected:
            if (output.resolve() == source.resolve() or
                    (output.exists() and source.exists() and output.samefile(source))):
                raise ValueError(f'Output would overwrite input history or provenance: {output}')


def _parser():
    parser = argparse.ArgumentParser(description="Lotto Pattern Lab: historical analysis and leakage-safe backtesting")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="Canonical CSV (place before subcommand)")
    commands = parser.add_subparsers(dest="command")
    collect = commands.add_parser("collect", help="Collect official results or explicitly import a CSV snapshot")
    collect.add_argument("--end", type=int, help="Requested final draw; default: latest reported by source")
    collect.add_argument("--input", type=Path, help="Import a canonical-schema CSV instead of HTTP collection")
    collect.add_argument("--source-label", help="Required attribution for --input")
    commands.add_parser("validate", help="Validate values, calendar and completeness")
    inspect = commands.add_parser("inspect", help="Inspect one number's descriptive statistics")
    inspect.add_argument("number", type=int)
    export = commands.add_parser("export-series", help="Export 45 binary main-number time series")
    export.add_argument("--output", type=Path, default=ROOT / "data/processed/number_series.csv")
    backtest = commands.add_parser("backtest", help="Evaluate RandomModel on unseen historical draws")
    backtest.add_argument("--mode", choices=["walk-forward", "checkpoints"], default="walk-forward")
    backtest.add_argument("--min-train", type=int, default=299)
    backtest.add_argument("--checkpoints", type=int, default=100)
    backtest.add_argument("--start", type=int)
    backtest.add_argument("--end", type=int)
    backtest.add_argument("--seed", type=int, default=42)
    backtest.add_argument("--tickets", type=int, default=1)
    backtest.add_argument("--repeats", type=int, default=1)
    backtest.add_argument("--report", type=Path, default=ROOT / "reports/random_backtest", help="Output prefix (.csv and .json)")
    candidates = commands.add_parser("candidates", help="Generate a uniform random candidate ticket")
    candidates.add_argument("--seed", type=int, default=42)
    return parser


def _status(path):
    print("=== Lotto Pattern Lab ===")
    if not path.exists():
        print("No historical dataset. Run: python main.py collect")
        return
    history = load_history(path)
    print(f"Loaded draws: 1-{int(history.draw_no.max())} ({len(history)} draws; through {history.iloc[-1].draw_date.date()})")
    metadata = path.with_suffix(".metadata.json")
    if metadata.exists():
        source = json.loads(metadata.read_text(encoding="utf-8"))
        print(f"Last collection/import source: {source.get('source', 'unknown')}")
    print("First pass: descriptive statistics and RandomModel. Advanced strategies are not implemented.")


def _inspect(history, number):
    stats = inspect_number(history, number)
    print(f"Number {number}")
    print(f"Total appearances: {stats['total_frequency']} / {stats['observed_draws']}")
    print(f"Current gap: {stats['current_gap'] if stats['current_gap'] is not None else 'never observed'}")
    print(f"Mean historical gap: {stats['mean_gap']}; median: {stats['median_gap']}")
    print(f"Gap variance: {stats['gap_variance']}; standard deviation: {stats['gap_std']}")
    print(f"Consecutive pairs: {stats['consecutive_pairs']}; longest run: {stats['longest_run']}")
    for n, recent in stats['recent'].items():
        print(f"Recent {n} draw frequency: {recent['frequency']}/{recent['observed_draws']} ({recent['rate']:.2%})")
    for warning in stats['warnings']:
        print(f"Note: {warning}")
    print("Periodicity and regime similarity are deferred to later phases.")


def _backtest(args, history):
    _guard_outputs(args.data, args.report.with_suffix('.csv'), args.report.with_suffix('.json'))
    keys = ('mode', 'min_train', 'seed', 'tickets', 'repeats', 'checkpoints', 'start', 'end')
    configuration = {key: getattr(args, key) for key in keys}
    results = run_backtest(history, RandomModel, **configuration)
    summary = summarize(results, seed=args.seed)
    summary.update(configuration=configuration,
                   created_at=datetime.now(timezone.utc).isoformat(),
                   dataset_path=str(args.data.resolve()),
                   dataset_sha256=hashlib.sha256(args.data.read_bytes()).hexdigest(),
                   versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
    metadata = args.data.with_suffix('.metadata.json')
    if metadata.exists():
        summary['dataset_provenance'] = json.loads(metadata.read_text(encoding='utf-8'))
    atomic_write(args.report.with_suffix('.csv'), results.to_csv(index=False, lineterminator='\n'))
    atomic_write(args.report.with_suffix('.json'), json.dumps(summary, indent=2, allow_nan=False) + '\n')
    print(f"RandomModel: {summary['target_draws']} targets, {summary['total_tickets']} tickets")
    print(f"Average matches: {summary['average_matches']:.6f}; random expectation: 0.800000")
    print(f"Match distribution: {summary['match_distribution']}")
    print(' | '.join(f"{n}+ match rate: {summary[f'rate_{n}_plus']:.4%}" for n in (3,4,5)))
    print(f"Best result: {summary['best_result']}; approximate 95% mean CI: {summary['mean_matches_ci95']}")
    print(f"Reports: {args.report.with_suffix('.csv')} and {args.report.with_suffix('.json')}")
    for warning in summary['warnings']:
        print(f"Note: {warning}")


def _interactive(args):
    while True:
        print("\n[1] Inspect number\n[2] Random-checkpoint backtest\n[3] Walk-forward backtest\n[4] Random candidates\n[5] Validate data\n[0] Exit")
        choice = input("Choice: ").strip()
        if choice == '0':
            return 0
        commands = {'2': ['backtest', '--mode', 'checkpoints'], '3': ['backtest'],
                    '4': ['candidates'], '5': ['validate']}
        if choice == '1':
            command = ['inspect', input('Number (1-45): ').strip()]
        elif choice in commands:
            command = commands[choice]
        else:
            print("Choose 0-5.")
            continue
        try:
            main(['--data', str(args.data), *command])
        except SystemExit:
            pass  # argparse has already explained an invalid menu argument.


def main(argv=None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command is None:
            _status(args.data)
            if sys.stdin.isatty():
                return _interactive(args)
            parser.print_help()
            return 0
        if args.command == 'collect':
            if args.input:
                if not args.source_label or args.end is not None:
                    raise ValueError('--input requires --source-label and cannot be combined with --end')
                report = import_history(args.data, args.input, args.source_label)
            else:
                report = collect_history(args.data, end=args.end)
            print(json.dumps(report, indent=2))
            return 0 if report['complete'] else 1
        history = load_history(args.data)
        if args.command == 'validate':
            _status(args.data)
            print('Validation passed: complete history; valid numbers, bonus and dates.')
        elif args.command == 'inspect':
            _inspect(history, args.number)
        elif args.command == 'export-series':
            _guard_outputs(args.data, args.output)
            atomic_write(args.output, binary_series(history).to_csv(lineterminator='\n'))
            print(f'Binary series saved to {args.output}')
        elif args.command == 'backtest':
            _backtest(args, history)
        elif args.command == 'candidates':
            target = int(history.draw_no.max()) + 1
            context = TargetDrawContext(target, history.iloc[-1].draw_date + pd.Timedelta(days=7))
            print(f'Uniform random candidate for draw {target} ({context.draw_date.date()}), seed={args.seed}: '
                  f'{RandomModel().predict(history, context=context, seed=args.seed)}')
            print('This ticket has no demonstrated predictive advantage.')
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print('\nExiting.')
        return 0
