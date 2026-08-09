from pathlib import Path

from pandas import read_csv

from src.data.utils import csv_filename, iso_to_date_str
from src.db.repo import DateSamplingRunRepo, StationRepo, StationSamplingRunRepo
from src.db.session import SessionLocal


def populate_check_ins(dsrun_id: int, ssrun_id: int, path: Path):
    db = SessionLocal()
    # init repos
    station_repo = StationRepo(db)
    ssrun_repo = StationSamplingRunRepo(db)
    dsrun_repo = DateSamplingRunRepo(db)

    # fetch station sampling results, and store the stations
    ssrun = ssrun_repo.get_by(id=ssrun_id)
    station_repo.bulk_insert(ssrun.sampled_stations)

    dsrun = dsrun_repo.get_by(id=dsrun_id)
    for dt_str in dsrun.sampled_dates:
        date_str = iso_to_date_str(dt_str)
        # df = read_csv(csv_filename(path, date_str))

    # iterate over dates (files)
    # skip if file processed: check sample dates, use files repo
    # load data from csv
    # aggregate counts
    # bulk upsert counts
    # mark file processed
