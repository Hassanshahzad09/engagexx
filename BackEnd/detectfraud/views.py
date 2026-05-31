from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import statistics

from django.conf import settings

@csrf_exempt
def suspiciousTimingAnalysis(request):

    if request.method != "POST":
        return JsonResponse({
            "error": "Only POST method allowed"
        }, status=405)

    try:
        data = json.loads(request.body)

        task_id = data.get("taskId")
        task_type = data.get("taskType")
        completion_time = float(data.get("completionTime"))

    except Exception as e:
        return JsonResponse({
            "error": "Invalid request data",
            "details": str(e)
        }, status=400)

    # Default values
    timing_classification = "Unknown"
    suspicious_timing_flag = False
    timing_risk_score = 0

    # -------------------------------
    # LIKE TASK ANALYSIS
    # -------------------------------
    if task_type == "Like":

        if completion_time <= 3:
            timing_classification = "Highly Suspicious"
            suspicious_timing_flag = True
            timing_risk_score = 35

        elif 3.1 <= completion_time <= 8:
            timing_classification = "Suspicious"
            suspicious_timing_flag = True
            timing_risk_score = 20

        elif 8.1 <= completion_time <= 25:
            timing_classification = "Normal"
            suspicious_timing_flag = False
            timing_risk_score = 5

        elif 25.1 <= completion_time <= 60:
            timing_classification = "Safe"
            suspicious_timing_flag = False
            timing_risk_score = 0

        else:
            timing_classification = "Very Slow"
            suspicious_timing_flag = False
            timing_risk_score = 0

    # -------------------------------
    # FOLLOW TASK ANALYSIS
    # -------------------------------
    elif task_type == "Follow":

        if completion_time <= 5:
            timing_classification = "Highly Suspicious"
            suspicious_timing_flag = True
            timing_risk_score = 35

        elif 5.1 <= completion_time <= 12:
            timing_classification = "Suspicious"
            suspicious_timing_flag = True
            timing_risk_score = 20

        elif 12.1 <= completion_time <= 40:
            timing_classification = "Normal"
            suspicious_timing_flag = False
            timing_risk_score = 5

        elif 40.1 <= completion_time <= 90:
            timing_classification = "Safe"
            suspicious_timing_flag = False
            timing_risk_score = 0

        else:
            timing_classification = "Very Slow"
            suspicious_timing_flag = False
            timing_risk_score = 0

    # -------------------------------
    # COMMENT TASK ANALYSIS
    # -------------------------------
    elif task_type == "Comment":

        if completion_time <= 10:
            timing_classification = "Highly Suspicious"
            suspicious_timing_flag = True
            timing_risk_score = 35

        elif 10.1 <= completion_time <= 20:
            timing_classification = "Suspicious"
            suspicious_timing_flag = True
            timing_risk_score = 20

        elif 20.1 <= completion_time <= 90:
            timing_classification = "Normal"
            suspicious_timing_flag = False
            timing_risk_score = 5

        elif 90.1 <= completion_time <= 180:
            timing_classification = "Safe"
            suspicious_timing_flag = False
            timing_risk_score = 0

        else:
            timing_classification = "Very Slow"
            suspicious_timing_flag = False
            timing_risk_score = 0

    # -------------------------------
    # SUBSCRIBE TASK ANALYSIS
    # -------------------------------
    elif task_type == "Subscribe":

        if completion_time <= 5:
            timing_classification = "Highly Suspicious"
            suspicious_timing_flag = True
            timing_risk_score = 35

        elif 5.1 <= completion_time <= 12:
            timing_classification = "Suspicious"
            suspicious_timing_flag = True
            timing_risk_score = 20

        elif 12.1 <= completion_time <= 35:
            timing_classification = "Normal"
            suspicious_timing_flag = False
            timing_risk_score = 5

        elif 35.1 <= completion_time <= 80:
            timing_classification = "Safe"
            suspicious_timing_flag = False
            timing_risk_score = 0

        else:
            timing_classification = "Very Slow"
            suspicious_timing_flag = False
            timing_risk_score = 0

    else:
        return JsonResponse({
            "error": "Invalid task type"
        }, status=400)

    # -----------------------------------
    # FINAL JSON RESPONSE FOR ML MODEL
    # -----------------------------------

    response_data = {
        "task_id": task_id,
        "task_type": task_type,
        "completion_duration": completion_time,
        "timing_classification": timing_classification,
        "suspicious_timing_flag": suspicious_timing_flag,
        "timing_risk_score": timing_risk_score
    }

    return JsonResponse(response_data, status=200)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import statistics


