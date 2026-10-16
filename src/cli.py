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
    inspect.add_argument('--no-plots',action='store_true',help='Skip the nine-panel PNG')
    analyze = commands.add_parser('analyze-all',help='Export exploratory temporal statistics for all 45 numbers')
    for command in (inspect,analyze):
        command.add_argument('--reports-dir',type=Path,help='Report root; default reports/ next to dataset project')
        command.add_argument('--windows',type=int,nargs='+',default=[26,52,104])
        command.add_argument('--max-lag',type=int,default=52)
        command.add_argument('--min-cycles',type=int,default=3)
        command.add_argument('--permutations',type=int,default=199,help='Shuffles per fixed scope; 0 skips null tests')
        command.add_argument('--seed',type=int,default=42)
        command.add_argument('--percentile',type=float,default=90)
        command.add_argument('--regime-history',type=int,default=52,help='Minimum past valid scores for a threshold')
        command.add_argument('--regime-length',type=int,default=3,help='Minimum consecutive high endpoints')
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
    from src.prediction_cli import add_commands
    add_commands(commands)
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
    print("Temporal exploration and experimental ranking models. No validated predictive advantage.")


def _inspect(history, number):
    stats = inspect_number(history, number)
    print(f"Number {number}")
    print(f"Total appearances: {stats['total_frequency']} / {stats['observed_draws']}")
    print(f"Overall appearance rate: {stats['appearance_rate']:.4%}")
    print(f"Current gap: {stats['current_gap'] if stats['current_gap'] is not None else 'never observed'}")
    print(f"Mean historical gap: {stats['mean_gap']}; median: {stats['median_gap']}")
    print(f"Gap variance: {stats['gap_variance']}; standard deviation: {stats['gap_std']}")
    print(f"Consecutive pairs: {stats['consecutive_pairs']}; longest run: {stats['longest_run']}")
    print(f"Longest observed absence: {stats['longest_absence']} draws; boundary-censored: {stats['longest_absence_touches_boundary']}")
    for n, recent in stats['recent'].items():
        print(f"Recent {n} draw frequency: {recent['frequency']}/{recent['observed_draws']} ({recent['rate']:.2%})")
    for warning in stats['warnings']:
        print(f"Note: {warning}")


def _explore(args,history):
    from src.analysis.exploration import analyze_history,report_paths,write_reports
    from src.analysis.periodicity import PeriodicityConfig
    from src.analysis.temporal import selected_numbers
    number=args.number if args.command=='inspect' else None
    if number is not None: selected_numbers([number])
    config=PeriodicityConfig(max_lag=args.max_lag,min_cycles=args.min_cycles)
    root=args.reports_dir or (ROOT/'reports' if args.data.resolve()==DEFAULT_DATA.resolve() else args.data.parent/'reports')
    directory=root/f'number_{number}' if number is not None else root
    destinations=report_paths(directory)
    if number is not None and not args.no_plots:
        destinations.append(root/'plots'/f'number_{number:02d}_temporal.png')
    _guard_outputs(args.data,*destinations)
    analysis=analyze_history(history,numbers=[number] if number is not None else None,
                             windows=args.windows,config=config,permutations=args.permutations,seed=args.seed,
                             percentile=args.percentile,min_history=args.regime_history,min_length=args.regime_length,
                             progress=lambda message:print(message,flush=True))
    analysis['metadata']['source_csv_sha256']=hashlib.sha256(args.data.read_bytes()).hexdigest()
    analysis['metadata']['source_path']=str(args.data.resolve())
    write_reports(analysis,directory)
    if number is not None:
        _inspect(history,number)
        diagnostics=analysis['diagnostics'][number]
        print(f"Strongest positive ACF lags (full history): {diagnostics['autocorrelation']['candidates'] or diagnostics['autocorrelation']['status']}")
        print(f"Dominant spectral periods (full history): {diagnostics['spectrum']['candidates'] or diagnostics['spectrum']['status']}")
        rolling=analysis['tables']['rolling_number_stats']
        for window in args.windows:
            group=rolling[rolling.window_size==window]
            if group.empty:
                print(f'Current {window}-draw periodicity: insufficient observations')
            else:
                row=group.iloc[-1]
                score='unavailable' if pd.isna(row.periodicity_score) else f'{row.periodicity_score:.4f}'
                lag='unavailable' if pd.isna(row.dominant_lag) else row.dominant_lag
                period='unavailable' if pd.isna(row.dominant_period) else row.dominant_period
                print(f'Current {window}-draw periodicity score: {score}; status={row.status}; lag={lag}; period={period}')
        regimes=analysis['tables']['periodicity_regimes']
        print(f'Historical high-periodicity regimes: {len(regimes)} (across window sizes)')
        if not regimes.empty:
            print(regimes[['window_size','start_draw','end_draw','peak_periodicity_score','dominant_period']].tail(8).to_string(index=False))
        print('Regime recurrence (overlapping support combined):')
        print(analysis['tables']['regime_recurrence'][['window_size','regime_count','independent_episodes','recurring_interval_candidate','status']].to_string(index=False))
        print('Fixed-scope conditional shuffle comparisons:')
        print(analysis['tables']['periodicity_null'][['scope','observed_score','p_value','p_bonferroni','status']].to_string(index=False))
        if not args.no_plots:
            from src.analysis.plots import plot_number
            print(f"Plot: {plot_number(history,number,analysis,root/'plots',config)}")
    else:
        print(f"Generated temporal reports for 45 numbers through draw {analysis['metadata']['cutoff_draw']}.")
        print(f"Rows per report: {analysis['metadata']['row_counts']}")
    print(f'Reports: {directory}')
    print(f"Analysis runtime (excluding exports/plots): {analysis['metadata']['runtime_seconds']}")
    for warning in analysis['metadata']['warnings']: print(f'Note: {warning}')


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
            _explore(args,history)
        elif args.command == 'analyze-all':
            _explore(args,history)
        elif args.command == 'export-series':
            _guard_outputs(args.data, args.output)
            atomic_write(args.output, binary_series(history).to_csv(lineterminator='\n'))
            print(f'Binary series saved to {args.output}')
        elif args.command == 'backtest':
            _backtest(args, history)
        elif args.command in ('compare-models','predict-current','explain-number'):
            from src.prediction_cli import run_command
            run_command(args,history,_guard_outputs)
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
