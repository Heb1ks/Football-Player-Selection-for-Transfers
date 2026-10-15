# TransferLens

**Development of an Intelligent System for Football Player Selection for Transfers Using Machine Learning**

A working early diploma prototype for historical football recruitment analysis. Define a recruitment brief, inspect player forecasts and their dated inputs, save candidates for comparison, explore a destination's prior formation context, and export CSV results.

Review package: [draft pull request #12](https://github.com/Heb1ks/Football-Player-Selection-for-Transfers/pull/12). The implementation is on `codex/DIP-01-predefense-mvp`; merge only after actual team review. No submission tag has been created.

![Recruitment interface](docs/screenshots/discovery.jpg)

## Problem and intended users

Scouts and analysts need to shortlist candidates and inspect the assumptions behind predictions. This project studies whether destination formation history adds predictive value beyond prior individual statistics. It supports human review; it does not automatically decide real transfers.

## Team and supervision

| Member | Account | Proposed responsibility |
| --- | --- | --- |
| Rymbaev Eskender | [Heb1ks](https://github.com/Heb1ks) | Application, integration, repository, demo |
| Diar Gizatov | [diar06kz](https://github.com/diar06kz) | Data checks, literature, evaluation, report review |

Supervisor: **Kozhakhmet Zhaksylyk**. Responsibility allocation is a proposal pending team confirmation. The initial code/document package was prepared with AI assistance; it does not establish individual contributions by both students. Record genuine personal changes and peer reviews under separate accounts.

## Current status and scope

Version 0.1, prepared 15 October 2026. Local working prototype and initial approbation report; user discussions and supervisor feedback remain pending. The original RMT experiment was reused and reproduced, with provenance preserved in [research/rmt/reuse_manifest.json](research/rmt/reuse_manifest.json). The diploma adds a web interface, inference API, application checks, diagrams and submission materials.

The dataset contains **781 real historical transfers**, including **242 held-out candidates from 2023–2024**. It covers adult outfield players changing clubs between the five major European domestic leagues under explicit coverage/minutes thresholds. It is not a live 2026 market feed. No financial optimisation, medical screening, contracts, video or complete tactical-fit model is implemented.

## Start locally

Python 3.12 and an internet connection for the first dependency installation are required. From this repository in PowerShell:

```powershell
./start.ps1
```

Open **http://127.0.0.1:8765**. If local PowerShell policy prevents scripts, use the commands below directly rather than changing a system policy:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe app/server.py
```

The committed cohort and trusted saved models support inference without downloading raw inputs. Do not load arbitrary joblib files. The server binds loopback, has read-only routes and is designed for a local demonstration. It has no account system or production hosting configuration. Stop with Ctrl+C.

## Research result

Train: 405 transfers from 2018–2021. Validation: 134 from 2022. Test: 242 from 2023–2024. Players do not overlap. Target: goals plus assists per 90 minutes in the first destination season, conditional on at least 450 observed minutes.

| Comparator | Test MAE | Test RMSE |
| --- | --- | --- |
| Training mean | 0.21925 | 0.28589 |
| Persistence from prior GA90 | 0.14729 | 0.20683 |
| Individual Random Forest | 0.14670 | 0.20656 |
| RF plus formation context | 0.14879 | 0.20778 |

Adding nominal formations did **not** improve test performance. Individual RF is practically tied with persistence. The prototype must not be presented as a model with proven recruitment benefit. Destination changes are associative scenarios, not causal predictions. GA90 does not measure defensive quality; later profile position and minutes-based cohort selection remain limitations.

## Checks and reproducibility

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Eleven automated tests passed locally, including a second run in an independent project virtual environment without RMT libraries. The complete resolved versions are in [requirements-lock.txt](requirements-lock.txt). See [test results](output/test-results.txt), [browser walkthrough](docs/browser-checks.md), and [latency measurement](output/latency.json). CI runs the same suite; remote CI status must be checked separately.

To rebuild training outputs from the exact original data:

```powershell
.venv/Scripts/python.exe tools/download_data.py
.venv/Scripts/python.exe tools/rebuild_models.py
```

The downloader verifies retained hashes and refuses a changed upstream snapshot. Full raw inputs are retained in the local submission archive but omitted from Git to avoid a large duplicate dataset. A publisher update or unavailable URL may require restoring that retained snapshot. Rebuilding models uses the original full-precision pipeline: a CSV roundtrip can change tree thresholds slightly. Both original test metrics are checked to tolerance 1e-10. Source attribution: [dcaribou/transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets), publisher repository CC0-1.0. Retrieval date 12 October 2026 is not a live-data freshness claim.

## Documentation and project tracking

- [Single approbation report PDF](output/pdf/TransferLens_PreDefense_Report.pdf) and [editable report](docs/report.md)
- [Board and task screenshot PDF](output/pdf/TransferLens_Task_Board_Evidence.pdf)
- [Shared GitHub Issues](https://github.com/Heb1ks/Football-Player-Selection-for-Transfers/issues), [task definitions](docs/tasks.json), and local board at `/board`
- [Context, use-case and component diagrams](diagrams/), editable Mermaid/PlantUML plus SVG/PNG
- [Five-minute demo in Russian](docs/demo-script-ru.md)
- [Submission checklist and form field draft](docs/submission-checklist-ru.md)
- [Interview guide](docs/interview-guide.md) and [supervisor feedback log](docs/supervisor-feedback.md)

The report contains the proposal, data-based relevance evidence, 13 used sources including 8 scientific publications, 4-system/8-criterion comparison, technology alternatives, requirements, architecture, prototype, evaluation, management/risks and an explicitly pending supervisor-feedback section.

## Repository layout

```text
app/                 Local HTTP API and browser UI
data/                Derived named cohort and measured results
models/              Trusted model pipelines and hash manifest
research/rmt/        Reused source, original outputs and provenance
docs/                Report source, tasks, evidence and team records
diagrams/            Editable sources and readable exports
tests/               Core and HTTP verification
tools/               Reproduction, documentation and packaging scripts
output/pdf/          Two separate form deliverables
.github/workflows/   Automated checks
```

Selected technologies: Python, pandas, NumPy, scikit-learn Random Forest, HTTP JSON/CSV, buildless HTML/CSS/JavaScript and browser localStorage. Detailed decisions and alternatives are in report section 5.

## Before 24 October 2026 at 18:00

Conduct 3–5 genuine user discussions or obtain a qualifying client agreement, get substantive supervisor feedback, confirm owners, record each member's real contribution and peer review, verify committee access and regenerate both PDFs. Tag the exact reviewed submission as `pre-defense-1` only then. A complete application is not required for this stage, but fabricated evidence or a last-minute package cannot substitute for actual progressive contributions and review.
