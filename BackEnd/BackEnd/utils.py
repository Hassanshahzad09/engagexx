def assign_jobs_round_robin(sellers: list, jobs_to_assign: int, last_index: int):
    """
    Distributes `jobs_to_assign` jobs among `sellers` using round-robin.

    KEY FIX: jobs_to_assign CAN exceed len(sellers).
    If you have 1 seller and 200 jobs, that seller gets 200 job entries.
    The caller (assign_jobs_api) is responsible for deduplication IF needed,
    but for EngageX each job entry is a separate JobsHistory row so repeats = multiple jobs.

    Returns:
        assigned: list of seller IDs (may contain duplicates if jobs > sellers)
        new_last_index: updated round-robin pointer
    """
    n = len(sellers)

    if n == 0 or jobs_to_assign <= 0:
        return [], last_index

    assigned = []
    current_index = (last_index + 1) % n

    for _ in range(jobs_to_assign):
        assigned.append(sellers[current_index])
        current_index = (current_index + 1) % n

    new_last_index = (current_index - 1 + n) % n

    return assigned, new_last_index





import hashlib
import imagehash
from PIL import Image


HAMMING_THRESHOLD = 10


def get_sha256(file) -> str:
    """
    Exact duplicate detection.
    Same exact screenshot gives same SHA-256 hash.
    """
    file.seek(0)
    sha256 = hashlib.sha256()

    for chunk in file.chunks():
        sha256.update(chunk)

    file.seek(0)
    return sha256.hexdigest()


def get_phash(file) -> str:
    """
    Similar duplicate detection.
    Edited/resized/compressed image can still have close pHash.
    """
    file.seek(0)
    image = Image.open(file).convert("RGB")
    phash = str(imagehash.phash(image))
    file.seek(0)
    return phash


def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Lower value means images are more similar.
    """
    return imagehash.hex_to_hash(hash1) - imagehash.hex_to_hash(hash2)