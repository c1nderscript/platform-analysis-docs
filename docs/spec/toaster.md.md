# toaster.md Spec

## File Overview
Captures short-lived tasks and immediate action items.

## Public API Surface
N/A

## Type & Trait/Class Map
N/A

## Control & Data Flow
Used as a simple list; tasks are added and removed manually.

## Dependencies
Informed by `plan.md` and guided by `AGENTS.md` policies.

## Error Model
Stale entries may cause confusion about project status.

## State & Concurrency
Sequential edits through git.

## Performance Notes
Not applicable.

## Security Considerations
Do not log sensitive operational details.

## Test Matrix
- Manual cleanup review.

## Maintenance Flags
Ensure tasks are triaged or archived promptly.

## Backlinks
- [[../AGENTS.md]]
- [[../plan.md]]
- [[../README.md]]
- [[../CHANGELOG.md]]
