from datetime import date
from pathlib import Path

from src.data.download import get_files
from src.data.sampling import sample_dates
from src.data.utils import cleanup

BASE_URL = "https://storage.googleapis.com/validaciones_tmsa/"
CHECK_INS_URL = BASE_URL + "ValidacionTroncal/validacionTroncal{date_str}.zip"
CHECK_OUTS_URL = BASE_URL + "Salidas/salidas{date_str}.zip"

CHECK_INS_PATH = Path("data/check_ins/daily")
CHECK_OUTS_PATH = Path("data/check_outs/daily")

TMP_UNZIP_PATH = Path("data/tmp_unzip")
TMP_UNZIP_CHECK_INS_PATH = TMP_UNZIP_PATH / "check_ins"
TMP_UNZIP_CHECK_OUTS_PATH = TMP_UNZIP_PATH / "check_outs"

CHECK_INS_COLUMNS = ["Fecha_Transaccion", "Estacion_Parada"]
CHECK_OUTS_COLUMNS = ["Fecha_Transaccion", "Tiempo", "Estacion", "Salidas_S"]

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
    cleanup(folders=[TMP_UNZIP_PATH])


if __name__ == "__main__":
    run()
