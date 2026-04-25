def assign_jobs_round_robin(sellers, jobs_to_assign, last_index):
    n = len(sellers)

    if n == 0:
        return [], last_index

    assigned = []
    current_index = (last_index + 1) % n

    for _ in range(jobs_to_assign):
        assigned.append(sellers[current_index])
        current_index = (current_index + 1) % n

    new_last_index = (current_index - 1 + n) % n

    return assigned, new_last_index