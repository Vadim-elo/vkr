# -*- coding: utf-8 -*-
from cryptography.fernet import Fernet
from django.contrib.auth.models import User, UserManager
from django.db import models

from mysite.settings import CIPHER_KEY


class CustomUser(User):
    objects = UserManager()

    class Meta:
        permissions = (
            ('kb', 'kb'),
            ('graphs', 'graphs'),
            ('upload', 'upload'),
            ('vk', 'vk'),
            ('comparing', 'comparing'),
            ('admin', 'admin'),
            ('admin_all', 'admin_all'),
            ('admin_collection', 'admin_collection'),
            ('dashboards', 'dashboards'),
            ('bias', 'bias'),
            ('sms', 'sms'),
            ('call_schedule', 'call_schedule')
        )


class CustomGroup(models.Model):
    group = models.CharField(max_length=200)
    admin_id = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.group


class CustomGroupUser(models.Model):
    group_id = models.IntegerField()
    user_id = models.IntegerField()
    admin_id = models.IntegerField()
    datebeg = models.DateTimeField(auto_now=True)
    dateend = models.DateTimeField(default=None)


class Dashboard(models.Model):
    name = models.CharField(max_length=300)
    link = models.TextField()
    group_id = models.IntegerField()

    def __str__(self):
        return self.name


class UsersId(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    users_id = models.CharField(max_length=3000, blank=True, editable=True)

    def __str__(self):
        return 'users_id'


class BiasAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    login = models.CharField(max_length=3000, blank=True)
    password = models.CharField(max_length=3000, blank=True)

    def __str__(self):
        return 'Авторизация'

    def save(self, *args, **kwargs):
        cipher_key = CIPHER_KEY
        cipher = Fernet(cipher_key)
        encrypted_text = cipher.encrypt(bytes(self.password, encoding='utf8'))
        self.password = encrypted_text
        super(BiasAuth, self).save(*args, **kwargs)


class BiasLog(models.Model):
    text = models.TextField()
    user_id = models.IntegerField()
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text


class KBLog(models.Model):
    text = models.TextField()
    user_id = models.IntegerField()
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text


class UploadLog(models.Model):
    text = models.TextField()
    user_id = models.IntegerField()
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text


class CollectorsOlap(models.Model):
    name = models.TextField()
    surname = models.TextField()
    users_id = models.TextField()

    def __str__(self):
        return self.users_id
