from django.db import models
from django.conf import settings


class TestAttempt(models.Model):
    """Gets data of testing process."""
    # Link to the user whi took the test
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    test_type = models.CharField(max_length=50) # e.g. "math 1" "full test"

    score = models.IntegerField()

    # Weighted max Scores
    weighted_score = models.FloatField(default=0.0)

    passed = models.BooleanField(default=False)

    mark = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    details = models.JSONField(default=list)

    def __str__(self):
        return f"{self.user} - {self.test_type} - Count: {self.score}, Points: {self.weighted_score}"

    class Meta:
        ordering = ['-created_at']
        app_label = 'main'


class ChatThread(models.Model):
    """Groups messages together for a specific task within a test attempt."""
    # Link back to the test attempt
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='chat_threads')

    # Identifies which specific question/task are asking the AI about
    task_id = models.CharField(max_length=100, help_text="ID of the specific question or task")

    created_at  = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        app_label = 'main'

    def __str__(self):
        return f"Chat for Attempt {self.attempt.id} - Task {self.task_id}"


class ChatMessage(models.Model):
    """A single message sent by either the user ot the AI."""

    ROLE_CHOICES = [
        ('system', 'System'),
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages')

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        app_label = 'main'

    def __str__(self):
        return f"{self.role.capitalize()}: {self.content[:30]}..."




