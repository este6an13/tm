from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


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

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        nullable=True, onupdate=func.now()
    )

    # Relationships
    station = relationship("Station", back_populates="counts")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "station_id",
            "year",
            "month",
            "day",
            "day_of_week",
            "time",
            "day_type",
            "window_minutes",
            name="uq_counts_station_time",
        ),
        Index("ix_counts_station_time", "station_id", "time"),
        Index("ix_counts_day_of_week", "day_of_week"),
    )

    def __repr__(self):
        return (
            f"<Counts(id={self.id}, station_id={self.station_id}, "
            f"date={self.year}-{self.month:02d}-{self.day:02d}, time={self.time}, "
            f"day_type={self.day_type}, window_minutes={self.window_size}, "
            f"count_in={self.count_in}, count_out={self.count_out})>"
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

    def __repr__(self):
        return f"<Station(id={self.id}, code='{self.code}', name='{self.name}')>"
