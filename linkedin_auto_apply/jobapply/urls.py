from django.urls import path
from .views import apply_linkedin_job

urlpatterns = [
    path('apply/', apply_linkedin_job, name='apply_jobs'),
]
