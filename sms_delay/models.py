from django.db import models
from mysite.settings import TIME_ZONE
from django.utils import timezone as utils_timezone


class SMSLog(models.Model):
    text = models.TextField()
    user_id = models.IntegerField()
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.date.astimezone(utils_timezone.pytz.timezone(TIME_ZONE)))
