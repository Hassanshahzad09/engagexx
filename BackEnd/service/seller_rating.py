import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from django.conf import settings


EXPECTED_TIME_HOURS = Decimal("4.00")
DEFAULT_TRUST_SCORE = Decimal("50.00")
DATASET_PATH = Path(settings.BASE_DIR) / "seller_rating_dataset.csv"


def clamp_decimal(value, minimum=Decimal("0.00"), maximum=Decimal("100.00")):
    value = Decimal(str(value))
    return max(minimum, min(maximum, value))


def safe_ratio(numerator, denominator, default=Decimal("0.00")):
    numerator = Decimal(str(numerator or 0))
    denominator = Decimal(str(denominator or 0))
    if denominator <= 0:
        return default
    return numerator / denominator


def round_decimal(value, places="0.01"):
    return Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def score_to_rating(final_reputation_score):
    score = Decimal(str(final_reputation_score))
    if score >= 85:
        return 5
    if score >= 70:
        return 4
    if score >= 55:
        return 3
    if score >= 40:
        return 2
    return 1


def calculate_rating_from_metrics(metrics):
    assigned_tasks = Decimal(str(metrics.get("AssignedTasks", 0) or 0))
    completed_tasks = Decimal(str(metrics.get("CompletedTasks", 0) or 0))
    approved_tasks = Decimal(str(metrics.get("ApprovedTasks", 0) or 0))
    submitted_proofs = Decimal(str(metrics.get("SubmittedProofs", 0) or 0))
    avg_completion_time = Decimal(str(metrics.get("AvgCompletionTime", 0) or 0))
    trust_score = clamp_decimal(metrics.get("TrustScore", DEFAULT_TRUST_SCORE))

    proof_validity_rate = metrics.get("ProofValidityRate")
    audit_retention_rate = metrics.get("AuditRetentionRate")

    success_rate = safe_ratio(approved_tasks, completed_tasks)
    completion_ratio = safe_ratio(completed_tasks, assigned_tasks)

    if proof_validity_rate is None:
        proof_validity_rate = safe_ratio(submitted_proofs, completed_tasks)
    proof_validity_rate = clamp_decimal(proof_validity_rate, Decimal("0.00"), Decimal("1.00"))

    if audit_retention_rate is None:
        audit_retention_rate = Decimal("1.00") if completed_tasks > 0 else Decimal("0.60")
    audit_retention_rate = clamp_decimal(audit_retention_rate, Decimal("0.00"), Decimal("1.00"))

    if avg_completion_time <= 0:
        speed_score = Decimal("0.00")
    else:
        speed_score = EXPECTED_TIME_HOURS / avg_completion_time
    speed_score = clamp_decimal(speed_score, Decimal("0.00"), Decimal("1.00"))

    performance_score = Decimal("100.00") * (
        Decimal("0.30") * success_rate
        + Decimal("0.20") * completion_ratio
        + Decimal("0.15") * proof_validity_rate
        + Decimal("0.15") * speed_score
        + Decimal("0.20") * audit_retention_rate
    )

    final_reputation_score = (
        Decimal("0.70") * performance_score
        + Decimal("0.30") * trust_score
    )
    final_reputation_score = clamp_decimal(final_reputation_score)
    rating = score_to_rating(final_reputation_score)

    return {
        "assigned_tasks": int(assigned_tasks),
        "completed_tasks": int(completed_tasks),
        "approved_tasks": int(approved_tasks),
        "rejected_tasks": int(Decimal(str(metrics.get("RejectedTasks", 0) or 0))),
        "submitted_proofs": int(submitted_proofs),
        "valid_proofs": int(Decimal(str(metrics.get("ValidProofs", 0) or 0))),
        "invalid_proofs": int(Decimal(str(metrics.get("InvalidProofs", 0) or 0))),
        "audit_checked_tasks": int(Decimal(str(metrics.get("AuditCheckedTasks", 0) or 0))),
        "audit_passed_tasks": int(Decimal(str(metrics.get("AuditPassedTasks", 0) or 0))),
        "audit_failed_tasks": int(Decimal(str(metrics.get("AuditFailedTasks", 0) or 0))),
        "avg_completion_time": float(round_decimal(avg_completion_time)),
        "trust_score": float(round_decimal(trust_score)),
        "success_rate": float(round_decimal(success_rate, "0.0001")),
        "completion_ratio": float(round_decimal(completion_ratio, "0.0001")),
        "proof_validity_rate": float(round_decimal(proof_validity_rate, "0.0001")),
        "speed_score": float(round_decimal(speed_score, "0.0001")),
        "audit_retention_rate": float(round_decimal(audit_retention_rate, "0.0001")),
        "performance_score": float(round_decimal(performance_score)),
        "final_reputation_score": float(round_decimal(final_reputation_score)),
        "rating": rating,
        "rating_label": f"{rating} Star",
    }


