from pathlib import Path


def file_exists(path: Path):
    return path.is_file()
