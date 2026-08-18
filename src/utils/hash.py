from hashlib import sha256
from json import dumps


def hash_params(params: dict) -> str:
    canonical = dumps(params, sort_keys=True)
    return canonical, sha256(canonical.encode()).hexdigest()
