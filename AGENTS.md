## Overview

This project is a `pytest` plugin that controls the execution of `pytest-bdd`
scenarios according to the classification tags that `gherkinator` renders
into generated `*.feature` files. Source lives in `src/pytest_gherkinator/`;
tests live in `tests/`.

The project uses:

- `uv` for dependency management and packaging.
- `just` as the task runner (see `justfile`).
- `ruff` for formatting and linting.
- `pyright` for static type checking.
- `coverage.py` for test coverage with branch coverage on `src/**/*.py`.

Private modules use the `_`-prefix convention (for example, `_main.py`,
`_constants.py`). The public API is re-exported through
`src/pytest_gherkinator/__init__.py`. Consumers and tests import from the
package root, not from private modules.

## How the plugin works

The plugin classifies collected test items from their `pytest` marks, sorts
them by risk level then test type, and skips scenarios whose plan status is
`planned` or `deprecated`. Keep these invariants in mind when editing:

1. **The mark set is the entire contract.** `src/pytest_gherkinator/_constants.py`
   defines the twelve marks (every value of the gherkinator YAML schema's
   `type`, `status`, and `risk` fields) plus the execution orders. The
   plugin never reads gherkinator YAML test plans or the `gherkinator`
   binary; `pytest` code must stay separate from gherkinator
   implementation details.
2. **Marks come from gherkinator's feature-level tag line.** gherkinator
   renders `@<type> @<risk> @<status> @<custom tags>` above the `Feature:`
   line of generated `*.feature` files (canonical/gherkinator commits
   `fff4439` and `f989cc6`), and `pytest-bdd` converts Gherkin tags into
   marks. Do not reintroduce per-plan YAML parsing or `pytest-bdd` internal
   access (for example `ScenarioTemplate`); classification is
   `item.iter_markers()` only.
3. **`pytest_collection_modifyitems` must stay a plain hook implementation.**
   `tryfirst`/`trylast`/`hookwrapper` change when it runs relative to the
   builtin mark plugin's `-m` deselection and can make the skip marks it
   adds invisible to mark-based filtering.
4. **Never guess ambiguous classifications.** An item carrying two distinct
   marks of one category (for example feature `@edge` plus scenario `@beta`)
   runs unclassified after a `GherkinatorWarning`.
5. **Degradation rules are intentional.** Missing status tag: run, never
   skip. Missing risk/type: sort last in that dimension. No classification
   marks at all: run after all classified items in original order. Do not
   "fix" these by skipping or dropping unclassified items.
6. **Sort stability is load-bearing.** Items sharing a classification keep
   their original relative order so scenarios that build state on each
   other within one feature file stay in definition order. Preserve the
   original-position tie-break in the sort key.
7. **Known limitations.** `pytest-xdist` ignores cross-worker execution
   order; reorder plugins such as `pytest-randomly` can undo the sort;
   custom plan tags (for example `@multi-node`) become marks the plugin
   does not register, so `pytest` may warn about them.

## Code style

Follow PEP 8 and PEP 257, plus:

### Imports

Three groups, alphabetized (`ruff format` handles ordering): standard
library, third-party, `pytest_gherkinator`.

### Docstrings

Every public module, class, and function must have a PEP 257 docstring.
Public modules declare `__all__` to make the public API explicit.

### Private modules

Internal modules use the `_`-prefix convention. The public API is
re-exported through `src/pytest_gherkinator/__init__.py`.

### Type annotations

All function signatures must have explicit type annotations. `just typecheck`
(pyright) validates them.

If a typing issue is found in production code (`src/pytest_gherkinator/`),
STOP and propose a resolution to the human-in-the-loop before editing
production code:

1. Describe the issue, its location, and the impact.
2. Propose a concrete fix.
3. Ask whether to proceed with the proposed fix or to research alternative
   resolutions.

Do not edit production code until the user explicitly approves the fix.

### Avoid inline error handling

```python
if path is None:
    raise FileNotFoundError(f"'{name}' does not exist")
```

Not:

```python
path = Path(name) if Path(name).exists() else None
```

