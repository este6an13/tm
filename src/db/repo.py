from typing import Literal

from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from src.db.models import (
    COUNTS_UQ_COLS,
    STATION_UQ_COLS,
    Base,
    Counts,
    DateSamplingRun,
    ProcessedFile,
    Station,
    StationSamplingRun,
)
from src.utils.logging import warning


class BaseRepo:
    model: type[Base]

    def __init__(self, db: Session):
        self.db = db

    def get_by(self, **filters):
        return self.db.query(self.model).filter_by(**filters).first()

    def exists(self, **filters):
        return self.get_by(**filters) is not None

    def get_all_by(self, **filters):
        return self.db.query(self.model).filter_by(**filters).all()

    def get_all(self):
        return self.db.query(self.model).all()

    def add(self, model):
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model


class StationRepo(BaseRepo):
    model = Station

    def get_by_codes(self, codes: list[int]) -> list[Station]:
        return self.db.query(self.model).filter(self.model.code.in_(codes)).all()

    def bulk_insert(self, stations: list[dict]) -> list[Station]:
        if not stations:
            return []

        # perform insert: handles uq constraint gracefully
        stmt = insert(self.model).values(stations)
        stmt = stmt.on_conflict_do_nothing(index_elements=STATION_UQ_COLS)
        self.db.execute(stmt)
        self.db.commit()

        # fetch inserted stations: lookup by codes
        codes = [s["code"] for s in stations]
        return self.get_by_codes(codes)


class CountsRepo(BaseRepo):
    model = Counts

    def _bulk_upsert_batch(
        self, batch: list[dict], col: str = Literal["count_in", "count_out"]
    ):
        # build insert statement for batch
        stmt = insert(self.model).values(batch)
        set_fields = {}
        # if conflict, overwrite with new value: upsert
        set_fields[col] = getattr(stmt.excluded, col)  # .count_in or .count_out
        # update if unique constraint conflict
        stmt = stmt.on_conflict_do_update(
            index_elements=COUNTS_UQ_COLS,
            set_=set_fields,
        )
        self.db.execute(stmt)

    def bulk_upsert(
        self,
        counts: list[dict],
        batch_size: int = 800,
        col: str = Literal["count_in", "count_out"],
    ):
        if not counts:
            return
        for i in range(0, len(counts), batch_size):
            batch = counts[i : i + batch_size]
            self._bulk_upsert_batch(batch, col)
        self.db.commit()

    def get_by(self, station_ids=None, time_min=400, time_max=2300, **filters):
        query = self.db.query(self.model)
        if station_ids is not None:
            query = query.filter(self.model.station_id.in_(station_ids))

        return (
            query.filter(
                self.model.time >= time_min,
                self.model.time <= time_max,
            )
            .filter_by(**filters)
            .all()
        )


class DateSamplingRunRepo(BaseRepo):
    model = DateSamplingRun

    def create(self, run: DateSamplingRun) -> DateSamplingRun:
        existing_run = self.get_by(
            start_date=run.start_date, end_date=run.end_date, seed=run.seed, n=run.n
        )
        if existing_run:
            params_str = f"start_date={run.start_date}, end_date={run.end_date}, seed={run.seed}, n={run.n}"
            warning(f"date sampling run with params {params_str} already exists")
            return existing_run
        return self.add(run)


class StationSamplingRunRepo(BaseRepo):
    model = StationSamplingRun

    def create(self, run: StationSamplingRun) -> StationSamplingRun:
        existing_run = self.get_by(
            nfiles=run.nfiles,
            nstations=run.nstations,
            seed=run.seed,
            sampled_files_hash=run.sampled_files_hash,
        )
        if existing_run:
            params_str = f"nfiles={run.nfiles}, nstations={run.nstations}, seed={run.seed}, sampled_files_hash={run.sampled_files_hash[:7]}"
            warning(f"station sampling run with params {params_str} already exists")
            return existing_run
        return self.add(run)


class ProcessedFileRepo(BaseRepo):
    model = ProcessedFile

    def is_processed(self, **filters):
        record = self.get_by(**filters)
        return bool(record and record.processed)

    def mark_processed(self, filename: str, process_type: str):
        record = self.get_by(filename=filename, process_type=process_type)
        if record:
            record.processed = True
        else:
            record = self.add(
                ProcessedFile(
                    processed=True,
                    filename=filename,
                    process_type=process_type,
                )
            )
        self.db.commit()
        self.db.refresh(record)
        return record
