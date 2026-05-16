from rest_framework.decorators import api_view
from rest_framework.response import Response
import pandas as pd
from django.conf import settings
from .models import JobAllocationModel

model = None


def get_job_allocation_model():
    global model

    if model is None:
        model = JobAllocationModel()
        training_df = pd.read_excel(settings.BASE_DIR / "sellers_dataset_500.xlsx")
        model.train(training_df)

    return model


@api_view(['POST'])
def allocate_jobs(request):
    try:
        sellers = request.data.get('sellers')
        total_jobs = request.data.get('total_jobs', 20)

        if not sellers:
            return Response({"error": "No sellers data provided"})

        result = get_job_allocation_model().predict_from_input(sellers, total_jobs)

        return Response({
            "status": "success",
            "job_allocation": result
        })

    except Exception as e:
        return Response({"error": str(e)})
