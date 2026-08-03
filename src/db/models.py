from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Counts15Min(Base):
    pass


class Station(Base):
    __tablename__ = "stations"

    # PK
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Station information
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(255))

    # Relationships
    counts_15min: Mapped[list["Counts15Min"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Station(id={self.id}, code='{self.code}', name='{self.name}')>"