Use explicit `raise` statements and intermediate variables for error
handling rather than burying the logic in one-liners or ternary
expressions.

### Comments

Do __not__ add generic one-off comments throughout the main codebase. Do
add comments in test files to provide justifications for assertions,
fixtures, and workarounds.

## Build commands

```bash
just build      # Build wheel and sdist into dist/ via `uv build`.
just clean      # Remove .venv, build artifacts, __pycache__, *.pyc.
just setup      # Create a uv dev environment (`uv sync --extra dev`).
just lock       # Regenerate uv.lock.
just upgrade    # Upgrade uv.lock with the latest dependencies.
```

## Testing

```bash
just check          # Run all static checks (`lint`, `typecheck`).
just unit           # Run unit tests with coverage report.
just test           # Run all test suites (unit).
just test <target>  # Run a specific test target.
just fmt            # Format all Python source code with ruff.
just lint           # Lint with ruff (no auto-fix).
just typecheck      # Static type checking with pyright.
```

### Unit tests

Unit tests use `pytest`'s `pytester` fixture to run the plugin in a sandbox
session. The `write_feature` fixture in `tests/unit/conftest.py` writes
`*.feature` files that byte-for-byte mirror gherkinator's `GenerateGherkin`
renderer (canonical/gherkinator @ `main`,
`internal/common/transpile.go`):

- When gherkinator's rendered output format changes, update `write_feature`
  first so the fixtures keep encoding the real contract.
- Do not shell out to the `gherkinator` binary in unit tests; the fixtures
  are the contract.

### Coverage

The target is **90% branch coverage** on `src/**/*.py`. Do __not__ write
unit tests for code paths that are impossible to reach in production.

## Development workflow

1. Write Python code in `src/pytest_gherkinator/`.
2. Write matching unit tests in `tests/unit/`.
3. Run `just unit` -- ensure all tests pass and coverage meets the 90%
   branch coverage threshold.
4. Format: `just fmt`.
5. Lint: `just lint` (uses `ruff check`). Fix all linter errors.
6. Typecheck: `just typecheck` (uses `pyright`). Fix all typing
   errors. If a typing issue is in production code, follow the
   human-in-the-loop protocol in the Code style section above.
7. Repeat for each new or modified file.

Pipe the output of shell commands to either `head` or `tail` to
capture the `stdout` and/or `stderr`.

## Commit conventions

Use Conventional Commits prefixes for commit messages:

- `feat:` -- New user-facing feature.
- `fix:` -- Bug fix.
- `test:` -- Add or modify tests only.
- `chore:` -- Maintenance tasks (formatting, dependency updates, etc.).
- `docs:` -- Documentation only.
- `refactor:` -- Code change that neither fixes a bug nor adds a feature.

Scopes are allowed (for example, `chore(deps):`, `chore(fmt):`).

### Commit trailers

- Commits must be signed off (`Signed-off-by:` trailer) **by the human**.
  Agents must never add a `Signed-off-by:` trailer on the human's behalf.
- Agents must include an `Assisted-by:` trailer identifying the agent
  and model.
- Order trailers as: `Assisted-by:` first, then the human's
  `Signed-off-by:` last (added by the human).

Format:

    Assisted-by: AGENT_NAME:MODEL_VERSION:[MODEL_VARIANT]

- `AGENT_NAME`: The AI tool (for example, `opencode`).
- `MODEL_VERSION`: The specific model version used.
- `MODEL_VARIANT`: The variant of the model version used (for example,
  `low`, `medium`, or `high`). Optional.

Other rules:

- Commit messages must be ASCII only.
- Keep PRs small and focused.
- Maintain a linear git history.

### Constraints

- Do __not__ add new dependencies beyond what is already in
  `pyproject.toml` without approval.
- Do __not__ install anything with `apt` or `snap`.
- Do __not__ run commands that require `sudo`.
- Do __not__ delete `oo001.md`; it is the design reference for the
  gherkinator YAML test plan format.
- Do __not__ edit production code (`src/pytest_gherkinator/`) without
  explicit user approval -- propose the change first and wait for
  approval.
- All errors must be handled explicitly in Python code.
