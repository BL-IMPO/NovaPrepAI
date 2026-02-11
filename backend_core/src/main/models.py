from django.db import models
from django.conf import settings


class TestAttempt(models.Model):
    # Link to the user whi took the test
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    test_type = models.CharField(max_length=50) # e.g. "math 1" "full test"

    score = models.IntegerField()
    passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    details = models.JSONField(default=list)

    def __str__(self):
        return f"{self.user} - {self.test_type} - {self.score}"

    class Meta:
        ordering = ['-created_at']
        app_label = 'main'


