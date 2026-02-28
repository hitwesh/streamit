import re
import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
    def _generate_unique_username(self, base: str | None) -> str:
        raw_base = (base or "user").strip().lower()
        cleaned = re.sub(r"[^a-z0-9_]+", "", raw_base)
        seed = cleaned or "user"

        candidate = seed
        while self.model.objects.filter(username__iexact=candidate).exists():
            candidate = f"{seed}{uuid.uuid4().hex[:4]}"

        return candidate

    def create_user(
        self,
        email=None,
        password=None,
        display_name=None,
        is_guest=False,
        username=None,
    ):
        if not is_guest and not email:
            raise ValueError("Email is required for non-guest users")

        if not username:
            base = None
            if email:
                base = email.split("@", 1)[0]
            elif display_name:
                base = display_name
            username = self._generate_unique_username(base)

        user = self.model(
            email=self.normalize_email(email) if email else None,
            username=username,
            display_name=display_name,
            is_guest=is_guest,
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(
            email=email,
            password=password,
            display_name="Admin",
            is_guest=False,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True, null=True, blank=True)
    username = models.CharField(max_length=30, unique=True, null=True, blank=True)
    display_name = models.CharField(max_length=50)

    is_guest = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def clean(self):
        super().clean()
        if not self.username:
            return

        conflict = (
            User.objects
            .filter(username__iexact=self.username)
            .exclude(pk=self.pk)
            .exists()
        )
        if conflict:
            raise ValidationError("Username already taken.")

    def __str__(self):
        return self.display_name
