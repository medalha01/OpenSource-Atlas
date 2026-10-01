# Contributing to OpenSource Atlas

Thanks for helping keep this atlas useful. The whole list is generated from a single
data file, so contributing is a small, structured edit — no Markdown table wrangling.

## TL;DR

1. **Fork** the repo and create a branch: `feat/add-<project>`.
2. **Edit [`data/projects.yaml`](data/projects.yaml)** — add or change one entry.
3. Run **`make build`** to regenerate `README.md`, then **`make check`** to run strict offline validation.
4. **Commit both** `data/projects.yaml` and `README.md`.
5. Open a **pull request** titled `Add <Project> to <Category>`.

> Never edit `README.md` by hand — it is a build artifact and will be overwritten.
> The single source of truth is `data/projects.yaml`.

## The data format

Each project is one YAML entry:

```yaml
- name: Ollama
  url: https://github.com/ollama/ollama
  desc: Run Llama 3, Mistral, Gemma, and more locally in seconds
  cat: AI, Machine Learning & LLMs
  sub: LLM Chat Interfaces & Local Runtimes
```

| Field | Required | Rules |
|-------|:---:|-------|
| `name` | ✅ | Display name. Must be unique across the list. |
| `url` | ✅ | Primary repository URL, must start with `https://`. Prefer the canonical repo (GitHub, GitLab, Codeberg, or the project's own forge). |
| `desc` | ✅ | One concise line. Say **what it does**, not "A tool that…". No trailing period. Aim for ≤ 100 characters. |
| `cat` | ✅ | Must exactly match a category defined in [`tools/generate.py`](tools/generate.py). |
| `sub` | ✅ | Must exactly match a subcategory within that category. |
| `alt` | ➖ | List of mirror / additional repository URLs. |
| `status` | ➖ | List of flags: `inactive`, `archived`, `beta`, or `deprecated`. |

Example with the optional fields:

```yaml
- name: RethinkDB
  url: https://github.com/rethinkdb/rethinkdb
  desc: Distributed document database built for real-time applications
  cat: Databases
  sub: Document & NoSQL Databases
  status: [inactive]
```

## Inclusion criteria

To keep the list curated rather than exhaustive, a project should be:

- **Open source** — a recognised OSI-approved or free-software license. Source-available
  licenses (BSL, SSPL, fair-code, etc.) are generally **out of scope**; if you believe an
  exception is warranted, say so in the PR.
- **Notable and maintained** — real-world usage and a community behind it. Brand-new or
  single-author hobby repositories are usually declined. Archived-but-historically-important
  projects are welcome **with** a `status: [archived]` flag.
- **Correctly placed** — in the most specific subcategory that fits. If nothing fits, propose
  a new subcategory in your PR (see below).

## Adding a category or subcategory

Categories and subcategories live in the `TAXONOMY` list in
[`tools/generate.py`](tools/generate.py). To add one, edit that list (keep the existing
ordering style) and then add your project(s) referencing the new `cat`/`sub`. Run
`make build && make check` and include the regenerated `README.md`.

## Acceptance checklist

Before opening your PR, confirm:

- [ ] The project is open source and actively maintained (or flagged if not).
- [ ] `url` is the canonical repository and resolves (no redirect to a renamed repo).
- [ ] `cat` and `sub` are spelled exactly as in the taxonomy.
- [ ] The entry is alphabetically ordered within its subcategory.
- [ ] `make build` was run and `README.md` is committed alongside the data change.
- [ ] `make check` passes with no new errors.

## Reporting a problem

- **Dead or moved link?** Open a [broken-link issue](../../issues/new?template=broken-link.yml).
- **Wrong category, description, or status?** Open a regular issue or send a PR.

A scheduled GitHub Actions workflow performs the external link sweep; `make check` intentionally stays deterministic and offline. The community still catches moved or stale projects first — thank you. 💛


## Security reports

Security issues in the atlas tooling or repository automation should follow [SECURITY.md](SECURITY.md). Vulnerabilities in a listed third-party project belong upstream with that project.
