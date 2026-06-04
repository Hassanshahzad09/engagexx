from rest_framework.decorators import api_view
from rest_framework.response import Response
import pandas as pd
from django.conf import settings
from .models import JobAllocationModel


# -----------------------------------------------
# Singleton model — trained once at first request
# -----------------------------------------------
_model_instance = None
DATASET_PATH = settings.BASE_DIR / "sellers_dataset_500.xlsx"


def get_job_allocation_model() -> JobAllocationModel:
    global _model_instance

    if _model_instance is None:
        print("[ML] Training model for the first time...")
        _model_instance = JobAllocationModel()
        training_df = pd.read_excel(DATASET_PATH)
        _model_instance.train(training_df, dataset_path=str(DATASET_PATH))
        print("[ML] Model ready.")

    return _model_instance


# -----------------------------------------------
# POST /ml/allocate-jobs/
# Body: { sellers: [...], total_jobs: int }
# -----------------------------------------------
@api_view(['POST'])
def allocate_jobs(request):
    """
    Accepts sellers list and total_jobs.
    Returns proportional job allocation per rating group.

    Edge cases handled:
    - 0 sellers          → returns {}
    - 1 seller, 200 jobs → all 200 go to that seller's rating group
    - New sellers (no history) → uses safe defaults
    - total_jobs = 0     → returns {}
    - total_jobs as string/Decimal/float → safely converted
    """
    try:
        sellers = request.data.get('sellers', [])
        total_jobs = request.data.get('total_jobs', 0)

        if not sellers:
            return Response({"error": "No sellers provided"}, status=400)

        # Fix: handle string, Decimal, float all at once
        try:
            total_jobs = int(float(total_jobs))
        except (TypeError, ValueError):
            return Response({"error": "total_jobs must be a positive integer"}, status=400)

        if total_jobs <= 0:
            return Response({"error": "total_jobs must be a positive integer"}, status=400)

        allocation = get_job_allocation_model().predict_from_input(sellers, total_jobs)

        return Response({
            "status": "success",
            "job_allocation": allocation
        })

    except Exception as e:
        print(f"[ML ERROR] allocate_jobs: {e}")
        return Response({"error": str(e)}, status=500)

# -----------------------------------------------
# POST /ml/log-seller-data/
# Body: { sellers: [...] }   (after task completion)
# -----------------------------------------------
@api_view(['POST'])
def log_seller_data(request):
    """
    Append updated seller performance data to the training Excel file.
    Call this after sellers complete jobs so the dataset stays fresh.
    Does NOT retrain — call /ml/retrain/ separately when needed.
    """
    try:
        new_sellers = request.data.get('sellers', [])
        if not new_sellers:
            return Response({"error": "No seller data provided"}, status=400)

        get_job_allocation_model().log_new_data(new_sellers, dataset_path=str(DATASET_PATH))

        return Response({"status": "Data logged successfully"})

    except Exception as e:
        print(f"[ML ERROR] log_seller_data: {e}")
        return Response({"error": str(e)}, status=500)


# -----------------------------------------------
# POST /ml/retrain/
# Triggers a full retrain from the updated Excel
# -----------------------------------------------
@api_view(['POST'])
def retrain_model(request):
    """
    Force retrain the model from the current dataset.
    Call this periodically (e.g., after 50+ new rows logged).
    """
    global _model_instance

    try:
        print("[ML] Retraining triggered...")
        _model_instance = JobAllocationModel()
        training_df = pd.read_excel(DATASET_PATH)
        _model_instance.train(training_df, dataset_path=str(DATASET_PATH))

        return Response({"status": "Model retrained successfully"})

    except Exception as e:
        print(f"[ML ERROR] retrain_model: {e}")
        return Response({"error": str(e)}, status=500)