# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Shiny chat app built on the [`commons`](https://github.com/michaelmayer2/commons) package: an LLM agent (Claude via AWS Bedrock, through `chatlas`) answers questions about a small clinical-trial dataset using SQL, trusted SAS measures, and agent-written SAS. SAS code runs on Altair SLC (via `slcPy`), not a SAS server.

## Commands

```bash
source .venv/bin/activate          # Python 3.13 venv
pip install -r requirements.txt    # commons and slcPy are pinned git commits
shiny run app.py                   # app.py exposes `app = commons.ui.app(agent)`
shiny run --reload app.py          # dev mode
```

There are no tests, linter, or build step in this repo. Running requires AWS Bedrock credentials (`AWS_*` env vars) and a licensed Altair SLC install (`WPSHOME` license env var).

## Architecture

`app.py` wires one dataset into three access paths that must stay consistent:

1. **SQL** — `data/visits.csv` is loaded into pandas and registered as `commons.data_source(visits=...)` under the `trial` source (queried via DuckDB inside commons).
2. **SAS library** — at import time `store_trial_library()` uses a short-lived `Slc()` session to write the *same* DataFrame to `TRIAL.VISITS` in `TRIAL_PATH`, a fresh `tempfile.mkdtemp(prefix="trial-")` directory per process (like R's `tempdir()`), removed at exit. This is a separate SLC process from the one the agent uses.
3. **SAS measures / run_sas** — `commons.slc_session()` (started lazily) runs both the trusted measures in `measures/` and agent-written `run_sas` code. The agent's `instructions` embed the actual path in its `libname` statement.

`app.py` exports the path as the `TRIAL_PATH` environment variable *before* the lazy SLC session starts; SLC inherits it, and `measures/trial.sas` assigns the library with `libname trial "%sysget(TRIAL_PATH)"`. New measure files must do the same rather than hardcode a path.

### SAS measure files (`measures/*.sas`)

`commons.sas_measures("measures", ...)` loads every `.sas` file in the directory. Each `/** ... */` block tagged `@measure <name>` becomes a callable measure; the code after the block (until the next block) is its body. Code before the first block (e.g. the `libname`) is prepended to every measure in that file. Supported tags: `@measure`, `@param [name=default] \`type\` description` (types: `string`, `integer`, `number`, `boolean`, `enum[...]`), `@return`, `@output` (the dataset the code must create, e.g. `WORK.RESULT`), `@provenance`. Params are bound as SAS macro variables (`&week`). Unknown tags or a missing `@output` dataset raise errors at load/run time.
