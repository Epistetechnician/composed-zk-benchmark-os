# Issue Tracker: GitHub

State slice: `agent-skills-repository-routing-configuration`.

Issues and published PRDs for this repository live in GitHub Issues at
<https://github.com/Epistetechnician/composed-zk-benchmark-os/issues>.

## Conventions

- Create, read, label, comment on, and close issues with the authenticated
  `gh` CLI from this repository.
- Infer the repository from `origin`; do not duplicate repository coordinates
  in individual commands unless required to disambiguate.
- When an engineering skill says to publish to the issue tracker, create a
  GitHub issue.
- Preserve repository claim boundaries in every issue. An issue or PRD grants
  no execution, settlement, custody, evidence-promotion, or production
  authority by itself.
- Never place secrets, credentials, private artifact bodies, or operator-live
  outputs in an issue.

## Read Commands

Use `gh issue view <number> --comments` for one issue and `gh issue list` with
JSON output when filtering by state or label. Read operations do not authorize
issue mutation.
