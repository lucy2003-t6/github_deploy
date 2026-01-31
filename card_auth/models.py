from django.db import models
import uuid
from django.utils import timezone

class VolunteerAccount(models.Model):
    """
    Stores the REAL credentials for the target platform (e.g., Suzhou Volunteer Platform).
    """
    name = models.CharField(max_length=100, help_text="User's Name (e.g., Zhang San)")
    platform_username = models.CharField(max_length=100, help_text="Login Username")
    platform_password = models.CharField(max_length=100, help_text="Login Password")
    
    def __str__(self):
        return f"{self.name} ({self.platform_username})"

class AccessCard(models.Model):
    """
    The 'Card Key' distributed to students.
    """
    code = models.CharField(max_length=50, default=uuid.uuid4, unique=True, help_text="The secret key string")
    linked_account = models.ForeignKey(VolunteerAccount, on_delete=models.CASCADE, related_name='cards')
    is_active = models.BooleanField(default=True)
    expiry_time = models.DateTimeField(null=True, blank=True, help_text="Optional expiry time")
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        if not self.is_active:
            return False
        if self.expiry_time and timezone.now() > self.expiry_time:
            return False
        return True

    def __str__(self):
        return f"Card {self.code[:8]}... -> {self.linked_account.name}"
