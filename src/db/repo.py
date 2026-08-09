from typing import Literal

from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from src.db.models import (
    COUNTS_UQ_COLS,
    STATION_UQ_COLS,
    Base,
    Counts,
    DateSamplingRun,
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

    def get_all(self):
        return self.db.query(self.model).all()

    def add(self, model):
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model


class StationRepo(BaseRepo):
    model = Station

    def create(self, station: Station) -> Station | None:
        if self.exists(code=station.code):
            warning(f"station with code {station.code} already exists")
            return
        return self.add(station)

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

    def create(self, counts: Counts) -> Counts:
        return self.add(counts)

    def update(self, IN: int | None, OUT: int | None, **filters):
        counts = self.get_by(**filters)
        if counts:
            if IN:
                counts.count_in = IN
            if OUT:
                counts.count_out = OUT
        self.db.commit()

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

    def bulk_upsert_in(self, counts: list[dict], batch_size: int = 800):
        if not counts:
            return
        for i in range(0, len(counts), batch_size):
            batch = counts[i : i + batch_size]
            self._bulk_upsert_batch(batch, "count_in")
        self.db.commit()

    def bulk_upsert_out(self, counts: list[dict], batch_size: int = 800):
        if not counts:
            return
        for i in range(0, len(counts), batch_size):
            batch = counts[i : i + batch_size]
            self._bulk_upsert_batch(batch, "count_out")
        self.db.commit()


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
