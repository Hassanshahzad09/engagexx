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