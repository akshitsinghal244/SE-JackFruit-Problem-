# Contributing

- **Branch:** `feature/RDCP1-<n>-<slug>` created from an up-to-date `main`.
- **Commit:** `RDCP1-<n> <message>` (one per sub-task, e.g. `RDCP1-18 US-10.2 scatter-gather`).
- **PR:** title `RDCP1-<n> <story title>`, filled-in template, raised by the **assignee**.
- **Review:** a repo owner who is not the author approves; CI must be green; squash-merge, delete the branch, then move the Jira card to Done.
- **Never** commit secrets, `.env`, `certs/`, datasets or trained models.
- Local checks before a PR: `cd gateway && ruff check . && pytest` | `cd client && npm run lint && npm run build` | `cd services && ruff check . && pytest` | `docker compose config -q`.
- Deviations from SRS/SAD/STP go into `docs/deviations.md` in the same PR.
