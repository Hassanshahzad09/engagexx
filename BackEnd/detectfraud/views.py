from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.conf import settings
from django.utils import timezone

import json
import statistics
import os
import hashlib
import numpy as np
import pandas as pd
import joblib
import shap

from BackEnd.utils import get_sha256, get_phash, hamming_distance, HAMMING_THRESHOLD
from service.models import JobsHistory, BuyerTasks, SellerProfile, SellerBehaviorLog
from .models import FraudAnalysisResult
from .image_analysis import analyze_proof_image_quality

# ======================================================
# PATHS
# ======================================================
MODEL_PATH      = settings.BASE_DIR / "engagex_model_v3.pkl"
SELLER_ENCODER  = settings.BASE_DIR / "seller_encoder.pkl"
TASK_ENCODER    = settings.BASE_DIR / "task_encoder.pkl"
FEATURE_COLUMNS = settings.BASE_DIR / "feature_columns.pkl"
EXPLAINER_PATH  = settings.BASE_DIR / "engagex_explainer.pkl"

# ======================================================
# GLOBAL STATE
# ======================================================
explainer       = None
model           = None
le_seller       = None
le_task         = None
feature_columns = None


# ======================================================
# TRAIN MODEL
# ======================================================
def train_model():
    global model, le_seller, le_task, feature_columns, explainer

    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import accuracy_score, classification_report

    df = pd.read_csv(settings.BASE_DIR / "engagex_dataset_v5_balanced_layers.csv")
    df.dropna(inplace=True)

    le_seller = LabelEncoder()
    le_task   = LabelEncoder()

    df["seller_type"] = le_seller.fit_transform(df["seller_type"])
    df["task_type"]   = le_task.fit_transform(df["task_type"])

    print(f"[EngageX] seller_type mapping: {list(le_seller.classes_)}")
    print(f"[EngageX] task_type mapping:   {list(le_task.classes_)}")

    DROP_COLS = ["fraud_label", "device_risk_score", "final_behavior_risk_score"]
    DROP_COLS = [c for c in DROP_COLS if c in df.columns]

    X = df.drop(columns=DROP_COLS)
    y = df["fraud_label"]

    feature_columns = list(X.columns)
    print(f"[EngageX] Features ({len(feature_columns)}): {feature_columns}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        min_samples_leaf=15, subsample=0.8,
        max_features="sqrt", random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)
    print(f"[EngageX] Accuracy: {round(acc * 100, 2)}%")
    print(classification_report(y_test, y_pred))

    explainer = shap.TreeExplainer(model)

    joblib.dump(model,           MODEL_PATH)
    joblib.dump(le_seller,       SELLER_ENCODER)
    joblib.dump(le_task,         TASK_ENCODER)
    joblib.dump(feature_columns, FEATURE_COLUMNS)
    joblib.dump(explainer,       EXPLAINER_PATH)
    print("[EngageX] Model and explainer saved")


# ======================================================
# LOAD MODEL
# ======================================================
def load_model():
    global model, le_seller, le_task, feature_columns, explainer

    all_exist = all(os.path.exists(p) for p in [
        MODEL_PATH, SELLER_ENCODER, TASK_ENCODER,
        FEATURE_COLUMNS, EXPLAINER_PATH
    ])

    if all_exist:
        model           = joblib.load(MODEL_PATH)
        le_seller       = joblib.load(SELLER_ENCODER)
        le_task         = joblib.load(TASK_ENCODER)
        feature_columns = joblib.load(FEATURE_COLUMNS)
        try:
            explainer = joblib.load(EXPLAINER_PATH)
        except Exception as exc:
            explainer = None
            print(f"[EngageX] SHAP explainer could not be loaded: {exc}")
        print("[EngageX] Model loaded from disk")
        print(f"[EngageX] seller_type mapping: {list(le_seller.classes_)}")
        print(f"[EngageX] task_type mapping:   {list(le_task.classes_)}")
    else:
        print("[EngageX] Files missing — retraining...")
        train_model()


load_model()


# ======================================================
# FEATURE REASONS MAP
# ======================================================
FEATURE_REASONS = {
    "is_duplicate_screenshot":  {"layer": "Layer 1 — Screenshot Check",    "label": "Duplicate screenshot detected",                 "threshold": lambda v: v >= 1},
    "timing_risk_score":        {"layer": "Layer 2 — Suspicious Timing",   "label": "Task completed suspiciously fast",              "threshold": lambda v: v >= 20},
    "completion_duration":      {"layer": "Layer 2 — Suspicious Timing",   "label": "Completion time is abnormally low",             "threshold": lambda v: v <= 5},
    "std_dev":                  {"layer": "Layer 2 — Repetitive Behavior", "label": "Highly repetitive completion times (bot-like)", "threshold": lambda v: v <= 4},
    "timing_consistency_score": {"layer": "Layer 2 — Repetitive Behavior", "label": "Timing consistency is suspiciously uniform",    "threshold": lambda v: v >= 15},
    "repetitive_behavior_flag": {"layer": "Layer 2 — Repetitive Behavior", "label": "Repetitive behavior pattern flagged",           "threshold": lambda v: v >= 1},
    "z_score":                  {"layer": "Layer 2 — Population Deviation","label": "Completion time far below population average",  "threshold": lambda v: v <= -1.5},
    "population_score":         {"layer": "Layer 2 — Population Deviation","label": "Seller speed abnormal vs all sellers",          "threshold": lambda v: v >= 15},
    "validity_score":           {"layer": "Layer 2 — Validity Check",      "label": "Task completion time is logically impossible",  "threshold": lambda v: v >= 15},
    "logical_behavior_flag":    {"layer": "Layer 2 — Validity Check",      "label": "Behavior is logically inconsistent",            "threshold": lambda v: v >= 1},
    "device_sharing_score":     {"layer": "Layer 2 — Device Analysis",     "label": "Device is shared among multiple sellers",       "threshold": lambda v: v >= 20},
    "ip_reuse_score":           {"layer": "Layer 2 — IP Analysis",         "label": "IP address reused by multiple sellers",         "threshold": lambda v: v >= 20},
    "device_seller_count":      {"layer": "Layer 2 — Device Analysis",     "label": "Multiple seller accounts on same device",       "threshold": lambda v: v >= 3},
    "ip_seller_count":          {"layer": "Layer 2 — IP Analysis",         "label": "Multiple seller accounts from same IP",         "threshold": lambda v: v >= 4},
    "seller_trust_score":       {"layer": "Seller Profile",                "label": "Seller has very low trust score",               "threshold": lambda v: v <= 35},
    "seller_age_days":          {"layer": "Seller Profile",                "label": "Account is very new",                          "threshold": lambda v: v <= 10},
    "total_completed_tasks":    {"layer": "Seller Profile",                "label": "Suspicious task count for account age",         "threshold": lambda v: v >= 200},
}




# ======================================================
# HELPERS — NORMALIZATION + HUMAN EXPLANATION
# ======================================================
def normalize_task_type(task_type):
    task_type = (task_type or "").strip()
    task_type_map = {
        "like": "Like", "likes": "Like",
        "follow": "Follow", "follows": "Follow",
        "comment": "Comment", "comments": "Comment",
        "subscribe": "Subscribe", "subscribes": "Subscribe",
        "subscribing": "Subscribe", "subscription": "Subscribe",
    }
    return task_type_map.get(task_type.lower(), task_type)


def _get_request_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "") or ""


