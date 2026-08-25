from datetime import date
from pathlib import Path

from src.data.download import get_files
from src.data.populate import populate_counts
from src.data.sampling.dates import sample_dates
from src.data.sampling.stations import sample_stations
from src.data.utils import cleanup
from src.db.session import SessionLocal

BASE_URL = "https://storage.googleapis.com/validaciones_tmsa/"
CHECK_INS_URL = BASE_URL + "ValidacionTroncal/validacionTroncal{date_str}.zip"
CHECK_OUTS_URL = BASE_URL + "Salidas/salidas{date_str}.zip"

CHECK_INS_PATH = Path("data/check_ins/daily")
CHECK_OUTS_PATH = Path("data/check_outs/daily")

TMP_UNZIP_PATH = Path("data/tmp_unzip")
TMP_UNZIP_CHECK_INS_PATH = TMP_UNZIP_PATH / "check_ins"
TMP_UNZIP_CHECK_OUTS_PATH = TMP_UNZIP_PATH / "check_outs"

CHECK_INS_COLUMNS = ["time", "station_code", "station_name"]
CHECK_OUTS_COLUMNS = ["time", "station_code", "station_name", "events"]

PARAMS = {
    "INS": [CHECK_INS_URL, CHECK_INS_PATH, TMP_UNZIP_CHECK_INS_PATH, CHECK_INS_COLUMNS],
    "OUTS": [
        CHECK_OUTS_URL,
        CHECK_OUTS_PATH,
        TMP_UNZIP_CHECK_OUTS_PATH,
        CHECK_OUTS_COLUMNS,
    ],
}


def set_up_workspace():
    CHECK_INS_PATH.mkdir(parents=True, exist_ok=True)
    CHECK_OUTS_PATH.mkdir(parents=True, exist_ok=True)
    TMP_UNZIP_CHECK_INS_PATH.mkdir(parents=True, exist_ok=True)
    TMP_UNZIP_CHECK_OUTS_PATH.mkdir(parents=True, exist_ok=True)


def run():

    # the actual pipeline params that should be configurable
    START_DATE = date(2025, 1, 1)
    END_DATE = date(2025, 12, 31)
    STRATUM_SIZE = 12
    N_FILES = 4
    N_STATIONS = 30
    TIME_MIN = 400
    TIME_MAX = 2300
    WINDOW_MINUTES = 15

    db = SessionLocal()
    set_up_workspace()
    dates, dsrun = sample_dates(
        db,
        start_date=START_DATE,
        end_date=END_DATE,
        n=STRATUM_SIZE,  # 1 year, 3 samples per month is 36 dates per day type
    )
    print(dates)
    # if you stop execution amid download, you may end up with unprocessed files
    # and that breaks execution downwards
    # you can manually remove those files and start the script again
    # note: data is not available for 20250530 for some reason
    get_files(dates, *PARAMS["INS"])
    get_files(dates, *PARAMS["OUTS"])
    cleanup(folders=[TMP_UNZIP_PATH])
    files, stations, ssrun = sample_stations(
        db, nfiles=N_FILES, nstations=N_STATIONS, paths=[CHECK_INS_PATH]
    )
    print(files)
    print(stations)

    populate_counts(
        dsrun.id, ssrun.id, CHECK_INS_PATH, "INS", WINDOW_MINUTES, TIME_MIN, TIME_MAX
    )
    populate_counts(
        dsrun.id, ssrun.id, CHECK_OUTS_PATH, "OUTS", WINDOW_MINUTES, TIME_MIN, TIME_MAX
    )


if __name__ == "__main__":
    run()
