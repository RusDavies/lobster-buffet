# Contributing

Lobster Buffet is early-stage, so small focused changes are easier to review
than broad rewrites.

Before opening a pull request:

- run the checks listed in `README.md`;
- keep private workspace facts out of fixtures, tests, docs, and examples;
- update schemas, manifests, fixtures, and wrapper tests together when changing
  operation contracts;
- keep wrapper code thin and delegated to the CLI core.

Public examples should use synthetic project names, synthetic channel IDs, and
redacted summaries.
