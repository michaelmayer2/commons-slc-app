# commons-slc-app

A chat app for asking questions about clinical-trial data. It pairs an LLM agent
(Claude on AWS Bedrock) with [commons](https://github.com/michaelmayer2/commons)
and [Altair SLC](https://altair.com/altair-slc), so answers can come from SQL,
from trusted SAS measures, or from SAS code the agent writes itself, all run
against the same data.

## How it works

- **Data**: `data/visits.csv` holds one row per subject per visit
  (`subject`, `arm`, `week`, `response`). At startup the app loads it for SQL
  queries and also writes it to the SAS library `TRIAL` as `TRIAL.VISITS`, in
  a fresh temporary directory (`/tmp/trial-XXXXXXXX`) for each app process that
  is removed when the process exits.
- **Measures**: `measures/trial.sas` defines trusted, reviewed SAS calculations
  the agent can call by name. For example, `arm_response` returns the mean
  response per treatment arm at a given visit week.
- **Agent**: `app.py` builds a `commons.Commons` agent backed by
  `chatlas.ChatBedrockAnthropic` and serves it as a Shiny chat UI.

## Requirements

- Python 3.13
- Altair SLC installed and licensed (the `WPSHOME` licence environment variable)
- AWS credentials with Bedrock access to `us.anthropic.claude-sonnet-5`

## Setup and running

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

shiny run app.py            # or: shiny run --reload app.py
```

Then open the URL Shiny prints (by default http://127.0.0.1:8000).

## Adding a SAS measure

Add a documented block to any `.sas` file in `measures/`:

```sas
/**
 * Short title
 *
 * What the measure computes.
 *
 * @measure my_measure
 * @param [week=12] `integer` Visit week.
 * @return What the output table contains.
 * @output WORK.RESULT
 */
proc ... data=trial.visits;
  where week = &week;
  ...
run;
```

Parameters become SAS macro variables (`&week`). The code must create the
dataset named in `@output`. Any code above the first block in a file, such as the
`libname` statement, runs before every measure in that file.

Because the library directory is random, measure files never hardcode it: they
assign it with `libname trial "%sysget(TRIAL_PATH)" access=readonly;`, reading
the `TRIAL_PATH` environment variable that `app.py` sets.
