from os import remove
from pathlib import Path
from shutil import move, rmtree
from zipfile import ZipFile

from requests import get

BASE_URL = "https://storage.googleapis.com/validaciones_tmsa/"
CHECK_INS_URL = BASE_URL + "ValidacionTroncal/validacionTroncal{date_str}.zip"
CHECK_OUTS_URL = BASE_URL + "Salidas/salidas{date_str}.zip"

CHECK_INS_PATH = Path("data/check_ins/daily")
CHECK_OUTS_PATH = Path("data/check_outs/daily")

UNZIP_CHECK_INS_DIR = Path("unzip/check_ins")
UNZIP_CHECK_OUTS_DIR = Path("unzip/check_outs")


def csv_filename(fdir, fname):
    return fdir / fname + ".csv"


def zip_filename(fdir, fname):
    return fdir / fname + ".zip"


def unzip_file(zip_path: Path, extract_to: Path) -> Path | None:
    extract_to.mkdir(exist_ok=True)
    with ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
    # return extracted CSV file path
    for file in Path(extract_to).glob("*.csv"):
        return file  # there should be only one
    return None


def extract_dir(zip_fname):
    return zip_fname.replace(".zip", "_extracted")


def move_file(src, dest):
    if src and src.exists():
        move(src, dest)


def cleanup(folders, files):
    for folder in folders:
        rmtree(folder)
    for file in files:
        remove(file)


def remove_file(path):
    if path.exists():
        remove(path)


def download_file(url: str, download_to: Path) -> bool:
    res = get(url, stream=True)
    if res.status_code == 200:
        with open(download_to, "wb") as f:
            f.writelines(res.iter_content(chunk_size=8192))
        return True
    else:
        return False


def get_file(
    date_str: str,
    url: str,
    download_to: Path,
    unzip_to: Path,
    overwrite=False,
):
    URL = url.format(date_str)
    csv_fname = csv_filename(fdir=download_to, fname=date_str)
    if overwrite:
        remove_file(csv_fname)
    zip_fname = zip_filename(fdir=unzip_to, fname=date_str)
    success = download_file(URL, download_to)
    if not success:
        return
    extract_to = extract_dir(zip_fname)
    csv_path = unzip_file(zip_fname, extract_to)
    move_file(src=str(csv_path), dest=csv_fname)
    # TODO: drop columns
    cleanup(folders=[extract_to], files=[zip_fname])


# get_file("20260730", CHECK_INS_URL, CHECK_INS_PATH, UNZIP_CHECK_INS_DIR)
