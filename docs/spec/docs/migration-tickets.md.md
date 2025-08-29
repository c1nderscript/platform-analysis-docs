# docs/migration-tickets.md Spec

## File Overview
Tracks migration tasks mapping legacy docs to Rust or TypeScript targets.

## Public API Surface
Lists source documents, desired targets, and noted dependencies.

## Type & Trait/Class Map
N/A

## Control & Data Flow
Read-only reference guiding migration ticket creation.

## Dependencies
Depends on component documentation for source links and root contribution guides.

## Error Model
Stale paths or missing docs may misroute migrations.

## State & Concurrency
Static documentation; edited via git.

## Performance Notes
N/A

## Security Considerations
Ensure referenced repositories are trusted and access-controlled.

## Test Matrix
- Run `python validate_backlinks.py`.

## Maintenance Flags
Update tickets as components migrate.

## Backlinks
- [[../../AGENTS.md]]
- [[../../plan.md]]
- [[../../toaster.md]]
- [[../../README.md]]
- [[../CHANGELOG.md]]
- [[../README.md]]
- [[../migration-tickets.md]]
