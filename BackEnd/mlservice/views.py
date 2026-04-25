from rest_framework.decorators import api_view
from rest_framework.response import Response
import pandas as pd
from .models import JobAllocationModel

# Load model once
model = JobAllocationModel()

# Train model ONCE when server starts
training_df = pd.read_excel("sellers_dataset_500.xlsx")
model.train(training_df)


@api_view(['POST'])
def allocate_jobs(request):
    try:
        sellers = request.data.get('sellers')
        total_jobs = request.data.get('total_jobs', 20)

        if not sellers:
            return Response({"error": "No sellers data provided"})

        result = model.predict_from_input(sellers, total_jobs)

        return Response({
            "status": "success",
            "job_allocation": result
        })

    except Exception as e:
        return Response({"error": str(e)})