import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from core.utils import generate_referral_code


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, blank=True)
    referral_code = models.CharField(max_length=16, unique=True, blank=True)
    referred_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='referrals'
    )
    is_blocked = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['referral_code']),
            models.Index(fields=['username']),
        ]

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self._generate_unique_code()
        super().save(*args, **kwargs)

    def _generate_unique_code(self):
        while True:
            code = generate_referral_code()
            if not User.objects.filter(referral_code=code).exists():
                return code

    def __str__(self):
        return self.username

    @property
    def display_name(self):
        return self.get_full_name() or self.username
