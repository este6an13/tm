from typing import Literal

from sqlalchemy.orm import Session, insert

from src.db.models import COUNTS_UQ_COLS, Base, Counts, Station


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
    model: Station

    def create(self, station: Station) -> Station:
        if self.exists(code=station.code):
            raise ValueError(f"station with code {station.code} already exists")
        return self.add(station)


class CountsRepo(BaseRepo):
    model: Counts

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
