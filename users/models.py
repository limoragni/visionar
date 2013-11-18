from django.db import models
from django.contrib.auth.models import User

class External(models.Model):
	user = models.OneToOneField(User)
	phone = models.CharField(max_length=100)
	company = models.CharField(max_length=100)