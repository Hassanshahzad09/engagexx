from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.conf import settings
from django.utils import timezone

import json
import statistics
import os
import numpy as np
import pandas as pd
import joblib
import shap

from BackEnd.utils import get_sha256, get_phash, hamming_distance, HAMMING_THRESHOLD
from service.models import JobsHistory, BuyerTasks, SellerProfile, SellerBehaviorLog


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

    df = pd.read_csv(settings.BASE_DIR / "engagex_dataset_v4.csv")
    df.dropna(inplace=True)

    le_seller = LabelEncoder()
    le_task   = LabelEncoder()

    df["seller_type"] = le_seller.fit_transform(df["seller_type"])
    df["task_type"]   = le_task.fit_transform(df["task_type"])

    print(f"[EngageX] seller_type mapping: {list(le_seller.classes_)}")
    print(f"[EngageX] task_type mapping:   {list(le_task.classes_)}")

    DROP_COLS = ["fraud_label","device_risk_score","final_behavior_risk_score","automation_score"]
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
# SHAP REASON EXTRACTOR
# ======================================================
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

    reasons.sort(key=lambda x: x["impact"], reverse=True)
    return reasons[:top_n]


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

    # ── Normalize task_type to match your thresholds ──────────────
    # Handles: 'follows' → 'Follow', 'likes' → 'Like', etc.
    task_type_map = {
        "like": "Like", "likes": "Like",
        "follow": "Follow", "follows": "Follow",
        "comment": "Comment", "comments": "Comment",
        "subscribe": "Subscribe", "subscribes": "Subscribe",
    }
    task_type_normalized = task_type_map.get(task_type.lower(), task_type)

    previous_jobs = (
        JobsHistory.objects
        .filter(seller__user_id=seller_id, task__taskType=task_type)
        .exclude(task_id=task_id)
        .values("task_id", "seller__user_id", "task__taskType", "completionTime")
        .order_by("-startDate")[:50]
    )
    tasks_list = [{
        "taskId":         str(j["task_id"]),
        "sellerId":       str(j["seller__user_id"]),
        "taskType":       j["task__taskType"],
        "completionTime": float(j["completionTime"] or 0),
    } for j in previous_jobs]

    global_jobs = (
        JobsHistory.objects
        .filter(task__taskType=task_type)
        .exclude(seller__user_id=seller_id)
        .values("task_id", "seller__user_id", "task__taskType", "completionTime")
        .order_by("-startDate")[:200]
    )
    allSellers = [{
        "taskId":         str(j["task_id"]),
        "sellerId":       str(j["seller__user_id"]),
        "taskType":       j["task__taskType"],
        "completionTime": float(j["completionTime"] or 0),
    } for j in global_jobs]

    # ── Layer A — Timing Consistency ──────────────────────────────
    completion_times = [
        t["completionTime"]
        for t in tasks_list
        if t["sellerId"] == str(seller_id) and t["taskType"] == task_type
    ]
    completion_times.append(completion_time)

    # Need at least 3 data points to judge consistency fairly
    if len(completion_times) < 3:
        std_dev                  = 0.0          # ← safe default, not None
        timing_consistency_label = "Insufficient History"
        timing_consistency_score = 0
    else:
        std_dev = statistics.stdev(completion_times)
        if std_dev < 2:   timing_consistency_label="Highly Repetitive"; timing_consistency_score=35
        elif std_dev < 5: timing_consistency_label="Moderate";          timing_consistency_score=15
        else:             timing_consistency_label="Natural";            timing_consistency_score=0

    # ── Layer B — Population Deviation ───────────────────────────
    seller_avg       = sum(completion_times) / len(completion_times)
    population_times = [s["completionTime"] for s in allSellers if s["taskType"] == task_type]

    if len(population_times) > 1:
        population_mean = statistics.mean(population_times)
        population_std  = statistics.stdev(population_times)
    else:
        population_mean = 0.0
        population_std  = 1.0

    z_score = (seller_avg - population_mean) / population_std if population_std != 0 else 0.0

    if z_score < -2:   population_label="Highly Abnormal"; population_score=35
    elif z_score < -1: population_label="Unusual";         population_score=15
    else:              population_label="Normal";           population_score=0

    # ── Layer C — Task Type Validity (uses normalized type) ───────
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

    if final_behavior_risk_score >= 70:   repetitive_behavior_flag=True;  overall_behavior_label="Highly Suspicious"
    elif final_behavior_risk_score >= 30: repetitive_behavior_flag=True;  overall_behavior_label="Moderately Suspicious"
    else:                                 repetitive_behavior_flag=False; overall_behavior_label="Normal"

    return {
        "layer_a": {
            "completion_times":         completion_times,
            "std_dev":                  round(std_dev, 2),   # ← always float now
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

    all_logs = SellerBehaviorLog.objects.all().values(
        "task_id", "seller_id", "ip_address", "device_id", "user_agent"
    )
    all_sellers = [{
        "taskId":    str(log["task_id"]),
        "sellerId":  str(log["seller_id"]),
        "ipAddress": log["ip_address"] or "",
        "deviceId":  log["device_id"]  or "",
        "userAgent": log["user_agent"] or "",
    } for log in all_logs]

    # Layer A — Device Sharing
    device_sellers = {str(seller_id)}
    for s in all_sellers:
        if s["deviceId"] == device_id and device_id:
            device_sellers.add(s["sellerId"])
    device_seller_count = len(device_sellers)

    if device_seller_count == 1:   device_sharing_label="Safe";              device_sharing_score=0
    elif device_seller_count == 2: device_sharing_label="Suspicious";        device_sharing_score=30
    else:                          device_sharing_label="Highly Suspicious"; device_sharing_score=70

    # Layer B — IP Reuse
    ip_sellers = {str(seller_id)}
    for s in all_sellers:
        if s["ipAddress"] == ip_address and ip_address:
            ip_sellers.add(s["sellerId"])
    ip_seller_count = len(ip_sellers)

    if ip_seller_count <= 2:   ip_reuse_label="Normal";             ip_reuse_score=0
    elif ip_seller_count <= 5: ip_reuse_label="Suspicious";         ip_reuse_score=15
    else:                      ip_reuse_label="Highly Suspicious";  ip_reuse_score=35

    # Layer C — Bot Detection
    bot_keywords      = ["headless","selenium","phantomjs","puppeteer","python-requests","scrapy","bot"]
    detected_keywords = [kw for kw in bot_keywords if kw.lower() in user_agent.lower()]
    automation_score  = 70 if detected_keywords else 0
    automation_label  = "Automation Detected" if detected_keywords else "Normal"

    device_risk_score = min(device_sharing_score + ip_reuse_score + automation_score, 100)

    if device_risk_score >= 70:   overall_device_label="Highly Suspicious";     device_fraud_flag=True
    elif device_risk_score >= 30: overall_device_label="Moderately Suspicious"; device_fraud_flag=True
    else:                         overall_device_label="Normal";                device_fraud_flag=False

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
        }
    }


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
        "fraud_reasons":      suspicious_signals if prediction == 1 else [],
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
        "layer_a": {"completion_times": completion_times, "std_dev": round(std_dev,2), "timing_consistency_label": timing_consistency_label, "timing_consistency_score": timing_consistency_score},
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

    task_type = task.taskType
    _task_type_map = {
    "like":"Like","likes":"Like",
    "follow":"Follow","follows":"Follow",
    "comment":"Comment","comments":"Comment",
    "subscribe":"Subscribe","subscribes":"Subscribe",
    }
    task_type = _task_type_map.get(task_type.lower(), task_type)
    # 3. Seller info
    seller_type_label, seller_type_encoded, seller_age_days = get_seller_type(seller_profile)

    total_completed_tasks = JobsHistory.objects.filter(
        seller=seller_profile, status="approved"
    ).count()

    seller_trust_score = float(getattr(seller_profile, "trust_score", 50) or 50)

    # 4. Layer 1 — check duplicate from DB
    current_job = (
        JobsHistory.objects
        .filter(task=task, seller=seller_profile, status="pending")
        .order_by("-startDate")
        .first()
    )

    is_duplicate_screenshot = 0
    if current_job and current_job.proofSha256:
        duplicate_exists = (
            JobsHistory.objects
            .filter(proofSha256=current_job.proofSha256)
            .exclude(id=current_job.id)
            .exists()
        )
        is_duplicate_screenshot = 1 if duplicate_exists else 0

    layer1_result = {
        "is_duplicate_screenshot": is_duplicate_screenshot,
        "message": "Duplicate detected" if is_duplicate_screenshot else "No duplicate found",
    }

    # 5. Layer 2 Module 1 — Timing
    timing_result = _run_timing_analysis(task_id, task_type, completion_time)

    # 6. Layer 2 Module 2 — Repetitive Behavior
    behavior_result = _run_repetitive_behavior(task_id, seller_id, task_type, completion_time)

    # 7. Save BehaviorLog then run Module 3
    # ── fix: always create new log, never skip ──
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
        # ── fix: removed device_fraud_flag and automation_score
        #    they were not in training features ──
    }

    # 9. Layer 3 — ML Prediction
    layer3_result = _run_ml_prediction(layer3_input)

    # 10. Full response
    return JsonResponse({
        "sellerInfo": {
            "sellerId":            str(seller_id),
            "sellerType":          seller_type_label,
            "sellerAgeDays":       seller_age_days,
            "trustScore":          seller_trust_score,
            "totalCompletedTasks": total_completed_tasks,
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
    }, status=200)
