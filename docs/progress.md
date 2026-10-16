# First-pass execution ledger

Ruling: User has supplied detailed scope and explicitly asked to implement and
run it; proceed inline without redundant approval gates. No commit steps.
Ruling: Empty intended workspace is already isolated; no Git worktree needed.
Ruling: Standard-library urllib avoids a missing requests dependency and supports
timeouts and bounded retries. Public connector retrieval is used only to stage
explicitly attributed offline snapshots because shell networking is restricted.
Pre-flight: tasks 2 and 3 consume task 1 canonical DataFrames; task 4 consumes all
public interfaces. Only raw canonical columns may enter model histories.

Task 1: complete. Strict dataset validation, official JSON source adapter,
incremental collector, atomic CSV storage and attributed snapshot import.
Task 2: complete. Binary main-number series and hand-checked descriptive stats.
Task 3: complete. RandomModel, exact historical prefixes, reproducible checkpoint
and walk-forward evaluation, multi-ticket/repeat streams and bootstrap summaries.
Task 4: complete. Interactive/noninteractive CLI, documentation and real-data runs.

Validation ledger:
- New module tests were run before implementation and failed on absent modules.
- Dataset/collection/analysis suite: 26 passed after implementation.
- With backtesting: 42 passed; with CLI: 44 passed.
- Independent review found output/input collisions and null draw_no rows silently
  dropped by pandas groupby. Three regression tests reproduced the failures.
- Fixed path collisions and retained null groups for strict validation. Full
  suite: 47 passed, including both regressions and unchanged-input assertions.
- Windows sandbox reproduced a pytest directory issue: mode 0700 directories
  cannot be reopened, mode 0777/inherited ACLs work. Local test fixture uses
  inherited permissions; optional pytest cache is disabled. No ACLs were changed.
- Official collector ran and returned a clear network error (WinError 10061).
- Explicit public-snapshot import validated 1,245 contiguous draws,
  2002-12-07 through 2026-10-10. No direct official-source verification claimed.
- Walk-forward targets 300..1245, seed 42: 946 tickets, mean 0.7885835095,
  best 4 matches. Checkpoints: 100 targets, 5 tickets x 10 repeats, mean 0.7888.
- Binary export, inspect number 17 and noninteractive main.py exercised.

No Git repository was created; no commits or pushes. Files are in the user's
original empty project directory. The first-pass scope is implemented; advanced
models and periodicity remain explicitly deferred as requested.
