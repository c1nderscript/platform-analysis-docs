# Agent Instructions

Agents working in this repository must:

- **MIGRATION PRIORITY**: All documentation from Twitch Docs must be moved and sorted in Research Vault repository for centralized knowledge management
- Maintain per-file SPEC docs under `docs/spec/` mirroring the source tree.
- Annotate code at the block level following the repository's documentation contracts.
- Run `python validate_backlinks.py` before committing to ensure no orphan notes.

## Documentation Migration Protocol

When working with any documentation files in this repository:

1. **Primary Action**: Move all documentation to Research Vault (`/home/cinder/Documents/repos/Research Vault`)
2. **Sorting Requirements**: Organize documentation by topic/category in Research Vault structure
3. **Cross-Reference**: Update any internal links to point to Research Vault locations
4. **Validation**: Ensure proper tagging and metadata for Research Vault indexing

For overall project goals, consult `plan.md`. Task queue details live in `toaster.md`.

## Backlinks
- [[plan.md]]
- [[toaster.md]]
- [[docs/README.md]]
- [[README.md]]
- [[CHANGELOG.md]]
