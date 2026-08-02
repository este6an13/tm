from datetime import date
from pathlib import Path

from src.data.download import get_files
from src.data.sampling.dates import sample_dates
from src.data.sampling.stations import sample_stations
from src.data.utils import cleanup

BASE_URL = "https://storage.googleapis.com/validaciones_tmsa/"
CHECK_INS_URL = BASE_URL + "ValidacionTroncal/validacionTroncal{date_str}.zip"
CHECK_OUTS_URL = BASE_URL + "Salidas/salidas{date_str}.zip"

CHECK_INS_PATH = Path("data/check_ins/daily")
CHECK_OUTS_PATH = Path("data/check_outs/daily")

TMP_UNZIP_PATH = Path("data/tmp_unzip")
TMP_UNZIP_CHECK_INS_PATH = TMP_UNZIP_PATH / "check_ins"
TMP_UNZIP_CHECK_OUTS_PATH = TMP_UNZIP_PATH / "check_outs"

CHECK_INS_COLUMNS = ["time", "station"]
CHECK_OUTS_COLUMNS = ["time", "station", "events"]

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
    set_up_workspace()
    dates = sample_dates(start_date=date(2026, 1, 1), end_date=date(2026, 1, 10), n=2)
    dates = dates[:1]  # just testing
    get_files(dates, *PARAMS["INS"])
    get_files(dates, *PARAMS["OUTS"])
    cleanup(folders=[TMP_UNZIP_PATH])
    stations = sample_stations(nfiles=2, nstations=4, paths=[CHECK_INS_PATH])
    print(stations)
    # [(7007, 'NQS - Calle 38A Sur'), (7505, 'LEON XIII'), (7201, 'Guatoque -Veraguas'), (4100, 'Carrera 77')]


if __name__ == "__main__":
    run()
