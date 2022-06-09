# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import CustomGroup, CustomGroupUser, Dashboard, BiasAuth, BiasLog, UploadLog, KBLog, UsersId


class UserKBLog(admin.ModelAdmin):
    readonly_fields = ("date", "user_id", "text")

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(KBLog, UserKBLog)


class UserBiasLog(admin.ModelAdmin):
    readonly_fields = ("date", "user_id", "text")

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(BiasLog, UserBiasLog)


class UserUploadLog(admin.ModelAdmin):
    readonly_fields = ("date", "user_id", "text")

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(UploadLog, UserUploadLog)

admin.site.register(CustomGroup)

admin.site.register(CustomGroupUser)

admin.site.register(Dashboard)


class BiasAuthInline(admin.StackedInline):
    model = BiasAuth
    can_delete = True
    verbose_name_plural = 'Биас'


class UsersIdInline(admin.StackedInline):
    model = UsersId
    can_delete = True
    verbose_name_plural = 'users_id'


class UserAdmin(BaseUserAdmin):
    inlines = (BiasAuthInline, UsersIdInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)

