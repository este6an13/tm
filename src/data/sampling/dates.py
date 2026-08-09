from collections import defaultdict
from datetime import timedelta
from random import sample, seed

from src.db.models import DateSamplingRun
from src.db.repo import DateSamplingRunRepo
from src.utils.day_types import get_day_type
from src.utils.seeds import SEED_SAMPLING_DATES


def generate_strata(start_date, end_date):
    # a stratum is a typle (year, month, day_type)
    strata = defaultdict(list)  # keys are strata, values are lists
    today = start_date
    while today <= end_date:
        day_type = get_day_type(today)
        strata[(today.year, today.month, day_type)].append(today)
        today += timedelta(days=1)
    return strata


def sample_stratum(strata, stratum, n):
    days = strata.get(stratum, [])
    if days:
        k = min(n, len(days))
        return sample(days, k=k)
    return []


def stratified_sampling(strata, n):
    sampled_dates = []
    # all (year, month, day_type) combinations : strata
    # g is the variable used for day type in this codebase
    ymg_combinations = sorted({(y, m, g) for (y, m, g) in strata})
    for year, month, day_type in ymg_combinations:
        samples = sample_stratum(strata, (year, month, day_type), n)
        sampled_dates.extend(samples)

    sampled_dates = sorted(set(sampled_dates))  # remove duplicates and sort
    return sampled_dates


# perform a stratified sampling, n is the number of elements required per stratum
def _sample_dates(start_date, end_date, n):
    seed(SEED_SAMPLING_DATES)
    strata = generate_strata(start_date, end_date)
    samples = stratified_sampling(strata, n)
    return samples


def sample_dates(db, start_date, end_date, n):
    # sampling
    dates = _sample_dates(start_date, end_date, n)
    # persistence
    run = DateSamplingRunRepo(db).create(
        DateSamplingRun(
            start_date=start_date,
            end_date=end_date,
            seed=SEED_SAMPLING_DATES,
            n=n,
            sampled_dates=sorted([str(dt) for dt in dates]),
            n_sampled=len(dates),
        )
    )
    return dates, run
