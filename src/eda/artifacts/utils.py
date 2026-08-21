from src.db.models import Artifact
from src.db.repo import ArtifactRepo
from src.db.session import SessionLocal


def record_artifact(name: str, params_str: str, params_hash: str):

    ArtifactRepo(SessionLocal()).create(
        Artifact(name=name, params=params_str, params_hash=params_hash)
    )
