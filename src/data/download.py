from os import remove
from pathlib import Path
from shutil import move
from zipfile import ZipFile

from requests import get


def csv_filename(fdir, fname):
    return fdir / f"{fname}.csv"


def zip_filename(fdir, fname):
    return fdir / f"{fname}.zip"


def unzip_file(zip_path: Path, extract_to: Path) -> Path | None:
    with ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
    # return extracted CSV file path
    for file in Path(extract_to).glob("*.csv"):
        return file  # there should be only one
    return None


def extract_dir(zip_fname):
    return Path(str(zip_fname).replace(".zip", "_extracted"))


def move_file(src, dest):
    if src and src.exists():
        move(src, dest)


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
    URL = url.format(date_str=date_str)
    csv_fname = csv_filename(fdir=download_to, fname=date_str)
    if overwrite:
        remove_file(csv_fname)
    zip_fname = zip_filename(fdir=unzip_to, fname=date_str)
    success = download_file(URL, zip_fname)
    if not success:
        return
    extract_to = extract_dir(zip_fname)
    csv_path = unzip_file(zip_fname, extract_to)
    move_file(src=csv_path, dest=csv_fname)
    # TODO: drop columns
