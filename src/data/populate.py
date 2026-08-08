from src.db.repo import CountsRepo, StationRepo
from src.db.session import SessionLocal


def populate_check_ins():
    db = SessionLocal()
    counts_repo = CountsRepo(db)
    station_repo = StationRepo(db)

    # create new stations: read sampling, and db to see new
    # iterate over dates (files)
    # skip if file processed: check sample dates, use files repo
    # load data from csv
    # aggregate counts
    # bulk upsert counts
    # mark file processed
