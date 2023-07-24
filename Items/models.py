
from django.db import models
from django.urls import reverse
from django.utils import timezone


class items(models.Model):
    id = models.IntegerField(max_length=64, )
    name = models.CharField(max_length=200, )
    description = models.CharField(max_length=200, )
    price = models.DecimalField(max_length=10, decimal_places=2, )
    target_inv = models.IntegerField(max_length=32, )
    current_inv = models.IntegerField(max_length=32, )
    reorder_level = models.IntegerField(max_length=32, )


