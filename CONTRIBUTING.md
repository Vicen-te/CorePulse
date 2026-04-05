# Contributing

Thanks for your interest in ThermalCore.

## How to contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes following [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md)
4. Run tests: `make test`
5. Commit following [docs/COMMIT_STANDARDS.md](docs/COMMIT_STANDARDS.md)
6. Open a Pull Request against `main`

## Rules

- All PRs must pass CI (unit tests) before merge
- One logical change per PR
- Add tests for new features
- Don't break existing sensors or the polling cache
- Run `make benchmark` if you change the sensor or cache layer — poll cycle must stay under 5ms

## Branch naming

- `feat/description` — new feature
- `fix/description` — bug fix
- `perf/description` — performance improvement
- `docs/description` — documentation only

## Questions?

Open an issue on GitHub.
