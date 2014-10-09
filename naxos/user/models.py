from django.db import models
from django.contrib.auth.models import AbstractUser


class ForumUser(AbstractUser):
    emailVisible = models.BooleanField(default=False)
    subscribeToEmails = models.BooleanField(default=True)
    mpPopupNotif = models.BooleanField(default=True)
    mpEmailNotif = models.BooleanField(default=False)
    avatar = models.ImageField(blank=True)
    quote = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
