# AGENTS.md Spec

## File Overview
Provides operational guidelines for contributors and automated agents.

## Public API Surface
Defines expected workflows and required checks.

## Type & Trait/Class Map
N/A

## Control & Data Flow
Information-only; no runtime behavior.

## Dependencies
References `plan.md`, `toaster.md`, and `validate_backlinks.py`.

## Error Model
Misinterpretation leads to policy violations.

## State & Concurrency
Edited manually; no concurrent access concerns.

## Performance Notes
None.

## Security Considerations
Ensure instructions do not expose sensitive data.

## Test Matrix
- Run `python validate_backlinks.py` to confirm link integrity.

## Maintenance Flags
Keep instructions aligned with project practices.

## Backlinks
- [[../plan.md]]
- [[../toaster.md]]
- [[../README.md]]
- [[../CHANGELOG.md]]