def _make_server_device_id(ip_address, user_agent):
    """
    Fallback only. Best device_id should come from frontend localStorage/fingerprint.
    This fallback keeps Module 3 alive when frontend sends blank deviceId.
    """
    source = f"{ip_address or ''}|{user_agent or ''}"
    if not source.strip('|'):
        return ""
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _hydrate_network_context(request, current_job, ip_address, device_id, user_agent):
    """
    Fraud API sometimes receives empty ipAddress/deviceId from frontend.
    In that case, use the behavior log created during submit_task(), then request metadata,
    then a safe server-side fallback device id.
    """
    ip_address = (ip_address or "").strip()
    device_id = (device_id or "").strip()
    user_agent = (user_agent or "").strip()

    latest_log = None
    if current_job:
        latest_log = current_job.behavior_logs.order_by("-created_at").first()

    if latest_log:
        ip_address = ip_address or (latest_log.ip_address or "")
        device_id = device_id or (latest_log.device_id or "")
        user_agent = user_agent or (latest_log.user_agent or "")

    ip_address = ip_address or _get_request_ip(request)
    user_agent = user_agent or request.META.get("HTTP_USER_AGENT", "")
    device_id = device_id or _make_server_device_id(ip_address, user_agent)

    return ip_address, device_id, user_agent


def _signal(feature, layer, reason, value, impact=0):
    return {
        "feature": feature,
        "layer": layer,
        "reason": reason,
        "value": value,
        "impact": impact,
    }


def _make_human_explanation(layer1_result, timing_result, behavior_result, device_result, layer3_result):
    probability = float(layer3_result.get("fraud_probability", 0) or 0)
    risk_level = layer3_result.get("risk_level", "LOW")
    prediction = layer3_result.get("prediction", "LEGITIMATE")
    summary = f"{prediction.title()} result with {probability}% fraud probability ({risk_level} risk)."
    points = []

    if layer1_result.get("is_duplicate_screenshot"):
        points.append("The submitted screenshot matches an older proof.")
    elif layer1_result.get("image_quality_label") and layer1_result.get("image_quality_label") != "No image provided":
        points.append(f"Screenshot check: {layer1_result.get('image_quality_label')}.")

    if timing_result.get("timing_risk_score", 0) >= 20:
        points.append(f"Timing looks suspicious: completed in {timing_result.get('completion_duration')} seconds.")

    final_behavior = behavior_result.get("final_behavior_analysis", {})
    history_count = behavior_result.get("layer_a", {}).get("history_count", 0)
    if final_behavior.get("repetitive_behavior_flag"):
        points.append("Seller has enough previous tasks and the timing pattern looks repetitive.")
    elif history_count < 2:
        points.append("No repetitive behavior penalty was applied because this seller has insufficient task history.")

    device_count = device_result.get("device_analysis", {}).get("device_seller_count", 1)
    ip_count = device_result.get("ip_analysis", {}).get("ip_seller_count", 1)
    if device_count > 1:
        points.append(f"Same device is linked with {device_count} seller accounts.")
    if ip_count > 2:
        points.append(f"Same IP address is linked with {ip_count} seller accounts.")
    if device_result.get("automation_analysis", {}).get("automation_score", 0) >= 70:
        points.append("Browser/user-agent looks automated, so manual verification is recommended.")

    if not points:
        points.append("No strong fraud signal was found; admin can review the proof normally.")

    return {
        "summary": summary,
        "decision_help": points,
        "admin_recommendation": (
            "Reject or manually verify before approval." if probability >= 70 else
            "Manually check the proof carefully." if probability >= 40 else
            "Looks safe, but still verify the screenshot before approval."
        )
    }

# ======================================================
# SHAP REASON EXTRACTOR
# ======================================================
def _signal_group(signal):
    """
    Group technically different features into one admin-visible reason.
    Example: device_seller_count and device_sharing_score both mean shared device.
    """
    feature = str(signal.get("feature", "")).strip()
    reason = str(signal.get("reason", "")).strip().lower()

    if feature == "is_duplicate_screenshot" or "duplicate screenshot" in reason:
        return "duplicate_screenshot"
    if feature in {"device_seller_count", "device_sharing_score"}:
        return "shared_device"
    if feature in {"ip_seller_count", "ip_reuse_score"}:
        return "shared_ip"
    if feature in {"image_brightness", "image_quality_score", "image_blur", "image_size", "image_detail"}:
        return f"image_quality:{feature}"
    if feature in {"automation_score", "user_agent"}:
        return "automation"
    if feature == "seller_age_days":
        return "new_account"
    if feature in {"timing_risk_score", "completion_duration", "validity_score", "logical_behavior_flag"}:
        return "suspicious_timing"
    if feature in {"std_dev", "timing_consistency_score", "repetitive_behavior_flag"}:
        return "repetitive_behavior"
    if feature in {"z_score", "population_score"}:
        return "population_deviation"
    return feature or reason


def _safe_float(value, default=0):
    try:
        return float(value)
    except Exception:
        return default


def _dedupe_signals(signals, max_items=None):
    """
    Keep one clean reason per fraud group.
    Manual rule impacts are on 0-100 scale; SHAP impacts are usually tiny decimals.
    This avoids showing the same thing twice like:
    - Same device is linked with 9 sellers
    - Device is shared among multiple sellers
    """
    best = {}
    order = []

    for signal in signals or []:
        if not isinstance(signal, dict):
            signal = {"reason": str(signal), "feature": "", "layer": "", "value": "", "impact": 0}

        group = _signal_group(signal)
        impact = abs(_safe_float(signal.get("impact", 0)))
        current = best.get(group)

        if current is None:
            best[group] = signal
            order.append(group)
            continue

        current_impact = abs(_safe_float(current.get("impact", 0)))
        if impact > current_impact:
            best[group] = signal

    cleaned = list(best.values())
    cleaned.sort(key=lambda x: abs(_safe_float(x.get("impact", 0))), reverse=True)

    if max_items:
        return cleaned[:max_items]
    return cleaned


def _strong_fraud_reasons(signals, probability, max_items=5):
    """
    Fraud reasons should be strong/admin-actionable reasons only.
    Weak model hints remain in suspicious_signals.
    """
    strong = []
    for signal in _dedupe_signals(signals):
        group = _signal_group(signal)
        impact = abs(_safe_float(signal.get("impact", 0)))

        if group == "duplicate_screenshot":
            strong.append(signal)
        elif group == "shared_device" and impact >= 30:
            strong.append(signal)
        elif group == "shared_ip" and impact >= 25:
            strong.append(signal)
        elif group == "automation" and impact >= 70:
            strong.append(signal)
        elif group.startswith("image_quality") and impact >= 20:
            strong.append(signal)
        elif probability >= 50 and impact >= 1:
            strong.append(signal)

    return _dedupe_signals(strong, max_items=max_items)


def _apply_rule_based_probability_floor(layer3_result, layer1_result, flat_device, device_result):
    """
    ML probability can be low when the dataset/model under-weights hard fraud rules.
    Exact duplicate proof or heavily shared device should still produce a strong final risk.
    """
    probability = float(layer3_result.get("fraud_probability", 0) or 0)
    floor = 0

    duplicate_type = layer1_result.get("duplicate_type", "none")
    if layer1_result.get("is_duplicate_screenshot"):
        floor = max(floor, 90 if duplicate_type == "exact_sha256" else 80)

    device_count = int(flat_device.get("device_seller_count", 1) or 1)
    ip_count = int(flat_device.get("ip_seller_count", 1) or 1)
    auto_score = int(device_result.get("automation_analysis", {}).get("automation_score", 0) or 0)

    if device_count >= 5:
        floor = max(floor, 75)
    elif device_count >= 3:
        floor = max(floor, 60)

    if auto_score >= 70:
        floor = max(floor, 70)

    # IP is softer because same WiFi/hostel/lab can be normal.
    if ip_count >= 8 and device_count >= 3:
        floor = max(floor, 80)

    final_probability = round(max(probability, floor), 2)
    layer3_result["fraud_probability"] = final_probability
    layer3_result["label"] = 1 if final_probability >= 50 else 0
    layer3_result["prediction"] = "FRAUD" if final_probability >= 50 else "LEGITIMATE"

    if final_probability < 20:
        layer3_result["risk_level"] = "LOW"
    elif final_probability < 50:
        layer3_result["risk_level"] = "MEDIUM"
    elif final_probability < 75:
        layer3_result["risk_level"] = "HIGH"
    else:
        layer3_result["risk_level"] = "CRITICAL"

    if floor > probability:
        layer3_result["probability_adjustment_note"] = (
            f"ML probability was {probability}%, but rule-based hard signals raised final risk to {final_probability}%."
        )

    return layer3_result


