# docs/progress-dashboard.md Spec

## File Overview
Provides status tracking for feature migrations and parity checks.

## Public API Surface
Presents feature rows with source docs, targets, conversion state, and parity indicators.

## Type & Trait/Class Map
N/A

## Control & Data Flow
Manual updates reflect migration progress over time.

## Dependencies
Relies on component docs and migration tickets for accurate references.

## Error Model
Out-of-date entries may misrepresent progress.

## State & Concurrency
No runtime state; updated serially in git.

## Performance Notes
N/A

## Security Considerations
None.

## Test Matrix
- Run `python validate_backlinks.py`.

## Maintenance Flags
Expand with new features as migration scope grows.

## Backlinks
- [[../../AGENTS.md]]
- [[../../plan.md]]
- [[../../toaster.md]]
- [[../../README.md]]
- [[../CHANGELOG.md]]
- [[../README.md]]
- [[../progress-dashboard.md]]
