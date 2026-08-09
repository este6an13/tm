from hashlib import sha256
from pathlib import Path
from random import sample, seed

from pandas import read_csv

from src.db.models import StationSamplingRun
from src.db.repo import StationSamplingRunRepo
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


def load_stations(files: Path) -> list[tuple[int, str]]:
    stations = []
    for file in files:
        df = read_csv(file, usecols=["station_code", "station_name"])
        stations_tuples = list(zip(df["station_code"], df["station_name"]))
        stations.extend(stations_tuples)
    return stations


# we deduplicate by code: the same station can change its name through time, but not its code
# we may end up with an old name for a station, that's a limitation we're gonna accept in this pipeline
def deduplicate_stations(stations: list[tuple[int, str]]) -> list[tuple[int, str]]:
    stations_map = {}
    for station in stations:
        # we don't care about replacing the name if it's different
        stations_map[station[0]] = station[1]  # 0: code, 1: name
    # back to the original format
    stations = [(code, name) for code, name in stations_map.items()]
    return stations


# nfiles doesn't need to be a large number, it's advised to use > 1, just in case there is a station
# not included in a file for some reason, so this is mostly for covering as much stations as possible
# paths doesn't need to cover both check-ins and check-outs, you could pick one, again this is mostly
# coverage; as nfiles increase we should converge to the real total population of stations
def _sample_stations(
    nfiles, nstations, paths
) -> tuple[list[Path], list[tuple[int, str]]]:
    seed(SEED_SAMPLING_STATIONS)
    files = sample_files(n=nfiles, paths=paths)
    stations = load_stations(files)
    stations = deduplicate_stations(stations)
    if nstations <= len(stations):
        stations = sample(stations, k=nstations)
    return files, stations  # return files just for reproducibility


def hash_file_list(files: list[str]) -> str:
    return sha256(",".join(files).encode()).hexdigest()


def sample_stations(db, nfiles, nstations, paths):
    # sampling
    files, stations = _sample_stations(nfiles, nstations, paths)
    files = sorted(files)  # required for hashing
    files = [str(f) for f in files]
    # persistence
    run = StationSamplingRunRepo(db).create(
        StationSamplingRun(
            nfiles=nfiles,
            nstations=nstations,
            seed=SEED_SAMPLING_STATIONS,
            sampled_files=files,
            sampled_files_hash=hash_file_list(files),
            sampled_stations=[{"code": code, "name": name} for code, name in stations],
            n_sampled=len(stations),
        )
    )
    return files, stations, run
