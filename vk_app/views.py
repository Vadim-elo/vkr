# coding: utf8
import pandas
from actstream import action
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render

from vk_app.scripts.vk import vk_main, df_user_photos, friends_result


@permission_required('website.some')
@login_required(login_url='/login/')
def search(request):
    path = vk_main()
    return render(request, 'vk_graphs.html', {'filepath': path})


@permission_required('website.some')
@login_required(login_url='/login/')
def node_info(request):
    node_id = request.POST.get('node_id')
    # response = GetInfo(node_id)
    # return HttpResponse(response)


@permission_required('website.vk')
@login_required(login_url='/login/')
def user_photos(request):
    if request.method == "POST" and request.POST.get('user_id'):
        action.send(request.user, verb='Поиск VK - Отметки на фото - поиск')
        result = df_user_photos(request.POST.get('user_id'))
        return render(request, 'user_photos.html', {'df': result[0].iterrows(), 'message': result[1]})
    else:
        action.send(request.user, verb='переход в Поиск VK - Отметки на фото')
        return render(request, 'user_photos.html')


@permission_required('website.vk')
@login_required(login_url='/login/')
def vk(request):
    action.send(request.user, verb='переход в Поиск VK')
    return render(request, 'vk.html')


@permission_required('website.vk')
@login_required(login_url='/login/')
def vk_friends(request):
    if request.method == "POST" and request.POST.get('target_user'):
        action.send(request.user, verb='Поиск VK - Общие друзья - поиск')
        vk_tuple = friends_result(request.POST.get('target_user'))

        df = pandas.DataFrame()
        target_user = ''
        target_link = ''

        if type(vk_tuple[0]) == str:
            return render(request, 'friends.html', {'target_link': target_link,
                                                    'target_user': target_user,
                                                    'df_friends': df.iterrows(),
                                                    'entered_target': request.POST.get('target_user'),
                                                    'error': 'true'})

        try:
            df = vk_tuple[0]
            target_user = vk_tuple[1]
            target_link = vk_tuple[2]
        except:
            pass

        return render(request, 'friends.html', {'target_link': target_link,
                                                'target_user': target_user,
                                                'df_friends': df.iterrows(),
                                                'entered_target': request.POST.get('target_user')})
    else:
        action.send(request.user, verb='переход в Поиск VK - Общие друзья')
        return render(request, 'friends.html')