@csrf_exempt
def analyzeRepetitiveBehavior(request):

    if request.method != "POST":
        return JsonResponse({
            "error": "Only POST method allowed"
        }, status=405)

    try:
        data = json.loads(request.body)

        # ---------------------------------------------------
        # CURRENT TASK DATA
        # ---------------------------------------------------
        currentTask = data[0]

        task_id = currentTask["taskId"]
        seller_id = currentTask["sellerId"]
        task_type = currentTask["taskType"]
        current_completion_time = float(currentTask["completionTime"])

        # ---------------------------------------------------
        # PREVIOUS TASKS OF CURRENT SELLER
        # ---------------------------------------------------
        previous_tasks = data[1]["previousTasks"]

        # ---------------------------------------------------
        # GLOBAL SELLERS HISTORY
        # ---------------------------------------------------
        sellersHistory = data[2]["sellerHistory"]

        # ---------------------------------------------------
        # STORE PREVIOUS TASKS
        # ---------------------------------------------------
        tasks_list = []

        for task in previous_tasks:

            task_data = {
                "taskId": task.get("taskId"),
                "sellerId": task.get("sellerId"),
                "taskType": task.get("taskType"),
                "completionTime": float(task.get("completionTime", 0))
            }

            tasks_list.append(task_data)

        # ---------------------------------------------------
        # STORE GLOBAL SELLERS HISTORY
        # ---------------------------------------------------
        allSellers = []

        for seller in sellersHistory:

            seller_data = {
                "taskId": seller.get("taskId"),
                "sellerId": seller.get("sellerId"),
                "taskType": seller.get("taskType"),
                "completionTime": float(seller.get("completionTime", 0))
            }

            allSellers.append(seller_data)

    except Exception as e:

        return JsonResponse({
            "error": "Invalid request data",
            "details": str(e)
        }, status=400)

    # =====================================================
    # MODULE 2 - LAYER A
    # TIMING CONSISTENCY ANALYSIS
    # =====================================================

    completion_times = []

    # Current seller + same task type only
    for task in tasks_list:

        if (
            task["sellerId"] == seller_id and
            task["taskType"] == task_type
        ):
            completion_times.append(task["completionTime"])

    # Include current task timing
    completion_times.append(current_completion_time)

    # Safety check
    if len(completion_times) > 1:
        std_dev = statistics.stdev(completion_times)
    else:
        std_dev = 0

    timing_consistency_label = "Unknown"
    timing_consistency_score = 0

    if std_dev < 2:

        timing_consistency_label = "Highly Repetitive"
        timing_consistency_score = 35

    elif std_dev < 5:

        timing_consistency_label = "Moderate"
        timing_consistency_score = 15

    else:

        timing_consistency_label = "Natural"
        timing_consistency_score = 0

    # =====================================================
    # MODULE 2 - LAYER B
    # POPULATION DEVIATION ANALYSIS
    # =====================================================

    # Seller average
    seller_avg = sum(completion_times) / len(completion_times)

    # Global same-task-type timings
    population_times = []

    for seller in allSellers:

        if seller["taskType"] == task_type:
            population_times.append(seller["completionTime"])

    # Add protection
    if len(population_times) > 1:

        population_mean = statistics.mean(population_times)
        population_std = statistics.stdev(population_times)

    else:

        population_mean = 0
        population_std = 1

    # Avoid division by zero
    if population_std == 0:
        z_score = 0
    else:
        z_score = (
            seller_avg - population_mean
        ) / population_std

    population_label = "Normal"
    population_score = 0

    if z_score < -2:

        population_label = "Highly Abnormal"
        population_score = 35

    elif z_score < -1:

        population_label = "Unusual"
        population_score = 15

    else:

        population_label = "Normal"
        population_score = 0

    # =====================================================
    # MODULE 2 - LAYER C
    # TASK TYPE VALIDITY ANALYSIS
    # =====================================================

    validity_label = "Unknown"
    validity_score = 0
    logical_behavior_flag = False

    # -----------------------------
    # LIKE TASK
    # -----------------------------
    if task_type == "Like":

        if current_completion_time <= 2:

            validity_label = "Impossible"
            validity_score = 35
            logical_behavior_flag = True

        elif current_completion_time <= 8:

            validity_label = "Suspicious"
            validity_score = 15
            logical_behavior_flag = True

        else:

            validity_label = "Realistic"
            validity_score = 0
            logical_behavior_flag = False

    # -----------------------------
    # FOLLOW TASK
    # -----------------------------
    elif task_type == "Follow":

        if current_completion_time <= 4:

            validity_label = "Impossible"
            validity_score = 35
            logical_behavior_flag = True

        elif current_completion_time <= 12:

            validity_label = "Suspicious"
            validity_score = 15
            logical_behavior_flag = True

        else:

            validity_label = "Realistic"
            validity_score = 0
            logical_behavior_flag = False

    # -----------------------------
    # COMMENT TASK
    # -----------------------------
    elif task_type == "Comment":

        if current_completion_time <= 5:

            validity_label = "Impossible"
            validity_score = 35
            logical_behavior_flag = True

        elif current_completion_time <= 15:

            validity_label = "Suspicious"
            validity_score = 15
            logical_behavior_flag = True

        else:

            validity_label = "Realistic"
            validity_score = 0
            logical_behavior_flag = False

    # -----------------------------
    # SUBSCRIBE TASK
    # -----------------------------
    elif task_type == "Subscribe":

        if current_completion_time <= 4:

            validity_label = "Impossible"
            validity_score = 35
            logical_behavior_flag = True

        elif current_completion_time <= 10:

            validity_label = "Suspicious"
            validity_score = 15
            logical_behavior_flag = True

        else:

            validity_label = "Realistic"
            validity_score = 0
            logical_behavior_flag = False

    # =====================================================
    # FINAL BEHAVIOR RISK SCORE
    # =====================================================

    final_behavior_risk_score = (
        timing_consistency_score +
        population_score +
        validity_score
    )

    # Risk classification
    if final_behavior_risk_score >= 70:

        repetitive_behavior_flag = True
        overall_behavior_label = "Highly Suspicious"

    elif final_behavior_risk_score >= 30:

        repetitive_behavior_flag = True
        overall_behavior_label = "Moderately Suspicious"

    else:

        repetitive_behavior_flag = False
        overall_behavior_label = "Normal"

    # =====================================================
    # FINAL JSON RESPONSE
    # =====================================================

    response_data = {

        "task_id": task_id,
        "seller_id": seller_id,
        "task_type": task_type,

        # -----------------------------------------
        # LAYER A
        # -----------------------------------------
        "layer_a": {

            "completion_times": completion_times,
            "std_dev": round(std_dev, 2),

            "timing_consistency_label":
                timing_consistency_label,

            "timing_consistency_score":
                timing_consistency_score
        },

        # -----------------------------------------
        # LAYER B
        # -----------------------------------------
        "layer_b": {

            "seller_average":
                round(seller_avg, 2),

            "population_mean":
                round(population_mean, 2),

            "population_std":
                round(population_std, 2),

            "z_score":
                round(z_score, 2),

            "population_label":
                population_label,

            "population_score":
                population_score
        },

        # -----------------------------------------
        # LAYER C
        # -----------------------------------------
        "layer_c": {

            "validity_label":
                validity_label,

            "validity_score":
                validity_score,

            "logical_behavior_flag":
                logical_behavior_flag
        },

        # -----------------------------------------
        # FINAL MODULE RESULT
        # -----------------------------------------
        "final_behavior_analysis": {

            "final_behavior_risk_score":
                final_behavior_risk_score,

            "overall_behavior_label":
                overall_behavior_label,

            "repetitive_behavior_flag":
                repetitive_behavior_flag
        }
    }

    return JsonResponse(response_data, status=200)    





