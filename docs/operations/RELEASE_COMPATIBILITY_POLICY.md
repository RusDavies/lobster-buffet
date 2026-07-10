# Release And Compatibility Policy

Status: Draft v0.1 Buffet-side policy.

## Purpose

This policy defines how Lobster Buffet versions and releases its provider
contracts so Lobster Portage can package or inspect them without owning Buffet
runtime behavior.

Buffet owns provider API, operation contracts, adapter capability contracts,
fixtures, validation, and wrapper compatibility metadata. Portage owns package,
install, doctor, rollback, and distribution mechanics.

## Version Surfaces

Buffet versions these surfaces separately:

- provider API: `lobster-buffet.provider.v0`
- local adapter API: `lobster-buffet.local-adapter.v0`
- operation contracts: `<operation-name>@<semver>`
- manifests and schemas: `<artifact>@<semver>`
- wrapper compatibility: wrapper package metadata plus provider API support

Draft `0.x` releases may change contracts, but every contract change must
update the affected schema, fixture, manifest reference, and validation path in
the same release candidate.

## Compatibility Classes

Compatible changes:

- adding a new optional input field with a safe default;
- adding a new operation in draft state;
- adding a new read-only adapter capability;
- expanding docs or fixtures without changing required output shape;
- adding wrapper support for an already schema-backed operation.

Potentially breaking changes:

- removing or renaming an operation, required field, error code, side effect, or
  adapter capability;
- changing an operation from read-only to mutating;
- changing approval requirements or local-only boundaries;
- embedding private/local data in shared artifacts;
- changing provider or adapter API names.

Breaking changes require a new incompatible contract version and a clear
migration note. In the v0.x draft series that may still be `0.y.0`, but the
manifest must make the compatibility boundary explicit.

## Release Gates

A Buffet release candidate is not packageable until:

1. Schema, manifest, fixture, and reference validation passes.
2. CLI-core regression checks pass.
3. Wrapper regression checks pass when wrapper paths are included.
4. Local-only boundary review confirms no private paths, channel IDs, secrets,
   tokens, personal memory, or customer data are present.
5. Mutating operations declare side effects, approval requirements, adapter
   capabilities, and fail-safe/preview expectations.
6. Handoff metadata identifies packageable artifacts and inspectable refs.

## Portage Handoff

Portage may inspect:

- release compatibility manifest;
- distribution handoff manifest;
- provider operation manifest;
- operation catalog;
- local adapter capability manifest;
- validation script and packageable artifact paths.

Portage should not infer local adapter configuration, private workspace state,
or release mechanics from Buffet. If Portage needs more metadata, Buffet should
add explicit handoff fields rather than relying on private conventions.

## Public Release Posture

`public_release_ready` remains false until the project has:

- a package/version tag plan;
- a privacy and security review;
- a documented changelog process;
- a rollback story owned by Portage or the downstream packager;
- a confirmed public package name.