def get_fraud_reasons(shap_values, feature_names, input_data, top_n=5):
    if hasattr(shap_values, "values"):
        sv = shap_values.values[0]
    elif isinstance(shap_values, np.ndarray):
        sv = shap_values[0] if shap_values.ndim == 2 else shap_values
    else:
        sv = np.array(shap_values)[0]

    reasons = []
    for i, feat in enumerate(feature_names):
        shap_val = float(sv[i])
        feat_val = input_data.get(feat, 0)
        if shap_val <= 0:
            continue
        if feat not in FEATURE_REASONS:
            continue
        info = FEATURE_REASONS[feat]
        try:
            suspicious = info["threshold"](feat_val)
        except Exception:
            suspicious = False
        if suspicious:
            reasons.append({
                "feature": feat,
                "layer":   info["layer"],
                "reason":  info["label"],
                "value":   round(float(feat_val), 2),
                "impact":  round(float(shap_val), 4),
            })

    return _dedupe_signals(reasons, max_items=top_n)


# ======================================================
# HELPER — SELLER TYPE FROM ACCOUNT AGE
# Uses LabelEncoder classes order:
# experienced=0, intermediate=1, new=2, veteran=3
# ======================================================
def get_seller_type(seller_profile):
    if not seller_profile.user.date_joined:
        return "new", 2, 0          # ← fix: "new" string for encoder

    age_days = (timezone.now() - seller_profile.user.date_joined).days

    if age_days <= 29:
        label = "new"
    elif age_days <= 179:
        label = "intermediate"
    elif age_days <= 364:
        label = "experienced"
    else:
        label = "veteran"

    # ── Encode using the SAME LabelEncoder the model was trained with ──
    try:
        encoded = int(le_seller.transform([label])[0])
    except Exception:
        encoded = 2  # fallback to "new"

    return label, encoded, age_days


# ======================================================
# INTERNAL — TIMING ANALYSIS (Module 1)
# ======================================================
def _run_timing_analysis(task_id, task_type, completion_time):
    timing_classification  = "Unknown"
    suspicious_timing_flag = False
    timing_risk_score      = 0

    if task_type == "Like":
        if completion_time <= 3:     timing_classification="Highly Suspicious"; suspicious_timing_flag=True;  timing_risk_score=35
        elif completion_time <= 8:   timing_classification="Suspicious";        suspicious_timing_flag=True;  timing_risk_score=20
        elif completion_time <= 25:  timing_classification="Normal";            suspicious_timing_flag=False; timing_risk_score=5
        elif completion_time <= 60:  timing_classification="Safe";              suspicious_timing_flag=False; timing_risk_score=0
        else:                        timing_classification="Very Slow";         suspicious_timing_flag=False; timing_risk_score=0

    elif task_type == "Follow":
        if completion_time <= 5:     timing_classification="Highly Suspicious"; suspicious_timing_flag=True;  timing_risk_score=35
        elif completion_time <= 12:  timing_classification="Suspicious";        suspicious_timing_flag=True;  timing_risk_score=20
        elif completion_time <= 40:  timing_classification="Normal";            suspicious_timing_flag=False; timing_risk_score=5
        elif completion_time <= 90:  timing_classification="Safe";              suspicious_timing_flag=False; timing_risk_score=0
        else:                        timing_classification="Very Slow";         suspicious_timing_flag=False; timing_risk_score=0

    elif task_type == "Comment":
        if completion_time <= 10:    timing_classification="Highly Suspicious"; suspicious_timing_flag=True;  timing_risk_score=35
        elif completion_time <= 20:  timing_classification="Suspicious";        suspicious_timing_flag=True;  timing_risk_score=20
        elif completion_time <= 90:  timing_classification="Normal";            suspicious_timing_flag=False; timing_risk_score=5
        elif completion_time <= 180: timing_classification="Safe";              suspicious_timing_flag=False; timing_risk_score=0
        else:                        timing_classification="Very Slow";         suspicious_timing_flag=False; timing_risk_score=0

    elif task_type == "Subscribe":
        if completion_time <= 5:     timing_classification="Highly Suspicious"; suspicious_timing_flag=True;  timing_risk_score=35
        elif completion_time <= 12:  timing_classification="Suspicious";        suspicious_timing_flag=True;  timing_risk_score=20
        elif completion_time <= 35:  timing_classification="Normal";            suspicious_timing_flag=False; timing_risk_score=5
        elif completion_time <= 80:  timing_classification="Safe";              suspicious_timing_flag=False; timing_risk_score=0
        else:                        timing_classification="Very Slow";         suspicious_timing_flag=False; timing_risk_score=0

    return {
        "task_id":                task_id,
        "task_type":              task_type,
        "completion_duration":    completion_time,
        "timing_classification":  timing_classification,
        "suspicious_timing_flag": suspicious_timing_flag,
        "timing_risk_score":      timing_risk_score,
    }


