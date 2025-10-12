# Contributing to toysoldiers_ai_0

Thank you for supporting the Toysoldiers Division. This guide outlines the
standard field workflow so contributions arrive synchronized with High Command
Doctrine.

## Table of Contents

1. [Project Scope](#project-scope)
2. [Prerequisites](#prerequisites)
3. [Repository Setup](#repository-setup)
4. [Daily Workflow](#daily-workflow)
5. [Validation Checklist](#validation-checklist)
6. [Exchange Protocol](#exchange-protocol)
7. [Support](#support)

## Project Scope

This repository houses frontline doctrine, tooling, and exchange automation for
the `toysoldiers_ai_0` theatre. Changes should emphasise operational clarity,
field safety, and morale support. When in doubt, align with the tone established
in `planning/` scrolls and the Code of Conduct.

## Prerequisites

- Python 3.11 or later
- Git 2.40 or later (with submodule support)
- Access to the `high_command_exchange` repository (mounted as `exchange/`)

Optional but helpful:

- Pre-commit tooling for lint/format checks
- Access to the companion `high_command_ai_0` repository for doctrine context

## Repository Setup

```pwsh
# Clone and initialise submodules
git clone https://github.com/Contingencyplana/toysoldiers_ai_0.git
cd toysoldiers_ai_0
git submodule update --init --recursive
```

## Daily Workflow

1. **Pull latest orders** – `git -C exchange pull` to sync pending directives.
2. **Read orders in sequence** – process them chronologically unless High
   Command flags an override.
3. **Implement directives** – update doctrine, tooling, or collateral as
   specified.
4. **Run the exchange receiver** – `py tools\exchange_receiver.py` targeting the
   order IDs you completed.
5. **Validate payloads** – `py tools\schema_validator.py <files>` to confirm the
   generated acknowledgements and reports.
6. **Commit and push** – capture both repository changes and submodule updates.

## Validation Checklist

Before requesting review or merging, confirm the following:

- [ ] Exchange acknowledgements and reports validate against published schemas
      (`py tools\schema_validator.py <path>`)
- [ ] Doctrine additions close with a Field Maxim when appropriate
- [ ] Markdown passes linting (one top-level heading, trailing newline)
- [ ] Scripts provide clear inline comments where logic is non-trivial
- [ ] Tests or manual verification notes accompany behavioural changes

## Exchange Protocol

- Never delete an order without moving it from `orders/pending/` to
  `orders/dispatched/` via the receiver.
- Reports belong in `exchange/reports/inbox/` until High Command archives them.
- Ledger files are authoritative; avoid manual edits unless an order explicitly
  instructs otherwise.
- Acknowledge every order—even if you must defer execution—so High Command can
  track awareness.

## Support

Have questions or need clarification?

- Open an issue tagged `question`
- Send a memo through `exchange/reports/inbox/`
- Email the maintainers at `ops@contingencyplana.dev`

May your rhythm stay steady and your reports stay clear.
