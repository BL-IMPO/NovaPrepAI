from django.contrib import admin

from users.models import UserProfile, ContactUs
from main.models import TestAttempt, ChatMessage


# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nickname', 'subscribe_newsletter')
    search_fields = ('user__username', 'nickname')

@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'test_type', 'score', 'weighted_score', 'passed')
    list_filter = ('passed', 'test_type')
    search_fields = ('user__username',)

@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('nickname', 'email', 'theme', 'message')
    search_fields = ('name', 'name')
