from pathlib import Path
from random import sample, seed

from src.utils.seeds import SEED_SAMPLING_STATIONS


# get list of files in path
def ls(path: Path):
    return [f for f in path.iterdir() if f.is_file()]


def sample_files(n, paths):
    files = []
    for path in paths:
        files.extend(ls(path))
    if n < len(files):
        return sample(files, k=n)
    return files  # all files


def sample_stations(nfiles, nstations, paths):
    seed(SEED_SAMPLING_STATIONS)
    # TODO: get sampled files, collect stations, sample stations