@csrf_exempt
def detect_ip_anomalies(request):

    # =====================================================
    # ONLY ALLOW POST
    # =====================================================
    if request.method != "POST":

        return JsonResponse({
            "error": "Only POST method allowed"
        }, status=405)

    try:

        # =================================================
        # LOAD JSON DATA
        # =================================================
        data = json.loads(request.body)

        # =================================================
        # CURRENT SELLER DATA
        # =================================================
        currentSeller = data["currentSeller"]

        task_id = currentSeller["taskId"]

        seller_id = currentSeller["sellerId"]

        ip_address = currentSeller["ipAddress"]

        device_id = currentSeller["deviceId"]

        user_agent = currentSeller["userAgent"]

        # =================================================
        # ALL SELLERS HISTORY
        # =================================================
        all_sellers = data["allSellers"]

    except Exception as e:

        return JsonResponse({
            "error": "Invalid JSON data",
            "details": str(e)
        }, status=400)

    # =====================================================
    # MODULE 3 - LAYER A
    # DEVICE SHARING ANALYSIS
    # =====================================================

    # Find unique sellers using same device
    device_sellers = set()

    for seller in all_sellers:

        if seller["deviceId"] == device_id:

            device_sellers.add(
                seller["sellerId"]
            )

    # Include current seller
    device_sellers.add(seller_id)

    device_seller_count = len(device_sellers)

    # -----------------------------------------------------
    # DEVICE SHARING SCORE
    # -----------------------------------------------------
    if device_seller_count == 1:

        device_sharing_label = "Safe"

        device_sharing_score = 0

    elif device_seller_count == 2:

        device_sharing_label = "Suspicious"

        device_sharing_score = 30

    else:

        device_sharing_label = "Highly Suspicious"

        device_sharing_score = 70

    # =====================================================
    # MODULE 3 - LAYER B
    # IP REUSE ANALYSIS
    # =====================================================

    # Find unique sellers using same IP
    ip_sellers = set()

    for seller in all_sellers:

        if seller["ipAddress"] == ip_address:

            ip_sellers.add(
                seller["sellerId"]
            )

    # Include current seller
    ip_sellers.add(seller_id)

    ip_seller_count = len(ip_sellers)

    # -----------------------------------------------------
    # IP REUSE SCORE
    # -----------------------------------------------------
    if ip_seller_count <= 2:

        ip_reuse_label = "Normal"

        ip_reuse_score = 0

    elif ip_seller_count <= 5:

        ip_reuse_label = "Suspicious"

        ip_reuse_score = 15

    else:

        ip_reuse_label = "Highly Suspicious"

        ip_reuse_score = 35

    # =====================================================
    # MODULE 3 - LAYER C
    # BOT / AUTOMATION ANALYSIS
    # =====================================================

    bot_keywords = [
        "headless",
        "selenium",
        "phantomjs",
        "puppeteer",
        "python-requests",
        "scrapy",
        "bot"
    ]

    detected_keywords = []

    automation_score = 0

    automation_label = "Normal"

    for keyword in bot_keywords:

        if keyword.lower() in user_agent.lower():

            detected_keywords.append(keyword)

    # -----------------------------------------------------
    # AUTOMATION SCORE
    # -----------------------------------------------------
    if len(detected_keywords) > 0:

        automation_score = 70

        automation_label = "Automation Detected"

    # =====================================================
    # FINAL DEVICE RISK SCORE
    # =====================================================

    device_risk_score = (
        device_sharing_score +
        ip_reuse_score +
        automation_score
    )

    # Maximum score limit
    device_risk_score = min(
        device_risk_score,
        100
    )

    # =====================================================
    # FINAL DEVICE FRAUD LABEL
    # =====================================================

    if device_risk_score >= 70:

        overall_device_label = "Highly Suspicious"

        device_fraud_flag = True

    elif device_risk_score >= 30:

        overall_device_label = "Moderately Suspicious"

        device_fraud_flag = True

    else:

        overall_device_label = "Normal"

        device_fraud_flag = False

    # =====================================================
    # ML READY FEATURES
    # =====================================================

    ml_features = {

        "device_seller_count":
            device_seller_count,

        "device_sharing_score":
            device_sharing_score,

        "ip_seller_count":
            ip_seller_count,

        "ip_reuse_score":
            ip_reuse_score,

        "automation_score":
            automation_score,

        "device_risk_score":
            device_risk_score,

        "device_fraud_flag":
            int(device_fraud_flag)
    }

    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    response_data = {

        "task_id": task_id,

        "seller_id": seller_id,

        # -------------------------------------------------
        # DEVICE SHARING ANALYSIS
        # -------------------------------------------------
        "device_analysis": {

            "device_id": device_id,

            "device_seller_count":
                device_seller_count,

            "device_sellers":
                list(device_sellers),

            "device_sharing_label":
                device_sharing_label,

            "device_sharing_score":
                device_sharing_score
        },

        # -------------------------------------------------
        # IP REUSE ANALYSIS
        # -------------------------------------------------
        "ip_analysis": {

            "ip_address": ip_address,

            "ip_seller_count":
                ip_seller_count,

            "ip_sellers":
                list(ip_sellers),

            "ip_reuse_label":
                ip_reuse_label,

            "ip_reuse_score":
                ip_reuse_score
        },

        # -------------------------------------------------
        # AUTOMATION ANALYSIS
        # -------------------------------------------------
        "automation_analysis": {

            "user_agent":
                user_agent,

            "detected_keywords":
                detected_keywords,

            "automation_label":
                automation_label,

            "automation_score":
                automation_score
        },

        # -------------------------------------------------
        # FINAL DEVICE RISK ANALYSIS
        # -------------------------------------------------
        "final_device_analysis": {

            "device_risk_score":
                device_risk_score,

            "overall_device_label":
                overall_device_label,

            "device_fraud_flag":
                device_fraud_flag
        },

        # -------------------------------------------------
        # ML FEATURES
        # -------------------------------------------------
        "ml_features":
            ml_features
    }

    return JsonResponse(
        response_data,
        status=200
    )




