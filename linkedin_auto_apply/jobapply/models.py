from django.db import models

class AppliedJob(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    job_title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    job_url = models.URLField(unique=True)

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"
