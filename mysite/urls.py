from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from mysite import settings, views

auth_views.PasswordResetView.template_name = 'registration/custom_reset_form.html'
auth_views.PasswordResetDoneView.template_name = 'registration/custom_password_reset_done.html'
auth_views.PasswordResetConfirmView.template_name = 'registration/custom_password_reset_confirm.html'
auth_views.PasswordResetCompleteView.template_name = 'registration/custom_password_reset_complete.html'
auth_views.PasswordChangeView.template_name = 'registration/custom_password_change_form.html'
auth_views.PasswordChangeDoneView.template_name = 'registration/custom_password_change_done.html'

admin.site.site_header = 'Администрирование'
admin.site.site_title = 'Администрирование'
admin.site.index_title = 'Администрирование'

urlpatterns = [
    path('', views.redirect_view, name='index_start'),
    path('profile/', include('website.urls'), name='index'),
    path('process-control/', admin.site.urls),
    path('', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = views.handler404
handler500 = views.handler500