# ======================================================
# INTERNAL — REPETITIVE BEHAVIOR (Module 2)
# ======================================================
def _run_repetitive_behavior(task_id, seller_id, task_type, completion_time):

    task_type_normalized = normalize_task_type(task_type)

    previous_jobs = (
        JobsHistory.objects
        .filter(seller__user_id=seller_id, task__taskType__iexact=task_type_normalized)
        .exclude(task_id=task_id)
        .values("task_id", "seller__user_id", "task__taskType", "completionTime")
        .order_by("-startDate")[:50]
    )
    tasks_list = [{
        "taskId":         str(j["task_id"]),
        "sellerId":       str(j["seller__user_id"]),
        "taskType":       normalize_task_type(j["task__taskType"]),
        # JobsHistory.completionTime is stored in HOURS by service.submit_task.
        # Fraud timing thresholds use SECONDS, so convert DB history to seconds.
        "completionTime": float(j["completionTime"] or 0) * 3600,
    } for j in previous_jobs]

    global_jobs = (
        JobsHistory.objects
        .filter(task__taskType__iexact=task_type_normalized)
        .exclude(seller__user_id=seller_id)
        .values("task_id", "seller__user_id", "task__taskType", "completionTime")
        .order_by("-startDate")[:200]
    )
    allSellers = [{
        "taskId":         str(j["task_id"]),
        "sellerId":       str(j["seller__user_id"]),
        "taskType":       normalize_task_type(j["task__taskType"]),
        # JobsHistory.completionTime is stored in HOURS by service.submit_task.
        # Fraud timing thresholds use SECONDS, so convert DB history to seconds.
        "completionTime": float(j["completionTime"] or 0) * 3600,
    } for j in global_jobs]

    previous_completion_times = [
        t["completionTime"]
        for t in tasks_list
        if t["sellerId"] == str(seller_id) and t["taskType"] == task_type_normalized
    ]
    completion_times = previous_completion_times + [float(completion_time)]
    history_count = len(previous_completion_times)

    # Fix: current task alone must never create a repetitive flag.
    if history_count < 2:
        std_dev                  = 0.0
        timing_consistency_label = "Insufficient History"
        timing_consistency_score = 0
    else:
        std_dev = statistics.stdev(completion_times)
        if std_dev < 2:   timing_consistency_label="Highly Repetitive"; timing_consistency_score=35
        elif std_dev < 5: timing_consistency_label="Moderate";          timing_consistency_score=15
        else:             timing_consistency_label="Natural";           timing_consistency_score=0

    seller_avg       = sum(completion_times) / len(completion_times)
    population_times = [s["completionTime"] for s in allSellers if s["taskType"] == task_type_normalized and s["completionTime"] > 0]

    if len(population_times) > 1:
        population_mean = statistics.mean(population_times)
        population_std  = statistics.stdev(population_times)
    else:
        population_mean = 0.0
        population_std  = 1.0

    z_score = (seller_avg - population_mean) / population_std if population_std != 0 else 0.0

    if z_score < -2:   population_label="Highly Abnormal"; population_score=35
    elif z_score < -1: population_label="Unusual";         population_score=15
    else:              population_label="Normal";          population_score=0

    validity_label="Unknown"; validity_score=0; logical_behavior_flag=False

    if task_type_normalized == "Like":
        if completion_time <= 2:    validity_label="Impossible"; validity_score=35; logical_behavior_flag=True
        elif completion_time <= 8:  validity_label="Suspicious"; validity_score=15; logical_behavior_flag=True
        else:                       validity_label="Realistic";  validity_score=0;  logical_behavior_flag=False
    elif task_type_normalized == "Follow":
        if completion_time <= 4:    validity_label="Impossible"; validity_score=35; logical_behavior_flag=True
        elif completion_time <= 12: validity_label="Suspicious"; validity_score=15; logical_behavior_flag=True
        else:                       validity_label="Realistic";  validity_score=0;  logical_behavior_flag=False
    elif task_type_normalized == "Comment":
        if completion_time <= 5:    validity_label="Impossible"; validity_score=35; logical_behavior_flag=True
        elif completion_time <= 15: validity_label="Suspicious"; validity_score=15; logical_behavior_flag=True
        else:                       validity_label="Realistic";  validity_score=0;  logical_behavior_flag=False
    elif task_type_normalized == "Subscribe":
        if completion_time <= 4:    validity_label="Impossible"; validity_score=35; logical_behavior_flag=True
        elif completion_time <= 10: validity_label="Suspicious"; validity_score=15; logical_behavior_flag=True
        else:                       validity_label="Realistic";  validity_score=0;  logical_behavior_flag=False

    final_behavior_risk_score = timing_consistency_score + population_score + validity_score

    # Fix: only consistency creates a repetitive behavior flag.
    repetitive_behavior_flag = bool(history_count >= 2 and timing_consistency_score >= 15)

    if repetitive_behavior_flag and final_behavior_risk_score >= 70:
        overall_behavior_label = "Highly Suspicious Repetition"
    elif repetitive_behavior_flag:
        overall_behavior_label = "Repetitive Timing Pattern"
    elif history_count < 2 and (population_score > 0 or validity_score > 0):
        overall_behavior_label = "Suspicious Speed, Not Repetitive"
    else:
        overall_behavior_label = "Normal"

    return {
        "layer_a": {
            "completion_times":         completion_times,
            "previous_completion_times": previous_completion_times,
            "history_count":            history_count,
            "std_dev":                  round(std_dev, 2),
            "timing_consistency_label": timing_consistency_label,
            "timing_consistency_score": timing_consistency_score,
        },
        "layer_b": {
            "seller_average":   round(seller_avg, 2),
            "population_mean":  round(population_mean, 2),
            "population_std":   round(population_std, 2),
            "z_score":          round(z_score, 2),
            "population_label": population_label,
            "population_score": population_score,
        },
        "layer_c": {
            "validity_label":        validity_label,
            "validity_score":        validity_score,
            "logical_behavior_flag": logical_behavior_flag,
        },
        "final_behavior_analysis": {
            "final_behavior_risk_score": final_behavior_risk_score,
            "overall_behavior_label":    overall_behavior_label,
            "repetitive_behavior_flag":  repetitive_behavior_flag,
            "note": "Repetition requires at least 2 previous same-type tasks. New sellers are not penalized for repetition.",
        },
        "_flat": {
            "std_dev":                  round(std_dev, 2),
            "seller_average":           round(seller_avg, 2),
            "z_score":                  round(z_score, 2),
            "population_score":         population_score,
            "timing_consistency_score": timing_consistency_score,
            "validity_score":           validity_score,
            "logical_behavior_flag":    int(logical_behavior_flag),
            "repetitive_behavior_flag": int(repetitive_behavior_flag),
        }
    }

# ======================================================
# INTERNAL — IP/DEVICE ANALYSIS (Module 3)
# ======================================================
def _run_ip_device_analysis(task_id, seller_id, ip_address, device_id, user_agent):

    seller_id = str(seller_id)
    ip_address = (ip_address or "").strip()
    device_id = (device_id or "").strip()
    user_agent = (user_agent or "").strip()

    all_logs = SellerBehaviorLog.objects.all().values(
        "task_id", "seller_id", "ip_address", "device_id", "user_agent"
    )
    all_sellers = [{
        "taskId":    str(log["task_id"]),
        "sellerId":  str(log["seller_id"]),
        "ipAddress": (log["ip_address"] or "").strip(),
        "deviceId":  (log["device_id"]  or "").strip(),
        "userAgent": (log["user_agent"] or "").strip(),
    } for log in all_logs]

    # Layer A — Device Sharing
    # Important: blank device_id should NOT be counted as one shared device.
    if device_id:
        device_sellers = {seller_id}
        for s in all_sellers:
            if s["deviceId"] == device_id:
                device_sellers.add(s["sellerId"])
        device_seller_count = len(device_sellers)
    else:
        device_sellers = {seller_id}
        device_seller_count = 1

    if not device_id:
        device_sharing_label = "Device ID Missing"
        device_sharing_score = 10
    elif device_seller_count == 1:
        device_sharing_label = "Safe"
        device_sharing_score = 0
    elif device_seller_count == 2:
        device_sharing_label = "Suspicious"
        device_sharing_score = 30
    else:
        device_sharing_label = "Highly Suspicious"
        device_sharing_score = 70

    # Layer B — IP Reuse
    # Same public IP can be normal in hostel/office/WiFi, so score is softer than device sharing.
    if ip_address:
        ip_sellers = {seller_id}
        for s in all_sellers:
            if s["ipAddress"] == ip_address:
                ip_sellers.add(s["sellerId"])
        ip_seller_count = len(ip_sellers)
    else:
        ip_sellers = {seller_id}
        ip_seller_count = 1

    if not ip_address:
        ip_reuse_label = "IP Missing"
        ip_reuse_score = 5
    elif ip_seller_count <= 2:
        ip_reuse_label = "Normal"
        ip_reuse_score = 0
    elif ip_seller_count <= 5:
        ip_reuse_label = "Suspicious"
        ip_reuse_score = 15
    else:
        ip_reuse_label = "Highly Suspicious"
        ip_reuse_score = 35

    # Layer C — Bot / automation clue from User-Agent
    bot_keywords      = ["headless", "selenium", "phantomjs", "puppeteer", "python-requests", "scrapy", "bot", "playwright"]
    detected_keywords = [kw for kw in bot_keywords if kw.lower() in user_agent.lower()]
    automation_score  = 70 if detected_keywords else 0
    automation_label  = "Automation Detected" if detected_keywords else "Normal"

    device_risk_score = min(device_sharing_score + ip_reuse_score + automation_score, 100)

    if device_risk_score >= 70:
        overall_device_label = "Highly Suspicious"
        device_fraud_flag = True
    elif device_risk_score >= 30:
        overall_device_label = "Moderately Suspicious"
        device_fraud_flag = True
    elif device_risk_score >= 10:
        overall_device_label = "Needs Context"
        device_fraud_flag = False
    else:
        overall_device_label = "Normal"
        device_fraud_flag = False

    return {
        "device_analysis": {
            "device_id":            device_id,
            "device_seller_count":  device_seller_count,
            "device_sellers":       list(device_sellers),
            "device_sharing_label": device_sharing_label,
            "device_sharing_score": device_sharing_score,
        },
        "ip_analysis": {
            "ip_address":      ip_address,
            "ip_seller_count": ip_seller_count,
            "ip_sellers":      list(ip_sellers),
            "ip_reuse_label":  ip_reuse_label,
            "ip_reuse_score":  ip_reuse_score,
        },
        "automation_analysis": {
            "user_agent":        user_agent,
            "detected_keywords": detected_keywords,
            "automation_label":  automation_label,
            "automation_score":  automation_score,
        },
        "final_device_analysis": {
            "device_risk_score":    device_risk_score,
            "overall_device_label": overall_device_label,
            "device_fraud_flag":    device_fraud_flag,
        },
        "_flat": {
            "device_seller_count":  device_seller_count,
            "device_sharing_score": device_sharing_score,
            "ip_seller_count":      ip_seller_count,
            "ip_reuse_score":       ip_reuse_score,
            "automation_score":     automation_score,
        }
    }