# views.py

import os
import json
import numpy as np
import pandas as pd
import joblib
import shap

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

# =========================
# PATHS
# =========================

MODEL_PATH      = settings.BASE_DIR / "engagex_model_v3.pkl"
SELLER_ENCODER  = settings.BASE_DIR / "seller_encoder.pkl"
TASK_ENCODER    = settings.BASE_DIR / "task_encoder.pkl"
FEATURE_COLUMNS = settings.BASE_DIR / "feature_columns.pkl"
EXPLAINER_PATH  = settings.BASE_DIR / "engagex_explainer.pkl"

# =========================
# GLOBAL STATE
# =========================

explainer       = None
model           = None
le_seller       = None
le_task         = None
feature_columns = None

# =========================
# TRAIN MODEL
# =========================

def train_model():
    global model, le_seller, le_task, feature_columns, explainer

    df = pd.read_csv(settings.BASE_DIR / "engagex_dataset_v4.csv")
    df.dropna(inplace=True)

    le_seller = LabelEncoder()
    le_task   = LabelEncoder()

    df["seller_type"] = le_seller.fit_transform(df["seller_type"])
    df["task_type"]   = le_task.fit_transform(df["task_type"])

    print(f"[EngageX] seller_type mapping: {list(le_seller.classes_)}")
    print(f"[EngageX] task_type mapping:   {list(le_task.classes_)}")

    DROP_COLS = [
        "fraud_label",
        "device_risk_score",
        "final_behavior_risk_score",
        "automation_score",
    ]
    DROP_COLS = [c for c in DROP_COLS if c in df.columns]

    X = df.drop(columns=DROP_COLS)
    y = df["fraud_label"]

    feature_columns = list(X.columns)
    print(f"[EngageX] Features ({len(feature_columns)}): {feature_columns}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        min_samples_leaf=15,
        subsample=0.8,
        max_features="sqrt",
        random_state=42
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


# =========================
# LOAD MODEL
# =========================

def load_model():
    global model, le_seller, le_task, feature_columns, explainer

    # ── Check ALL 5 files including explainer ──────────────────
    all_exist = all(os.path.exists(p) for p in [
        MODEL_PATH, SELLER_ENCODER, TASK_ENCODER,
        FEATURE_COLUMNS, EXPLAINER_PATH
    ])

    if all_exist:
        model           = joblib.load(MODEL_PATH)
        le_seller       = joblib.load(SELLER_ENCODER)
        le_task         = joblib.load(TASK_ENCODER)
        feature_columns = joblib.load(FEATURE_COLUMNS)
        explainer       = joblib.load(EXPLAINER_PATH)
        print("[EngageX] Model loaded from disk")
        print(f"[EngageX] seller_type mapping: {list(le_seller.classes_)}")
        print(f"[EngageX] task_type mapping:   {list(le_task.classes_)}")
    else:
        print("[EngageX] Files missing — retraining...")
        train_model()


load_model()


# =========================
# FEATURE REASONS MAP
# =========================

FEATURE_REASONS = {
    "is_duplicate_screenshot": {
        "layer": "Layer 1 — Screenshot Check",
        "label": "Duplicate screenshot detected",
        "threshold": lambda v: v >= 1
    },
    "timing_risk_score": {
        "layer": "Layer 2 — Suspicious Timing",
        "label": "Task completed suspiciously fast",
        "threshold": lambda v: v >= 20
    },
    "completion_duration": {
        "layer": "Layer 2 — Suspicious Timing",
        "label": "Completion time is abnormally low",
        "threshold": lambda v: v <= 5
    },
    "std_dev": {
        "layer": "Layer 2 — Repetitive Behavior",
        "label": "Highly repetitive completion times (bot-like consistency)",
        "threshold": lambda v: v <= 4
    },
    "timing_consistency_score": {
        "layer": "Layer 2 — Repetitive Behavior",
        "label": "Timing consistency is suspiciously uniform",
        "threshold": lambda v: v >= 15
    },
    "repetitive_behavior_flag": {
        "layer": "Layer 2 — Repetitive Behavior",
        "label": "Repetitive behavior pattern flagged",
        "threshold": lambda v: v >= 1
    },
    "z_score": {
        "layer": "Layer 2 — Population Deviation",
        "label": "Completion time is far below population average",
        "threshold": lambda v: v <= -1.5
    },
    "population_score": {
        "layer": "Layer 2 — Population Deviation",
        "label": "Seller speed is abnormal compared to all sellers",
        "threshold": lambda v: v >= 15
    },
    "validity_score": {
        "layer": "Layer 2 — Validity Check",
        "label": "Task completion time is logically impossible",
        "threshold": lambda v: v >= 15
    },
    "logical_behavior_flag": {
        "layer": "Layer 2 — Validity Check",
        "label": "Behavior is logically inconsistent for this task",
        "threshold": lambda v: v >= 1
    },
    "device_sharing_score": {
        "layer": "Layer 2 — Device Analysis",
        "label": "Device is shared among multiple sellers",
        "threshold": lambda v: v >= 20
    },
    "ip_reuse_score": {
        "layer": "Layer 2 — IP Analysis",
        "label": "IP address reused by multiple sellers",
        "threshold": lambda v: v >= 20
    },
    "device_seller_count": {
        "layer": "Layer 2 — Device Analysis",
        "label": "Multiple seller accounts on same device",
        "threshold": lambda v: v >= 3
    },
    "ip_seller_count": {
        "layer": "Layer 2 — IP Analysis",
        "label": "Multiple seller accounts from same IP",
        "threshold": lambda v: v >= 4
    },
    "seller_trust_score": {
        "layer": "Seller Profile",
        "label": "Seller has very low trust score",
        "threshold": lambda v: v <= 35
    },
    "seller_age_days": {
        "layer": "Seller Profile",
        "label": "Account is very new",
        "threshold": lambda v: v <= 10
    },
    "total_completed_tasks": {
        "layer": "Seller Profile",
        "label": "Suspicious number of tasks for account age",
        "threshold": lambda v: v >= 200
    },
}


# =========================
# SHAP REASON EXTRACTOR
# =========================

def get_fraud_reasons(shap_values, feature_names, input_data, top_n=5):
    """
    Returns suspicious signals regardless of fraud/legit prediction.
    Shows any feature that:
      1. Has positive SHAP value (pushed towards fraud)
      2. Crossed its suspicious threshold
    """

    # Safely extract raw numpy array
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

        # Only include features pushing TOWARDS fraud
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


# =========================
# PREDICT VIEW
# =========================

@csrf_exempt
def predict_fraud(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Flatten nested input
    flat_input = {}
    for key, value in body.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, dict):
                    for k2, v2 in sub_value.items():
                        flat_input[k2] = v2
                else:
                    flat_input[sub_key] = sub_value
        else:
            flat_input[key] = value

    # Encode categoricals
    try:
        if "seller_type" in flat_input and isinstance(flat_input["seller_type"], str):
            flat_input["seller_type"] = int(le_seller.transform([flat_input["seller_type"]])[0])
        if "task_type" in flat_input and isinstance(flat_input["task_type"], str):
            flat_input["task_type"]   = int(le_task.transform([flat_input["task_type"]])[0])
    except Exception as e:
        return JsonResponse({"error": f"Encoding error: {str(e)}"}, status=400)

    # Build DataFrame
    sample_df = pd.DataFrame([flat_input])
    for col in feature_columns:
        if col not in sample_df.columns:
            sample_df[col] = 0
    sample_df = sample_df[feature_columns]

    # Predict
    raw_proba         = float(model.predict_proba(sample_df)[0][1])
    fraud_probability = round(raw_proba * 100, 2)
    prediction        = 1 if fraud_probability >= 50 else 0

    # Risk level
    if fraud_probability < 20:   risk_level = "LOW"
    elif fraud_probability < 50: risk_level = "MEDIUM"
    elif fraud_probability < 75: risk_level = "HIGH"
    else:                        risk_level = "CRITICAL"

    # =========================
    # SHAP — always run
    # Show suspicious signals even when probability < 50%
    # Admin can see what triggered even for borderline cases
    # =========================

    suspicious_signals = []

    try:
        shap_values    = explainer.shap_values(sample_df)
        suspicious_signals = get_fraud_reasons(
            shap_values=shap_values,
            feature_names=feature_columns,
            input_data=flat_input,
            top_n=5
        )
    except Exception as e:
        print(f"[EngageX] SHAP error: {str(e)}")

    return JsonResponse({
        "prediction":          "FRAUD" if prediction == 1 else "LEGITIMATE",
        "fraud_probability":   fraud_probability,
        "risk_level":          risk_level,
        "label":               prediction,

        # ── Always returned ───────────────────────────────────────
        # fraud_reasons = confirmed fraud signals (prediction == 1)
        # suspicious_signals = warning signals even if not fraud yet
        "fraud_reasons":       suspicious_signals if prediction == 1 else [],
        "suspicious_signals":  suspicious_signals,
    })