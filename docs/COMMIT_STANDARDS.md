# Commit Standards

Git and GitHub conventions for this project.

## Format

```
<type>(<scope>): <short description>
```

Subject line: lowercase, imperative mood, no period, max 72 characters.
Body (optional): explain *why*, not *what*. Separate from subject with a blank line.

## Types

| Type | When to use | Example |
|---|---|---|
| `feat` | New feature | `feat(sensors): implement CPU temperature reader` |
| `fix` | Bug fix | `fix(gpu): handle missing nvidia-smi gracefully` |
| `perf` | Performance improvement | `perf(sensors): shared cache for poll cycle` |
| `refactor` | Restructuring, no behavior change | `refactor(ui): extract theme watcher module` |
| `test` | Adding or updating tests | `test(cpu): add unit tests for core mapping` |
| `docs` | Documentation only | `docs: rewrite README with architecture section` |
| `style` | Formatting, whitespace | `style(ui): fix indentation in main_window.py` |
| `chore` | Config, deps, maintenance | `chore: add pytest to dev dependencies` |
| `WIP` | Blocked, moving on | `WIP(chart): blocked by pyqtgraph import error` |

## Scopes

- `sensors`, `cpu`, `gpu` — sensor layer
- `ui`, `window` — UI layer
- `config`, `utils`, `ipc` — utilities
- `deps` — dependencies

## Rules

- One logical change per commit
- Run tests before committing — never commit broken code
- Body explains *why* the change was made if not obvious from the subject
- If blocked 3 times on the same error: commit with `WIP:` prefix and document in Known Issues

## Examples

```
feat(sensors): implement CPU temperature reader

Use psutil as the primary source. Falls back to reading
/sys/class/thermal/thermal_zone*/temp when psutil returns empty.
```

```
fix(gpu): return None instead of crashing when nvidia-smi is not installed
```

```
perf(sensors): shared cache, slots, and compact log

Replace 4 TTL-based cache classes with a single refresh_caches()
called once per poll cycle. Poll cycle drops from 948ms to 0.47ms.
```