# ======================================================
# INTERNAL — SCREENSHOT ANALYSIS
# ======================================================
def _run_screenshot_analysis(current_job):
    result = {
        "is_duplicate_screenshot": 0,
        "message": "No screenshot submitted",
        "duplicate_type": "none",
        "duplicate_job_id": None,
        "image_quality_score": 0,
        "image_quality_label": "No image provided",
        "image_signals": [],
    }

    if not current_job:
        return result

    if current_job.proofSha256:
        duplicate = (
            JobsHistory.objects
            .filter(proofSha256=current_job.proofSha256)
            .exclude(proofSha256="")
            .exclude(id=current_job.id)
            .first()
        )
        if duplicate:
            result.update({
                "is_duplicate_screenshot": 1,
                "message": "Exact duplicate screenshot detected",
                "duplicate_type": "exact_sha256",
                "duplicate_job_id": duplicate.id,
            })

    if not result["is_duplicate_screenshot"] and getattr(current_job, "proofPhash", ""):
        old_proofs = (
            JobsHistory.objects
            .exclude(id=current_job.id)
            .exclude(proofPhash="")
            .exclude(proofPhash__isnull=True)
            .only("id", "proofPhash")
        )
        for old_job in old_proofs:
            try:
                distance = hamming_distance(current_job.proofPhash, old_job.proofPhash)
            except Exception:
                continue
            if distance < HAMMING_THRESHOLD:
                result.update({
                    "is_duplicate_screenshot": 1,
                    "message": "Similar or edited duplicate screenshot detected",
                    "duplicate_type": "perceptual_hash",
                    "duplicate_job_id": old_job.id,
                    "phash_distance": distance,
                    "phash_threshold": HAMMING_THRESHOLD,
                })
                break

    if getattr(current_job, "proofImage", None):
        try:
            quality = analyze_proof_image_quality(image_path=current_job.proofImage.path)
        except Exception:
            quality = analyze_proof_image_quality(None)
        result.update({
            "image_quality_score": quality.get("image_quality_score", 0),
            "image_quality_label": quality.get("image_quality_label", "No image provided"),
            "image_signals": quality.get("image_signals", []),
            "image_width": quality.get("image_width", 0),
            "image_height": quality.get("image_height", 0),
            "image_format": quality.get("image_format", ""),
            "image_file_size_kb": quality.get("image_file_size_kb", 0),
        })
        if not result["is_duplicate_screenshot"]:
            result["message"] = result["image_quality_label"]

    return result

# ======================================================
# INTERNAL — ML PREDICTION (Layer 3)
# ======================================================
def _run_ml_prediction(layer3_input):
    sample_df = pd.DataFrame([layer3_input])
    for col in feature_columns:
        if col not in sample_df.columns:
            sample_df[col] = 0
    sample_df = sample_df[feature_columns]

    raw_proba         = float(model.predict_proba(sample_df)[0][1])
    fraud_probability = round(raw_proba * 100, 2)
    prediction        = 1 if fraud_probability >= 50 else 0

    if fraud_probability < 20:   risk_level = "LOW"
    elif fraud_probability < 50: risk_level = "MEDIUM"
    elif fraud_probability < 75: risk_level = "HIGH"
    else:                        risk_level = "CRITICAL"

    suspicious_signals = []
    try:
        shap_values        = explainer.shap_values(sample_df)
        suspicious_signals = get_fraud_reasons(
            shap_values=shap_values,
            feature_names=feature_columns,
            input_data=layer3_input,
            top_n=5,
        )
    except Exception as e:
        print(f"[EngageX] SHAP error: {str(e)}")

    return {
        "prediction":         "FRAUD" if prediction == 1 else "LEGITIMATE",
        "fraud_probability":  fraud_probability,
        "risk_level":         risk_level,
        "label":              prediction,
        # Keep reasons visible for admin even when probability is below 50%.
        # Fraud reasons are NOT only for 100% fraud; they explain the strongest signals found.
        "fraud_reasons":      suspicious_signals,
        "suspicious_signals": suspicious_signals,
    }


# ======================================================
# STANDALONE VIEW — Screenshot Upload (Layer 1)
# ======================================================
@csrf_exempt
def upload_job_screenshot_proof(request, task_id, seller_id):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    screenshot = request.FILES.get("proofImage") or request.FILES.get("screenshot")
    if not screenshot:
        return JsonResponse({"error": "No screenshot image provided"}, status=400)

    try:
        with transaction.atomic():
            try:
                task = BuyerTasks.objects.get(id=task_id)
            except BuyerTasks.DoesNotExist:
                return JsonResponse({"error": "Task not found"}, status=404)

            try:
                seller_profile = SellerProfile.objects.get(user_id=seller_id)
            except SellerProfile.DoesNotExist:
                return JsonResponse({"error": "Seller profile not found"}, status=404)

            current_job = (
                JobsHistory.objects
                .select_for_update()
                .filter(task=task, seller=seller_profile, status="pending")
                .order_by("-startDate")
                .first()
            )

            if not current_job:
                return JsonResponse({"error": "No pending job found for this seller and task"}, status=400)

            sha256_new = get_sha256(screenshot)
            phash_new  = get_phash(screenshot)

            # Layer 1 — Exact Duplicate
            exact_duplicate = (
                JobsHistory.objects
                .filter(proofSha256=sha256_new)
                .exclude(id=current_job.id)
                .first()
            )

            if exact_duplicate:
                screenshot.seek(0)
                current_job.proofImage  = screenshot
                current_job.proofSha256 = sha256_new
                # ── fix: only save proofPhash if field exists on model ──
                if hasattr(current_job, "proofPhash"):
                    current_job.proofPhash = phash_new
                    current_job.save(update_fields=["proofImage","proofSha256","proofPhash"])
                else:
                    current_job.save(update_fields=["proofImage","proofSha256"])

                return JsonResponse({
                    "status": "rejected", "layer": 1,
                    "message": "Exact duplicate screenshot detected.",
                    "is_duplicate_screenshot": 1,
                    "sha256":            sha256_new,
                    "duplicateJobId":    exact_duplicate.id,
                    "duplicateSellerId": exact_duplicate.seller.user_id,
                    "duplicateTaskId":   exact_duplicate.task_id,
                }, status=409)

            # Layer 2 — Similar / Edited (perceptual hash)
            if hasattr(current_job, "proofPhash"):
                old_proofs = (
                    JobsHistory.objects
                    .exclude(id=current_job.id)
                    .exclude(proofPhash="")
                    .exclude(proofPhash__isnull=True)
                )
                for old_job in old_proofs:
                    distance = hamming_distance(phash_new, old_job.proofPhash)
                    if distance < HAMMING_THRESHOLD:
                        screenshot.seek(0)
                        current_job.proofImage  = screenshot
                        current_job.proofSha256 = sha256_new
                        current_job.proofPhash  = phash_new
                        current_job.save(update_fields=["proofImage","proofSha256","proofPhash"])
                        return JsonResponse({
                            "status": "rejected", "layer": 2,
                            "message": "Similar or edited duplicate screenshot detected.",
                            "is_duplicate_screenshot": 1,
                            "distance":          distance,
                            "threshold":         HAMMING_THRESHOLD,
                            "sha256":            sha256_new,
                            "phash":             phash_new,
                            "duplicateJobId":    old_job.id,
                            "duplicateSellerId": old_job.seller.user_id,
                            "duplicateTaskId":   old_job.task_id,
                        }, status=409)

            # Accepted
            screenshot.seek(0)
            current_job.proofImage  = screenshot
            current_job.proofSha256 = sha256_new
            if hasattr(current_job, "proofPhash"):
                current_job.proofPhash = phash_new
                current_job.save(update_fields=["proofImage","proofSha256","proofPhash"])
            else:
                current_job.save(update_fields=["proofImage","proofSha256"])

            return JsonResponse({
                "status":   "accepted",
                "message":  "Screenshot saved. No duplicate found.",
                "is_duplicate_screenshot": 0,
                "jobId":    current_job.id,
                "taskId":   task.id,
                "sellerId": seller_profile.user_id,
                "sha256":   sha256_new,
            }, status=201)

    except Exception as error:
        return JsonResponse({"error": str(error)}, status=500)


