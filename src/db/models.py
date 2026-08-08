from datetime import date

from sqlalchemy import JSON, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


COUNTS_UQ_COLS = [
    "station_id",
    "year",
    "month",
    "day",
    "day_of_week",
    "time",
    "day_type",
    "window_minutes",
]


class Counts(Base):
    __tablename__ = "counts"

    # PK
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Time dimensions
    year: Mapped[int] = mapped_column()
    month: Mapped[int] = mapped_column()
    day: Mapped[int] = mapped_column()  # 1–31
    day_of_week: Mapped[int] = mapped_column()  # 0=Monday, 6=Sunday
    time: Mapped[int] = mapped_column()  # e.g., 400 → 04:00, 2300 → 23:00

    # Day type classification
    day_type: Mapped[str] = mapped_column(String(20))  # WD, SA, SU, HO

    # FK to station
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))

    # Aggregation window width, in minutes
    window_minutes: Mapped[int] = mapped_column()

    # Aggregated counts
    count_in: Mapped[int] = mapped_column()
    count_out: Mapped[int] = mapped_column()

    # Relationships
    station = relationship("Station", back_populates="counts")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            *COUNTS_UQ_COLS,
            name="uq_counts_station_time",
        ),
        Index("ix_counts_station_time", "station_id", "time"),
        Index("ix_counts_day_of_week", "day_of_week"),
    )


class Station(Base):
    __tablename__ = "stations"

    # PK
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Station information
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(255))

    # Relationships
    counts: Mapped[list["Counts"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )


class ProcessedFile(Base):
    __tablename__ = "processed_files"

    # PK
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # File details
    filename: Mapped[str] = mapped_column(String(100))  # "20251014"

    # Processing details
    process_type: Mapped[str] = mapped_column(String(50))
    processed: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (
        UniqueConstraint("filename", "process_type", name="uq_processed_file_type"),
    )


class DateSamplingRun(Base):
    __tablename__ = "date_sampling_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    start_date: Mapped[date] = mapped_column()
    end_date: Mapped[date] = mapped_column()
    n: Mapped[int] = mapped_column()
    seed: Mapped[int] = mapped_column()
    sampled_dates: Mapped[list[str]] = mapped_column(JSON)

    __table_args__ = (
        UniqueConstraint(
            "start_date",
            "end_date",
            "n",
            "seed",
            name="uq_date_sampling_run_params",
        ),
    )


class StationSamplingRun(Base):
    __tablename__ = "station_sampling_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    nfiles: Mapped[int] = mapped_column()
    nstations: Mapped[int] = mapped_column()
    seed: Mapped[int] = mapped_column()
    sampled_files: Mapped[list[str]] = mapped_column(JSON)
    sampled_files_hash: Mapped[str] = mapped_column(String(64))
    sampled_stations: Mapped[list[dict]] = mapped_column(JSON)

    __table_args__ = (
        UniqueConstraint(
            "nfiles",
            "nstations",
            "seed",
            "sampled_files_hash",
            name="uq_station_sampling_run_params",
        ),
    )
