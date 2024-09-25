from django.urls import path
from .views import Predict

urlpatterns = [
    path('predict/', Predict.as_view(), name='predict'),
]