# ======================================================
# STANDALONE VIEW — Timing Analysis
# ======================================================
@csrf_exempt
def suspiciousTimingAnalysis(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)
    try:
        data            = json.loads(request.body)
        task_id         = data.get("taskId")
        task_type       = data.get("taskType")
        completion_time = float(data.get("completionTime"))
    except Exception as e:
        return JsonResponse({"error": "Invalid request data", "details": str(e)}, status=400)

    if task_type not in ("Like","Follow","Comment","Subscribe"):
        return JsonResponse({"error": "Invalid task type"}, status=400)

    return JsonResponse(_run_timing_analysis(task_id, task_type, completion_time), status=200)


# ======================================================
# STANDALONE VIEW — Repetitive Behavior
# ======================================================
@csrf_exempt
def analyzeRepetitiveBehavior(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)
    try:
        data                    = json.loads(request.body)
        currentTask             = data[0]
        task_id                 = currentTask["taskId"]
        seller_id               = currentTask["sellerId"]
        task_type               = currentTask["taskType"]
        current_completion_time = float(currentTask["completionTime"])
        previous_tasks          = data[1]["previousTasks"]
        sellersHistory          = data[2]["sellerHistory"]
    except Exception as e:
        return JsonResponse({"error": "Invalid request data", "details": str(e)}, status=400)

    tasks_list = [{
        "taskId":         t.get("taskId"),
        "sellerId":       t.get("sellerId"),
        "taskType":       t.get("taskType"),
        "completionTime": float(t.get("completionTime", 0)),
    } for t in previous_tasks]

    allSellers = [{
        "taskId":         s.get("taskId"),
        "sellerId":       s.get("sellerId"),
        "taskType":       s.get("taskType"),
        "completionTime": float(s.get("completionTime", 0)),
    } for s in sellersHistory]

    completion_times = [
        t["completionTime"]
        for t in tasks_list
        if t["sellerId"] == seller_id and t["taskType"] == task_type
    ]
    completion_times.append(current_completion_time)
    if len(completion_times) < 3:
        std_dev                  = None
        timing_consistency_label = "Insufficient History"
        timing_consistency_score = 0   # ← no penalty for new users
    else:
        std_dev = statistics.stdev(completion_times) if len(completion_times) > 1 else 0.0

        if std_dev < 2:   timing_consistency_label="Highly Repetitive"; timing_consistency_score=35
        elif std_dev < 5: timing_consistency_label="Moderate";          timing_consistency_score=15
        else:             timing_consistency_label="Natural";            timing_consistency_score=0

    seller_avg       = sum(completion_times) / len(completion_times)
    population_times = [s["completionTime"] for s in allSellers if s["taskType"] == task_type]

    if len(population_times) > 1:
        population_mean = statistics.mean(population_times)
        population_std  = statistics.stdev(population_times)
    else:
        population_mean = 0.0; population_std = 1.0

    z_score = (seller_avg - population_mean) / population_std if population_std != 0 else 0.0

    if z_score < -2:   population_label="Highly Abnormal"; population_score=35
    elif z_score < -1: population_label="Unusual";         population_score=15
    else:              population_label="Normal";           population_score=0

    validity_label="Unknown"; validity_score=0; logical_behavior_flag=False

    if task_type == "Like":
        if current_completion_time <= 2:    validity_label="Impossible"; validity_score=35; logical_behavior_flag=True
        elif current_completion_time <= 8:  validity_label="Suspicious"; validity_score=15; logical_behavior_flag=True
        else:                               validity_label="Realistic";  validity_score=0;  logical_behavior_flag=False
    elif task_type == "Follow":
        if current_completion_time <= 4:    validity_label="Impossible"; validity_score=35; logical_behavior_flag=True
        elif current_completion_time <= 12: validity_label="Suspicious"; validity_score=15; logical_behavior_flag=True
        else:                               validity_label="Realistic";  validity_score=0;  logical_behavior_flag=False
    elif task_type == "Comment":
        if current_completion_time <= 5:    validity_label="Impossible"; validity_score=35; logical_behavior_flag=True
        elif current_completion_time <= 15: validity_label="Suspicious"; validity_score=15; logical_behavior_flag=True
        else:                               validity_label="Realistic";  validity_score=0;  logical_behavior_flag=False
    elif task_type == "Subscribe":
        if current_completion_time <= 4:    validity_label="Impossible"; validity_score=35; logical_behavior_flag=True
        elif current_completion_time <= 10: validity_label="Suspicious"; validity_score=15; logical_behavior_flag=True
        else:                               validity_label="Realistic";  validity_score=0;  logical_behavior_flag=False

    final_behavior_risk_score = timing_consistency_score + population_score + validity_score

    if final_behavior_risk_score >= 70:   repetitive_behavior_flag=True;  overall_behavior_label="Highly Suspicious"
    elif final_behavior_risk_score >= 30: repetitive_behavior_flag=True;  overall_behavior_label="Moderately Suspicious"
    else:                                 repetitive_behavior_flag=False; overall_behavior_label="Normal"

    return JsonResponse({
        "task_id": task_id, "seller_id": seller_id, "task_type": task_type,
        "layer_a": {"completion_times": completion_times, "std_dev": round(std_dev,2)  if std_dev is not None else 0.0, "timing_consistency_label": timing_consistency_label, "timing_consistency_score": timing_consistency_score},
        "layer_b": {"seller_average": round(seller_avg,2), "population_mean": round(population_mean,2), "population_std": round(population_std,2), "z_score": round(z_score,2), "population_label": population_label, "population_score": population_score},
        "layer_c": {"validity_label": validity_label, "validity_score": validity_score, "logical_behavior_flag": logical_behavior_flag},
        "final_behavior_analysis": {"final_behavior_risk_score": final_behavior_risk_score, "overall_behavior_label": overall_behavior_label, "repetitive_behavior_flag": repetitive_behavior_flag},
    }, status=200)


