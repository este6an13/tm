from sqlalchemy.orm import Session

from src.db.models import Base, Station


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
