# Coding Standard

## Python

- Python 3.12+
- PEP8
- Type hints
- dataclass(slots=True)

## Architecture

- One responsibility per class
- No business logic in Runtime
- No business logic in Vision
- Dependency Injection preferred
- Repository pattern for data access

## Testing

- Every public service has tests
- Regression tests required
- Business cases preferred over synthetic examples

## Documentation

Every feature updates:

- CHANGELOG.md
- ROADMAP.md (if milestone changes)
- DECISIONS.md (if architecture changes)