# ======================================================
# STANDALONE VIEW — IP/Device Anomalies
# ======================================================
@csrf_exempt
def detect_ip_anomalies(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)
    try:
        data          = json.loads(request.body)
        currentSeller = data["currentSeller"]
        task_id       = currentSeller["taskId"]
        seller_id     = currentSeller["sellerId"]
        ip_address    = currentSeller["ipAddress"]
        device_id     = currentSeller["deviceId"]
        user_agent    = currentSeller["userAgent"]
        all_sellers   = data["allSellers"]
    except Exception as e:
        return JsonResponse({"error": "Invalid JSON data", "details": str(e)}, status=400)

    device_sellers = {seller_id}
    for s in all_sellers:
        if s["deviceId"] == device_id: device_sellers.add(s["sellerId"])
    device_seller_count = len(device_sellers)

    if device_seller_count == 1:   device_sharing_label="Safe";              device_sharing_score=0
    elif device_seller_count == 2: device_sharing_label="Suspicious";        device_sharing_score=30
    else:                          device_sharing_label="Highly Suspicious"; device_sharing_score=70

    ip_sellers = {seller_id}
    for s in all_sellers:
        if s["ipAddress"] == ip_address: ip_sellers.add(s["sellerId"])
    ip_seller_count = len(ip_sellers)

    if ip_seller_count <= 2:   ip_reuse_label="Normal";             ip_reuse_score=0
    elif ip_seller_count <= 5: ip_reuse_label="Suspicious";         ip_reuse_score=15
    else:                      ip_reuse_label="Highly Suspicious";  ip_reuse_score=35

    bot_keywords      = ["headless","selenium","phantomjs","puppeteer","python-requests","scrapy","bot"]
    detected_keywords = [kw for kw in bot_keywords if kw.lower() in user_agent.lower()]
    automation_score  = 70 if detected_keywords else 0
    automation_label  = "Automation Detected" if detected_keywords else "Normal"

    device_risk_score = min(device_sharing_score + ip_reuse_score + automation_score, 100)

    if device_risk_score >= 70:   overall_device_label="Highly Suspicious";    device_fraud_flag=True
    elif device_risk_score >= 30: overall_device_label="Moderately Suspicious"; device_fraud_flag=True
    else:                         overall_device_label="Normal";               device_fraud_flag=False

    return JsonResponse({
        "task_id": task_id, "seller_id": seller_id,
        "device_analysis":     {"device_id": device_id, "device_seller_count": device_seller_count, "device_sellers": list(device_sellers), "device_sharing_label": device_sharing_label, "device_sharing_score": device_sharing_score},
        "ip_analysis":         {"ip_address": ip_address, "ip_seller_count": ip_seller_count, "ip_sellers": list(ip_sellers), "ip_reuse_label": ip_reuse_label, "ip_reuse_score": ip_reuse_score},
        "automation_analysis": {"user_agent": user_agent, "detected_keywords": detected_keywords, "automation_label": automation_label, "automation_score": automation_score},
        "final_device_analysis": {"device_risk_score": device_risk_score, "overall_device_label": overall_device_label, "device_fraud_flag": device_fraud_flag},
        "ml_features": {"device_seller_count": device_seller_count, "device_sharing_score": device_sharing_score, "ip_seller_count": ip_seller_count, "ip_reuse_score": ip_reuse_score, "automation_score": automation_score, "device_risk_score": device_risk_score, "device_fraud_flag": int(device_fraud_flag)},
    }, status=200)


# ======================================================
# STANDALONE VIEW — ML Predict Fraud
# ======================================================
@csrf_exempt
def predict_fraud(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    flat_input = {}
    for key, value in body.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, dict):
                    for k2, v2 in sub_value.items(): flat_input[k2] = v2
                else: flat_input[sub_key] = sub_value
        else: flat_input[key] = value

    try:
        if "seller_type" in flat_input and isinstance(flat_input["seller_type"], str):
            flat_input["seller_type"] = int(le_seller.transform([flat_input["seller_type"]])[0])
        if "task_type" in flat_input and isinstance(flat_input["task_type"], str):
            flat_input["task_type"]   = int(le_task.transform([flat_input["task_type"]])[0])
    except Exception as e:
        return JsonResponse({"error": f"Encoding error: {str(e)}"}, status=400)

    return JsonResponse(_run_ml_prediction(flat_input))


