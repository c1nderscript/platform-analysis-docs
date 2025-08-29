<!-- 2025-08-29: Added high-priority rule per new directive (see task xyz). -->
# Agent Instructions

<rule>
<document_type>RULE</document_type>
<document_id>f6b6c227321c4501bd9851</document_id>
<rule_content>
All documentation in the Twitch Docs repo must be moved and sorted in the Research Vault repository.
</rule_content>
</rule>

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
