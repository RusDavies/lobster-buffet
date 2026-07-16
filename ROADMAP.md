# Roadmap

Lobster Buffet is still pre-alpha. The current priority is making the provider
surface useful without weakening the local/private adapter boundary.

## Near Term

- Promote the MCP wrapper from `skeleton` to `validated_skeleton` when the
  packageability gates and docs agree.
- Fix and harden the local project adapter against real clean/dirty Git states.
- Add a Python package manifest for the CLI core.
- Add CI that runs schema, CLI, wrapper, adapter-conformance, and secret-scan
  checks.
- Add at least one real-world local adapter example that uses only synthetic or
  explicitly public data.

## Later

- Define versioned release candidates for the CLI core and wrappers.
- Add generated wrapper input schemas from the operation schema catalog.
- Produce SBOM/provenance guidance for downstream packaging.
- Document adapter implementation patterns for non-Discord OpenClaw instances.
- Revisit the public package name before a stable release.
