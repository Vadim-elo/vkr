from abc import ABC

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Subquery


class ArrayFormat(Subquery, ABC):
    template = 'ARRAY(%(subquery)s)'
    output_field = ArrayField(base_field=models.IntegerField())


class History(models.Model):
    weekday = models.IntegerField()
    termdelay = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.weekday
