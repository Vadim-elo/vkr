from django.urls import path

from . import views
from sigma import views as sigma_views
from vk_app import views as vk_views
from face_verifier import views as face_views
from sms_delay import views as sms_views
from call_schedule import views as call_schedule_views

urlpatterns = [
    path('', views.index, name=''),
    path('process-control/', views.redirect_view, name='admin_ref'),
    path('management/', views.management, name='management'),
    path('graphs/node_info', sigma_views.node_info, name='graphs_info'),
    path('graphs/', sigma_views.search, name='graphs'),
    path('upload/', views.upload, name='upload'),
    path('upload/payments/', views.upload_payments, name='upload_payments'),
    path('upload/payments/type1/', views.upload_payments_first, name='upload_payments_first'),
    path('upload/payments/type2/', views.upload_payments_second, name='upload_payments_second'),
    path('upload/moneta/', views.upload_moneta, name='upload_moneta'),
    path('upload/portfolio/', views.upload_portfolio, name='upload_portfolio'),
    path('mailings/',  views.mailings, name='mailings'),
    path('db_search/',  views.db_search, name='db_search'),
    path('vk/', vk_views.vk, name='vk'),
    path('vk/user_photos/',  vk_views.user_photos, name='user_photos'),
    path('vk/friends/', vk_views.vk_friends, name ='vk_friends'),
    path('vk/find_by_photo', face_views.findclone, name='find_by_photo'),
    path('api-admin/',  views.cash_u_api, name='api-admin'),
    path('comparing/',  face_views.face_cut, name='face_cut'),
    path('dashboards/',  views.dashboards, name='dashboards'),
    path('bias/',  views.bias, name='bias'),
    path('bias/profile/',  views.bias_profile, name='bias_profile'),
    path('upload/receipts/',  views.receipts, name='receipts'),
    path('sms/',  sms_views.sms, name='sms'),
    path('call_schedule/',  call_schedule_views.delays, name='call_schedule'),
    path('confirmation/',  views.confirmation, name='confirmation'),
]

# path('vk/info/',  vk_views.search, name='vk_graphs'), # TODO визуализация графика друзей по id - не работает
