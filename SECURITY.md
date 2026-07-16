# Security Policy

## Supported Versions

Lobster Buffet is pre-alpha. Security issues are accepted for the current
default branch only.

## Reporting A Vulnerability

Please report vulnerabilities privately through GitHub security advisories when
available, or by contacting the repository owner.

Do not include real secrets, private workspace data, customer data, or live
OpenClaw runtime exports in public issues.

## Boundary Expectations

Shared provider artifacts must not embed private adapter configuration,
Discord channel maps, secrets, local absolute paths, personal memory, or
credentials. Runtime deployments should keep those facts in local adapter
configuration and secret stores.
