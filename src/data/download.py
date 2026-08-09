from datetime import date
from pathlib import Path
from shutil import move
from zipfile import ZipFile

from pandas import read_csv, Series, DataFrame
from requests import get

from src.data.files import file_exists
from src.data.utils import csv_filename, get_date_str
from src.utils.logging import warning


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


def download_file(url: str, download_to: Path) -> bool:
    res = get(url, stream=True)
    if res.status_code == 200:
        with open(download_to, "wb") as f:
            f.writelines(res.iter_content(chunk_size=8192))
        return True
    else:
        return False


# drop unused columns, saves disk space
def drop_columns(df, columns_to_keep: list[str]):
    df = df[columns_to_keep]
    return df


def parse_station(station_str: str) -> tuple[int, str] | None:
    if station_str and "(" in station_str and ")" in station_str:
        code = int(station_str.split(")")[0].replace("(", "").strip())
        name = station_str.split(")")[1].strip()
        return (code, name)


def parse_stations(stations: Series) -> Series:
    return stations.apply(parse_station)


# make sure check-ins and check-outs files use the same terminology for easier renaming later
# we bring check-outs file to use the same convention as check-ins
def standardize_columns(df):
    if "Tiempo" in df.columns:  # check-outs files have this column
        # "Fecha_Transaccion" and "Tiempo" are concatenated to follow check-ins convention
        df["Fecha_Transaccion"] = df["Fecha_Transaccion"] + " " + df["Tiempo"]
        df = df.rename(columns={"Estacion": "Estacion_Parada"})
        df = df.rename(
            columns={"Salidas_S": "events"}
        )  # this column is only in check-outs files, we rename it right away
    return df


def split_station_column(df):
    # split estacion into two separate columns for easier processing downstream in the pipeline
    stations = parse_stations(df["Estacion_Parada"])
    df[["station_code", "station_name"]] = DataFrame(stations.tolist(), index=df.index)
    return df


def rename_columns(df):
    df = df.rename(columns={"Fecha_Transaccion": "time", "Estacion_Parada": "station"})
    return df


def post_processing(csv_fname, columns_to_keep):
    df = read_csv(csv_fname)
    df = standardize_columns(df)  # use same convention in both files
    df = split_station_column(df)  # split station column in code, name
    df = rename_columns(df)  # rename columns for consistency with the codebase
    df = drop_columns(df, columns_to_keep)  # drop unused columns
    df.to_csv(csv_fname)


def get_file(
    date_str: str,
    url: str,
    download_to: Path,
    unzip_to: Path,
    columns: list[str],
    redownload=False,
):
    URL = url.format(date_str=date_str)
    csv_fname = csv_filename(fdir=download_to, fname=date_str)
    if not redownload and file_exists(csv_fname):
        warning(f"file {csv_fname} already exists, skipping download")
        return
    zip_fname = zip_filename(fdir=unzip_to, fname=date_str)
    success = download_file(URL, zip_fname)
    if not success:
        return
    extract_to = extract_dir(zip_fname)
    csv_path = unzip_file(zip_fname, extract_to)
    move_file(src=csv_path, dest=csv_fname)
    post_processing(csv_fname, columns)


def get_files(
    dates: list[date],
    url: str,
    download_to: Path,
    unzip_to: Path,
    columns: list[str],
    redownload=False,
):
    for dt in dates:
        date_str = get_date_str(dt)
        get_file(date_str, url, download_to, unzip_to, columns, redownload)