# ======================================================
# MAIN UNIFIED ORCHESTRATOR
# Frontend sends ONLY:
#   taskId, sellerId, completionTime,
#   ipAddress, deviceId, userAgent
# ======================================================
@csrf_exempt
def analyze_seller_submission(request):

    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    # 1. Parse input
    try:
        data            = json.loads(request.body)
        task_id         = data.get("taskId")
        seller_id       = data.get("sellerId")
        completion_time = float(data.get("completionTime"))
        ip_address      = data.get("ipAddress", "")
        device_id       = data.get("deviceId",  "")
        user_agent      = data.get("userAgent",  "")
    except Exception as e:
        return JsonResponse({"error": "Invalid request data", "details": str(e)}, status=400)

    # 2. Fetch from DB
    try:
        task           = BuyerTasks.objects.get(id=task_id)
        seller_profile = SellerProfile.objects.get(user_id=seller_id)
    except BuyerTasks.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)
    except SellerProfile.DoesNotExist:
        return JsonResponse({"error": "Seller profile not found"}, status=404)

    task_type = normalize_task_type(task.taskType)
    # 3. Seller info
    seller_type_label, seller_type_encoded, seller_age_days = get_seller_type(seller_profile)

    total_completed_tasks = JobsHistory.objects.filter(
        seller=seller_profile, status="approved"
    ).count()

    seller_trust_score = float(getattr(seller_profile, "trust_score", 50) or 50)

    # 4. Layer 1 — check duplicate from DB
    current_job = (
    JobsHistory.objects
    .filter(
        task=task,
        seller=seller_profile,
        status__in=["pending", "submitted"]
    )
    .order_by("-startDate")
    .first()
)

    ip_address, device_id, user_agent = _hydrate_network_context(
        request, current_job, ip_address, device_id, user_agent
    )

    layer1_result = _run_screenshot_analysis(current_job)
    is_duplicate_screenshot = int(layer1_result.get("is_duplicate_screenshot", 0))

    # 5. Layer 2 Module 1 — Timing
    timing_result = _run_timing_analysis(task_id, task_type, completion_time)

    # 6. Layer 2 Module 2 — Repetitive Behavior
    behavior_result = _run_repetitive_behavior(task_id, seller_id, task_type, completion_time)

    # 7. Save / reuse BehaviorLog then run Module 3
    # submit_task() already creates this log. Here we only create one if missing.
    if current_job and not current_job.behavior_logs.exists():
        SellerBehaviorLog.objects.create(
            task_id    = str(task_id),
            seller_id  = str(seller_id),
            job        = current_job,
            ip_address = ip_address or None,
            device_id  = device_id,
            user_agent = user_agent,
        )
    device_result = _run_ip_device_analysis(task_id, seller_id, ip_address, device_id, user_agent)

    # 8. Build Layer 3 payload
    # ── fix: use LabelEncoder for task_type, not hardcoded map ──
    try:
        task_type_encoded = int(le_task.transform([task_type])[0])
    except Exception:
        task_type_encoded = 0

    flat_behavior = behavior_result["_flat"]
    flat_device   = device_result["_flat"]

    layer3_input = {
        "seller_type":              seller_type_encoded,
        "seller_age_days":          seller_age_days,
        "total_completed_tasks":    total_completed_tasks,
        "seller_trust_score":       seller_trust_score,
        "task_type":                task_type_encoded,
        "is_duplicate_screenshot":  is_duplicate_screenshot,
        "completion_duration":      completion_time,
        "timing_risk_score":        timing_result["timing_risk_score"],
        "std_dev":                  flat_behavior["std_dev"],
        "seller_average":           flat_behavior["seller_average"],
        "z_score":                  flat_behavior["z_score"],
        "population_score":         flat_behavior["population_score"],
        "timing_consistency_score": flat_behavior["timing_consistency_score"],
        "validity_score":           flat_behavior["validity_score"],
        "logical_behavior_flag":    flat_behavior["logical_behavior_flag"],
        "repetitive_behavior_flag": flat_behavior["repetitive_behavior_flag"],
        "device_seller_count":      flat_device["device_seller_count"],
        "device_sharing_score":     flat_device["device_sharing_score"],
        "ip_seller_count":          flat_device["ip_seller_count"],
        "ip_reuse_score":           flat_device["ip_reuse_score"],
        "automation_score":         flat_device.get("automation_score", 0),
    }

    # 9. Layer 3 — ML Prediction
    # 9. Layer 3 — ML Prediction
    layer3_result = _run_ml_prediction(layer3_input)

    manual_signals = []
    if is_duplicate_screenshot:
        manual_signals.append(_signal(
            "is_duplicate_screenshot",
            "Layer 1 — Screenshot Check",
            layer1_result.get("message", "Duplicate screenshot detected"),
            layer1_result.get("duplicate_type", "duplicate"),
            100,
        ))
    manual_signals.extend(layer1_result.get("image_signals", []))

    if flat_device["device_seller_count"] >= 2 or flat_device["device_sharing_score"] >= 20:
        manual_signals.append(_signal(
            "device_seller_count",
            "Layer 2 — Device Analysis",
            f"Same device is linked with {flat_device['device_seller_count']} seller account(s)",
            flat_device["device_seller_count"],
            flat_device["device_sharing_score"],
        ))

    if flat_device["ip_seller_count"] >= 3 or flat_device["ip_reuse_score"] >= 15:
        manual_signals.append(_signal(
            "ip_seller_count",
            "Layer 2 — IP Analysis",
            f"Same IP is linked with {flat_device['ip_seller_count']} seller account(s)",
            flat_device["ip_seller_count"],
            flat_device["ip_reuse_score"],
        ))

    auto_score = device_result.get("automation_analysis", {}).get("automation_score", 0)
    if auto_score >= 70:
        manual_signals.append(_signal(
            "automation_score",
            "Layer 2 — Bot/User-Agent Analysis",
            "Browser/user-agent looks automated",
            device_result.get("automation_analysis", {}).get("detected_keywords", []),
            auto_score,
        ))

    # 9.1 Combine rule signals + ML signals cleanly.
    # suspicious_signals = all useful signals, but without duplicate meanings.
    # fraud_reasons = only strong/actionable reasons for admin decision.
    combined_signals = manual_signals + layer3_result.get("suspicious_signals", [])
    layer3_result["suspicious_signals"] = _dedupe_signals(combined_signals, max_items=8)

    layer3_result = _apply_rule_based_probability_floor(
        layer3_result=layer3_result,
        layer1_result=layer1_result,
        flat_device=flat_device,
        device_result=device_result,
    )
    layer3_result["fraud_reasons"] = _strong_fraud_reasons(
        layer3_result.get("suspicious_signals", []),
        probability=layer3_result.get("fraud_probability", 0),
        max_items=5,
    )

    human_explanation = _make_human_explanation(
        layer1_result, timing_result, behavior_result, device_result, layer3_result
    )

    # 10. Save to FraudAnalysisResult ─────────────────────────────
    try:

        # Re-analysis of same proof should update the latest result instead of failing
        # because FraudAnalysisResult.job is OneToOne.
        if current_job:
            FraudAnalysisResult.objects.filter(job=current_job).delete()

        fraud_result = FraudAnalysisResult.objects.create(
            # Core references
            job     = current_job,
            task    = task,
            seller  = seller_profile,

            # Layer 1
            is_duplicate_screenshot = bool(is_duplicate_screenshot),

            # Layer 2 — Timing
            completion_duration   = completion_time,
            timing_risk_score     = timing_result["timing_risk_score"],
            timing_classification = timing_result["timing_classification"],

            # Layer 2 — Behavior
            std_dev                  = flat_behavior["std_dev"],
            z_score                  = flat_behavior["z_score"],
            population_score         = flat_behavior["population_score"],
            timing_consistency_score = flat_behavior["timing_consistency_score"],
            validity_score           = flat_behavior["validity_score"],
            logical_behavior_flag    = bool(flat_behavior["logical_behavior_flag"]),
            repetitive_behavior_flag = bool(flat_behavior["repetitive_behavior_flag"]),
            overall_behavior_label   = behavior_result["final_behavior_analysis"]["overall_behavior_label"],

            # Layer 2 — Device/IP
            ip_address           = ip_address or None,
            device_id            = device_id,
            device_seller_count  = flat_device["device_seller_count"],
            ip_seller_count      = flat_device["ip_seller_count"],
            device_sharing_score = flat_device["device_sharing_score"],
            ip_reuse_score       = flat_device["ip_reuse_score"],
            device_sharing_label = device_result["device_analysis"]["device_sharing_label"],
            ip_reuse_label       = device_result["ip_analysis"]["ip_reuse_label"],

            # Layer 3 — ML Result
            prediction        = layer3_result["prediction"],
            fraud_probability = layer3_result["fraud_probability"],
            risk_level        = layer3_result["risk_level"],
            is_fraud          = layer3_result["label"] == 1,
            fraud_reasons     = layer3_result["fraud_reasons"],
            suspicious_signals = layer3_result["suspicious_signals"],

            # Seller snapshot
            seller_type        = seller_type_label,
            seller_age_days    = seller_age_days,
            seller_trust_score = seller_trust_score,
        )
        JobsHistory.objects.filter(id=fraud_result.job_id).update(fraud_id=fraud_result.id)

        print(f"[EngageX] FraudAnalysisResult saved for seller {seller_id} task {task_id}")
    except Exception as e:
        print(f"[EngageX] Failed to save FraudAnalysisResult: {e}")
        # Don't crash the response if saving fails

    # 11. Full response
    return JsonResponse({
        "sellerInfo": {
            "sellerId":            str(seller_id),
            "sellerType":          seller_type_label,
            "sellerAgeDays":       seller_age_days,
            "trustScore":          seller_trust_score,
            "totalCompletedTasks": total_completed_tasks,
        },
        "fraud_layers_summary": {
            "total_main_layers": 3,
            "layer1": "Screenshot/proof duplicate + image quality",
            "layer2_modules": ["Timing", "Repetitive behavior", "Device/IP", "Bot/User-Agent"],
            "layer3": "ML probability + explainable reasons",
        },
        "networkContextUsed": {
            "ipAddress": ip_address,
            "deviceId": device_id,
            "userAgent": user_agent,
        },
        "layer1_screenshot": layer1_result,
        "layer2": {
            "module1_timing":   timing_result,
            "module2_behavior": {
                "layer_a":                 behavior_result["layer_a"],
                "layer_b":                 behavior_result["layer_b"],
                "layer_c":                 behavior_result["layer_c"],
                "final_behavior_analysis": behavior_result["final_behavior_analysis"],
            },
            "module3_device": {
                "device_analysis":       device_result["device_analysis"],
                "ip_analysis":           device_result["ip_analysis"],
                "automation_analysis":   device_result["automation_analysis"],
                "final_device_analysis": device_result["final_device_analysis"],
            },
        },
        "layer3_prediction": layer3_result,
        "human_explanation": human_explanation,
    }, status=200)