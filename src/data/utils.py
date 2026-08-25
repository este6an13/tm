from datetime import date
from os import remove
from shutil import rmtree

from src.utils.logging import success


def cleanup(folders=None, files=None):
    if folders is not None:
        for folder in folders:
            rmtree(folder)
    if files is not None:
        for file in files:
            remove(file)
    success("🧹 cleaned up temporary folders and files")


def get_date_str(dt: date):
    return f"{dt.year}{dt.month:02d}{dt.day:02d}"


def iso_to_date_str(dt_str: str):  # "YYYY-MM-DD" string
    return dt_str.replace("-", "")


def csv_filename(fdir, fname):
    return fdir / f"{fname}.csv"
