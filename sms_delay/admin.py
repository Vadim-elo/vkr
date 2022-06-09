# -*- coding: utf-8 -*-

from django.contrib import admin

from sms_delay.models import SMSLog


class UserSMSLog(admin.ModelAdmin):
    readonly_fields = ("date", "user_id", "text")

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(SMSLog, UserSMSLog)