def calculate_trust_score(
    completed_tasks,
    rejected_tasks,
    valid_proofs,
    invalid_proofs,
    audit_passed_tasks,
    audit_failed_tasks,
    unethical_reports,
):
    trust_score = DEFAULT_TRUST_SCORE
    trust_score += Decimal(str(completed_tasks or 0)) * Decimal("3.00")
    trust_score += Decimal(str(valid_proofs or 0)) * Decimal("2.00")
    trust_score += Decimal(str(audit_passed_tasks or 0)) * Decimal("5.00")
    trust_score -= Decimal(str(rejected_tasks or 0)) * Decimal("5.00")
    trust_score -= Decimal(str(invalid_proofs or 0)) * Decimal("15.00")
    trust_score -= Decimal(str(audit_failed_tasks or 0)) * Decimal("25.00")
    trust_score -= Decimal(str(unethical_reports or 0)) * Decimal("8.00")
    return clamp_decimal(trust_score)


def build_seller_metrics_from_history(seller_profile):
    jobs = seller_profile.jobs.all()
    assigned_tasks = jobs.count()
    completed_jobs = jobs.filter(status="completed")
    rejected_jobs = jobs.filter(status="rejected")
    completed_tasks = completed_jobs.count()
    valid_proofs = completed_jobs.filter(proofStatus="valid").count()
    invalid_proofs = jobs.filter(proofStatus="invalid").count()
    rejected_tasks = rejected_jobs.count() + invalid_proofs
    approved_tasks = valid_proofs if completed_tasks else 0

    submitted_proofs = completed_jobs.exclude(proofUrl="").count()
    audit_passed_tasks = jobs.filter(auditStatus="passed").count()
    audit_failed_tasks = jobs.filter(auditStatus="failed").count()
    audit_checked_tasks = audit_passed_tasks + audit_failed_tasks

    completion_times = [
        Decimal(str(job.completionTime or 0))
        for job in completed_jobs
        if Decimal(str(job.completionTime or 0)) > 0
    ]
    avg_completion_time = (
        sum(completion_times) / Decimal(len(completion_times))
        if completion_times
        else Decimal(str(seller_profile.avgCompletionTime or 0))
    )

    trust_score = calculate_trust_score(
        completed_tasks=completed_tasks,
        rejected_tasks=rejected_tasks,
        valid_proofs=valid_proofs,
        invalid_proofs=invalid_proofs,
        audit_passed_tasks=audit_passed_tasks,
        audit_failed_tasks=audit_failed_tasks,
        unethical_reports=seller_profile.unethical_reports,
    )

    audit_retention_rate = safe_ratio(
        audit_passed_tasks,
        audit_checked_tasks,
        default=Decimal("1.00") if completed_tasks > 0 else Decimal("0.60"),
    )

    return {
        "AssignedTasks": assigned_tasks,
        "CompletedTasks": completed_tasks,
        "ApprovedTasks": approved_tasks,
        "RejectedTasks": rejected_tasks,
        "SubmittedProofs": submitted_proofs,
        "ValidProofs": valid_proofs,
        "InvalidProofs": invalid_proofs,
        "ProofValidityRate": safe_ratio(valid_proofs, submitted_proofs),
        "AuditCheckedTasks": audit_checked_tasks,
        "AuditPassedTasks": audit_passed_tasks,
        "AuditFailedTasks": audit_failed_tasks,
        "AvgCompletionTime": avg_completion_time,
        "TrustScore": trust_score,
        "AuditRetentionRate": audit_retention_rate,
    }


def calculate_seller_rating(seller_profile):
    metrics = build_seller_metrics_from_history(seller_profile)
    return calculate_rating_from_metrics(metrics)


def update_seller_rating(seller_profile):
    rating_data = calculate_seller_rating(seller_profile)
    seller_profile.ratings = rating_data["rating"]
    seller_profile.sucessRate = Decimal(str(rating_data["success_rate"] * 100))
    seller_profile.avgCompletionTime = Decimal(str(rating_data["avg_completion_time"]))
    seller_profile.save(update_fields=["ratings", "sucessRate", "avgCompletionTime"])
    return rating_data


def load_rating_dataset(limit=None):
    if not DATASET_PATH.exists():
        return []

    rows = []
    with DATASET_PATH.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            rows.append(row)
            if limit and len(rows) >= limit:
                break
    return rows


def rating_dataset_summary():
    rows = load_rating_dataset()
    rating_counts = {str(rating): 0 for rating in range(1, 6)}

    for row in rows:
        rating = str(row.get("Rating", "")).strip()
        if rating in rating_counts:
            rating_counts[rating] += 1

    return {
        "dataset_path": str(DATASET_PATH),
        "total_rows": len(rows),
        "rating_counts": rating_counts,
    }
