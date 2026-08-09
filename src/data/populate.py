from src.db.repo import StationRepo, StationSamplingRunRepo
from src.db.session import SessionLocal


def populate_check_ins(dsrun_id: int, ssrun_id: int):
    db = SessionLocal()
    # init repos
    station_repo = StationRepo(db)
    ssrun_repo = StationSamplingRunRepo(db)

    # fetch station sampling results, and store the stations
    ssrun = ssrun_repo.get_by(id=ssrun_id)
    station_repo.bulk_insert(ssrun.sampled_stations)

    # iterate over dates (files)
    # skip if file processed: check sample dates, use files repo
    # load data from csv
    # aggregate counts
    # bulk upsert counts
    # mark file processed
