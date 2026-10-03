import atexit
import os
import shutil
import tempfile

import chatlas
import commons
import pandas as pd
from slc.slc import Slc

# The SLC library the measures in measures/trial.sas and the agent's run_sas
# code read the trial data from: a fresh directory per process, like R's
# tempdir(), removed at exit. SLC inherits the environment, so the measures
# find it with %sysget(TRIAL_PATH).
TRIAL_PATH = tempfile.mkdtemp(prefix="trial-")
os.environ["TRIAL_PATH"] = TRIAL_PATH
atexit.register(shutil.rmtree, TRIAL_PATH, ignore_errors=True)

visits = pd.read_csv("data/visits.csv")


def store_trial_library(visits: pd.DataFrame) -> None:
    """Write TRIAL.VISITS from the same rows the agent queries with SQL."""
    session = Slc()
    try:
        library = session.create_library("trial", TRIAL_PATH)
        library.create_dataset_from_dataframe("visits", visits)
    finally:
        session.shutdown()


store_trial_library(visits)

slc = commons.slc_session()

agent = commons.Commons(
    client=chatlas.ChatBedrockAnthropic(model="us.anthropic.claude-sonnet-5"),
    data_sources={"trial": commons.data_source(visits=visits)},
    semantic_layer=commons.semantic_layer(
        commons.sas_measures("measures", session=slc)
    ),
    sas=slc,
    instructions=(
        "The trial data is also in the SAS library TRIAL. In run_sas, assign it "
        f'with: libname trial "{TRIAL_PATH}" access=readonly;'
    ),
)

app = commons.ui.app(agent)
