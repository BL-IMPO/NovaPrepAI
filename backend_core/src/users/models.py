from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    subscribe_newsletter = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} Profile"


class ContactUs(models.Model):
    nickname = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=False)
    theme = models.CharField(max_length=200)
    message = models.TextField()

    def __str__(self):
        return f"{self.nickname} Message"
