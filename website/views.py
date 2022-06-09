import datetime
import re
import time
from smtplib import SMTPException

import pandas
from actstream import action
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail
from django.shortcuts import render
from django.shortcuts import redirect
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse, HttpResponse, JsonResponse
from django.contrib.auth.models import Group, User
from django.utils.timezone import now
from secrets import choice
import string

from mysite.settings import CIPHER_KEY
from .models import CustomGroup, CustomGroupUser, Dashboard, BiasLog, KBLog, CollectorsOlap, UsersId
from .scripts import upload_type1, upload_type2, check_moneta, portfolio_checkup, kb_script, cashu_api_admin, \
    admin_users, bias_script, atol_online

from .scripts.Рассылки import auxiliary_func_delay
from cryptography.fernet import Fernet


@login_required(login_url='/login/')
def index(request):
    request.session.set_expiry(0)
    return render(request, 'index.html')


@permission_required('website.some')
@login_required(login_url='/login/')
def redirect_view(request):
    return redirect('/process-control')


@permission_required('website.admin')
@login_required(login_url='/login/')
def confirmation(request):
    """
    Отвечает за блок Подтверждение пользователей

    при обновлении таблицы collectors на базе olap рабатывает триггер и новые сотрудники,
    добавленные в спутник добавляются в модель CollectorsOlap

    в данном блоке есть возможность подтвердить добавление сотрудника заполнив недостоющие поля,
    либо исключить запись о возможном сотруднике, удалив ее

    теперь сотрудники вносятся автоматически и указывается users_id сотрудника
    """

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # TODO deprecated since 3.1 if request.is_ajax():
        if request.POST.get("name", None):
            name = request.POST.get("name", None)
            surname = request.POST.get("surname", None)
            email_search = re.search("([^@|\s]+@[^@]+\.[^@|\s]+)", request.POST.get("email", None), re.I)
            if email_search:
                email = email_search.string.replace(' ', '')
            else:
                email = ''

            selected_dep = request.POST.get("selected_dep", None)
            selected_gr = request.POST.get("selected_gr", None)
            password = ''.join([choice(string.ascii_uppercase + string.digits) for _ in range(12)])

            confirm_id = request.POST.get("id", None)

            if email and selected_gr != 'Выбрать:' and selected_dep != 'Выбрать:':
                try:
                    User.objects.get(username=email)
                except User.DoesNotExist:
                    user = User.objects.create_user(
                        username=email,
                        first_name=name.title().replace(' ', ''),
                        last_name=surname.title().replace(' ', ''),
                        email=email,
                        password=password.replace(' ', '')
                    )
                    group = Group.objects.get(name=selected_dep.title())
                    group.user_set.add(user)

                    CustomGroupUser(
                        group_id=CustomGroup.objects.get(group=selected_gr, is_active=True).id,
                        user_id=user.id,
                        admin_id=request.user.id
                    ).save()

                    UsersId(user=user, users_id=request.POST.get("users_id", None)).save()
                    CollectorsOlap.objects.get(id=confirm_id).delete()
                    admin_users.update_collectors()

                    try:
                        send_mail(
                            'Доступ к some.host',
                            'Вы получили это письмо, потому что для вас была создана учетная запись'
                            ' в https://127.0.0.1/ . Для того, чтобы получить доступ к сервису перейдите по ссылке'
                            ' https://127.0.0.1/ и следуйте инструкциям.',
                            '',
                            [email],
                            fail_silently=False,
                        )
                        return HttpResponse(
                            f'Пользователь {name} {surname} успешно добавлен! '
                            f'На указанный email выслана инструкция для авторизации.'
                        )
                    except SMTPException:
                        return HttpResponse(
                            f'Пользователь {name} {surname} успешно добавлен, но уведомить его невозможно! '
                            f'Сотруднику необходимо перейти по ссылке https://127.0.0.1/password_reset/ '
                            f'для получения доступа.',
                            status=400
                        )
            elif not email:
                return HttpResponse('Неверно заполнено поле email!', status=400)
            elif selected_dep == 'Выбрать:':
                return HttpResponse('Ошибка! Не выбран отдел пользователя.', status=400)
            elif selected_gr == 'Выбрать:':
                return HttpResponse('Ошибка! Не небрана группа пользователя!', status=400)
        if request.POST.get("declain_id"):
            CollectorsOlap.objects.get(id=request.POST.get("declain_id")).delete()
            return HttpResponse('Пользователь успешно исключен!')
    else:
        action.send(request.user, verb='переход в Подтверждение пользователей')
        df = pandas.DataFrame(list(CollectorsOlap.objects.filter().values()))

        df_gr = pandas.DataFrame(list(CustomGroup.objects.filter(is_active=True).values()))
        df['groups'] = [list(df_gr['group']) for i in range(0, len(df))]

        return render(request, 'confirmation.html', context={
            "df": df.iterrows()
        })


@permission_required('website.admin')
@login_required(login_url='/login/')
def management(request):
    """
    Отвечате за блок Управление

    в perm собирается шаблон с id групп пользователей относительно прав текущего пользователя
    #  тестово усключена данная логика

    Django ORM
    Есть возможность создать кастомную группу, привязать кастомную группу отдельному пользователю,
    удалить группу со всеми связями

    Ajax позволяет отвязать кастомную группу от пользователя и обновить статус пользователя в системе

    Возвращает данные по группам и пользвователям в табличном виде
    """

    '''
    if 'website.admin_all' in request.user.get_group_permissions():
        group_obj = Group.objects.filter().values_list('id')
        perm = '(' + str(tuple(group_obj)).replace(',)', '').replace('(', '')
    elif 'website.admin_collection' in request.user.get_group_permissions():
        perm = "(4)"
    else:
        perm = "(4)"  # another case
    '''

    if request.method == "POST" and request.POST.get("group_name"):
        name = request.POST.get("group_name")
        group_error = "error"

        try:
            CustomGroup.objects.get(group=name, is_active=True)
        except CustomGroup.DoesNotExist:
            CustomGroup(group=name, admin_id=request.user.id).save()
            group_error = "done"

        df = admin_users.get_users()  # perm, request.user.id
        df_gr = pandas.DataFrame(list(CustomGroup.objects.filter(is_active=True).values()))  # admin_id=request.user.id,

        return render(request, 'management.html', context={
            "df": df.iterrows(),
            "df_gr": df_gr.iterrows(),
            "df_filter": df_gr.iterrows(),
            "group_error": group_error,
            "df_del": df_gr.iterrows(),
        })
    elif request.method == "POST" and request.POST.get("group_id") and request.POST.get("user_id"):
        group_id = request.POST.get("group_id")
        user_id = request.POST.get("user_id")
        try:
            CustomGroupUser.objects.get(group_id=group_id, user_id=user_id, dateend=None)  # , admin_id=request.user.id
            user_group_error = "error"
        except CustomGroupUser.DoesNotExist:
            CustomGroupUser(group_id=group_id, user_id=user_id, admin_id=request.user.id).save()
            admin_users.update_collectors()
            user_group_error = "done"

        df = admin_users.get_users()  # perm, request.user.id
        df_gr = pandas.DataFrame(list(CustomGroup.objects.filter(is_active=True).values()))  # admin_id=request.user.id,

        return render(request, 'management.html', context={
            "df": df.iterrows(),
            "df_gr": df_gr.iterrows(),
            "df_filter": df_gr.iterrows(),
            "user_group_error": user_group_error,
            "df_del": df_gr.iterrows(),
        })
    elif request.method == "POST" and request.POST.get("del_group_id"):
        del_group_id = request.POST.get("del_group_id")

        CustomGroup.objects.filter(id=del_group_id).update(is_active=False)
        CustomGroupUser.objects.filter(
            group_id=del_group_id
        ).update(dateend=now())
        admin_users.update_collectors()

        df = admin_users.get_users()  # perm, request.user.id
        df_gr = pandas.DataFrame(list(CustomGroup.objects.filter(is_active=True).values()))  # admin_id=request.user.id,
        return render(request, 'management.html', context={
            "df": df.iterrows(),
            "df_gr": df_gr.iterrows(),
            "df_filter": df_gr.iterrows(),
            "df_del": df_gr.iterrows(),
        })

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # TODO deprecated since 3.1 if request.is_ajax():
        try:
            id = request.POST.get("id_user", None)
            is_active = request.POST.get("is_active", None)
            action.send(request.user, verb='статус пользователя')
            User.objects.filter(id=id).update(is_active=is_active.title())
            admin_users.update_collectors()
        except:
            pass

        try:
            id_user_del = request.POST.get("id_user_del", None)
            group_name_del = request.POST.get("group_name_del", None)

            CustomGroupUser.objects.filter(
                group_id=CustomGroup.objects.get(group=group_name_del, is_active=True).id,
                user_id=id_user_del
            ).update(dateend=now())
            admin_users.update_collectors()
        except:
            pass
        return HttpResponse()
    else:
        action.send(request.user, verb='переход в управление')
        df = admin_users.get_users()  # perm, request.user.id
        df_gr = pandas.DataFrame(list(CustomGroup.objects.filter(is_active=True).values()))  # admin_id=request.user.id,

        return render(request, 'management.html', context={
            "df": df.iterrows(),
            "df_gr": df_gr.iterrows(),
            "df_filter": df_gr.iterrows(),
            "df_del": df_gr.iterrows(),
        })


@permission_required('website.upload')
@login_required(login_url='/login/')
def upload(request):
    return render(request, 'upload.html')


@permission_required('website.upload')
@login_required(login_url='/login/')
def upload_payments(request):
    return render(request, 'upload_payments.html')


@permission_required('website.upload')
@login_required(login_url='/login/')
def upload_payments_first(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # TODO deprecated since 3.1 if request.is_ajax():
        time.sleep(15)
        return HttpResponse()

    if request.method == "GET" and request.GET.get('hidden_input'):
        result = request.GET.get('hidden_input')
        issueFile = open('media/uploads/payments/type1/out/загрузки' + result, 'rb')
        response = FileResponse(issueFile, as_attachment=True)
        return response

    if request.method == "POST" and request.FILES['file_load']:
        myfile = request.FILES['file_load']
        fs = FileSystemStorage(location='media/uploads/payments/type1/in')
        filename = fs.save(myfile.name, myfile)

        result = upload_type1.main(fs.path(filename), request.user.id)
        if result.startswith('(1)_'):
            return render(request, 'upload_payments_1.html',
                          {'result': result, 'type': 'done'})
        else:
            return render(request, 'upload_payments_1.html',
                          {'result': result, 'type': 'error'})
    else:
        return render(request, 'upload_payments_1.html')


@permission_required('website.upload')
@login_required(login_url='/login/')
def upload_payments_second(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # TODO deprecated since 3.1 if request.is_ajax():
        time.sleep(15)
        return HttpResponse()

    if request.method == "GET" and request.GET.get('hidden_input'):
        issueFile = open('media/uploads/payments/type2/out/загрузки' + request.GET.get('hidden_input'), 'rb')
        response = FileResponse(issueFile, as_attachment=True)
        return response

    if request.method == "POST" and request.FILES['file_load']:
        myfile = request.FILES['file_load']
        fs = FileSystemStorage(location='media/uploads/payments/type2/in')
        filename = fs.save(myfile.name, myfile)

        result = upload_type2.main(fs.path(filename), request.user.id)
        if result.startswith('(2)_'):
            return render(request, 'upload_payments_2.html',
                          {'result': result, 'type': 'done'})
        else:
            return render(request, 'upload_payments_2.html',
                          {'result': result, 'type': 'error'})
    else:
        return render(request, 'upload_payments_2.html')


@permission_required('website.upload')
@login_required(login_url='/login/')
def upload_moneta(request):
    if request.method == "GET" and request.GET.get('hidden_input'):
        resultFile = open(request.GET.get('hidden_input'), 'rb')
        response = FileResponse(resultFile, as_attachment=True)
        return response
    if request.method == "POST":
        result = check_moneta.main(request.POST.get('date_first'), request.POST.get('date_second'))
        if result.startswith('media/uploads/moneta/moneta_yandex_'):
            return render(request, 'upload_moneta.html',
                          {'result': result, 'type': 'done'})
        else:
            return render(request, 'upload_moneta.html',
                          {'result': result, 'type': 'error'})
    else:
        return render(request, 'upload_moneta.html')


@permission_required('website.upload')
@login_required(login_url='/login/')
def upload_portfolio(request):
    if request.method == "GET" and request.GET.get('hidden_input'):
        resultFile = open(request.GET.get('hidden_input'), 'rb')
        response = FileResponse(resultFile, as_attachment=True)
        return response
    if request.method == "POST" \
            and request.FILES['file_load1'] \
            and request.FILES['file_load2'] \
            and request.FILES['file_load3'] \
            and request.FILES['file_load4']:
        fs = FileSystemStorage(location='media/uploads/portfolio/in')

        myfile1 = request.FILES['file_load1']
        filename1 = fs.save(myfile1.name, myfile1)

        myfile2 = request.FILES['file_load2']
        filename2 = fs.save(myfile2.name, myfile2)

        myfile3 = request.FILES['file_load3']
        filename3 = fs.save(myfile3.name, myfile3)

        myfile4 = request.FILES['file_load4']
        filename4 = fs.save(myfile4.name, myfile4)
        result = portfolio_checkup.main(request.POST.get('date_end'),
                                        fs.path(filename1),
                                        fs.path(filename2),
                                        fs.path(filename3),
                                        fs.path(filename4))
        if result.startswith('portfolio_output'):
            return render(request, 'upload_portfolio.html',
                          {'result': result, 'type': 'done'})
        else:
            return render(request, 'upload_portfolio.html',
                          {'result': result, 'type': 'error'})
    else:
        return render(request, 'upload_portfolio.html')


@permission_required('website.some')
@login_required(login_url='/login/')
def mailings(request):
    if request.method == "POST" and request.POST.get('client_gr') and request.POST.get(
            'text_mailing') and request.POST.get("btn_add"):
        action.send(request.user, verb='добавить рассылку')
        chech_push = auxiliary_func_delay.push_group(request.POST.get('client_gr'),
                                                     request.POST.get('text_mailing'),
                                                     request.POST.get("btn_add"))
        result = auxiliary_func_delay.get_group()
        if chech_push == False:
            return render(request, 'mailings.html', context={"result": result.iterrows(),
                                                             "chech_push": chech_push,
                                                             })
        else:
            return render(request, 'mailings.html', context={"result": result.iterrows(),
                                                             "chech_push": chech_push,
                                                             "check_name": request.POST.get('client_gr'),
                                                             "check_text": request.POST.get('text_mailing'),
                                                             })
    elif request.method == "POST" and request.POST.get("btn_delete"):
        action.send(request.user, verb='удалить рассылку')
        btn_del = str(request.POST.get("btn_delete")).split('&')
        name = list(map(str, btn_del))[0]
        user = list(map(str, btn_del))[1]
        auxiliary_func_delay.del_group(name, user)
        result = auxiliary_func_delay.get_group()
        return render(request, 'mailings.html', context={"result": result.iterrows()})

    elif request.method == "POST" and request.POST.get("btn_edit"):
        action.send(request.user, verb='отредактировать рассылку')
        btn_edit = str(request.POST.get("btn_edit")).split('&')
        name = list(map(str, btn_edit))[0]
        text = list(map(str, btn_edit))[1]
        result = auxiliary_func_delay.get_group()
        return render(request, 'mailings.html', context={"result": result.iterrows(),
                                                         "check_name": name,
                                                         "check_text": text,
                                                         "check_edit": "True"})

    elif request.method == "POST" and request.POST.get("btn_change"):
        action.send(request.user, verb='изменить рассылку')
        auxiliary_func_delay.del_group(request.POST.get('client_gr'), request.POST.get("btn_change"))
        auxiliary_func_delay.push_group(request.POST.get('client_gr'),
                                        request.POST.get('text_mailing'),
                                        request.POST.get("btn_change"))

        # auxiliary_func_delay.edit_group(request.POST.get('client_gr'),request.POST.get('text_mailing'),request.POST.get("btn_change"))
        result = auxiliary_func_delay.get_group()
        return render(request, 'mailings.html', context={"result": result.iterrows()})
    else:
        action.send(request.user, verb='переход в рассылки')
        result = auxiliary_func_delay.get_group()
        return render(request, 'mailings.html', context={"result": result.iterrows()})


@permission_required('website.kb')
@login_required(login_url='/login/')
def db_search(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # TODO deprecated since 3.1 if request.is_ajax():
        try:
            req_phone = request.POST.get("req_phone", None)
            res = {}  # TODO from .scripts import dadata
            response = ' '
            if res['city'] != None:
                response = res['city'] + response
            if res['region'] != None:
                response = response + res['region']
            return HttpResponse(response)
        except:
            return HttpResponse('Что-то пошло не так!', status=400)
    if request.method == "POST" and request.POST.get('surname'):
        if request.POST.get('phone'):
            phone = request.POST.get('phone')
        else:
            phone = ''
        if request.POST.get('address'):
            address = request.POST.get('address')
        else:
            address = ''

        if request.POST.get('bdate'):
            bdate = request.POST.get('bdate')
        else:
            bdate = None

        df_tuple = kb_script.get_fio(
            request.POST.get('surname').replace(' ', ''),
            request.POST.get('name').replace(' ', ''),
            request.POST.get('midname').replace(' ', ''),
            bdate,
            phone,
            address
        )
        error_kb = ''
        if len(df_tuple) > 2:
            KBLog(text=f'query {str(df_tuple[0])} - {df_tuple[1]}', user_id=request.user.id).save()
            error_kb = df_tuple[2]
            df0 = pandas.DataFrame()
            df1 = df0
        else:
            df0 = df_tuple[0].iterrows()
            df1 = df_tuple[1].iterrows()

        return render(request, 'db_search.html',
                      context={
                          "df0": df0,
                          "df1": df1,
                          "fio_checker": 1,
                          "entered_surname": request.POST.get('surname'),
                          "entered_name": request.POST.get('name'),
                          "entered_midname": request.POST.get('midname'),
                          "entered_date": bdate,
                          "entered_phone": phone,
                          "entered_address": address,
                          "error_kb": error_kb
                      })
    elif request.method == "POST" and request.POST.get('phone'):
        if request.POST.get('name'):
            name = request.POST.get('name').replace(' ', '')
        else:
            name = ''
        if request.POST.get('midname'):
            midname = request.POST.get('midname').replace(' ', '')
        else:
            midname = ''
        if request.POST.get('address'):
            address = request.POST.get('address')
        else:
            address = ''

        if request.POST.get('bdate'):
            bdate = request.POST.get('bdate')
        else:
            bdate = None

        df = kb_script.get_phones(
            request.POST.get('phone'),
            bdate,
            name,
            midname,
            address
        )
        return render(request, 'db_search.html', context={
            "df_phone": df.iterrows(),
            "phone_checker": 1,
            "entered_phone": request.POST.get('phone'),
            "entered_date": bdate,
            "entered_name": name,
            "entered_midname": midname,
            "entered_address": address,
        })
    elif request.method == "POST" and request.POST.get('address'):
        if request.POST.get('name'):
            name = request.POST.get('name').replace(' ', '')
        else:
            name = ''
        if request.POST.get('midname'):
            midname = request.POST.get('midname').replace(' ', '')
        else:
            midname = ''
        if request.POST.get('bdate'):
            bdate = request.POST.get('bdate')
        else:
            bdate = None

        df = kb_script.get_address(
            request.POST.get('address'),
            bdate,
            name,
            midname
        )
        return render(request, 'db_search.html',
                      context={
                          "df_address": df.iterrows(),
                          "address_checker": 1,
                          "entered_address": request.POST.get('address'),
                          "entered_name": name,
                          "entered_midname": midname,
                          "entered_date": bdate,
                      })
    elif request.method == "POST":
        action.send(request.user, verb='Поиск по базе - поиск')
        return render(request, 'db_search.html', context={
            "error": 'Внимание, незаполнено одно из обязательных полей: "Фамилия", "Телефон", "Адрес"!'})
    else:
        action.send(request.user, verb='переход в Поиск по базе')
        return render(request, 'db_search.html')


@permission_required('website.some')
@login_required(login_url='/login/')
def cash_u_api(request):
    existing_user = False
    if request.method == "POST":
        if request.POST.get('api_login') and request.POST.get('api_pass'):
            action.send(request.user, verb='api добавить пользователя')
            existing_user = cashu_api_admin.user_in(request.POST.get('api_login'), request.POST.get('api_pass'))
        elif request.POST.get('btn_block'):
            action.send(request.user, verb='api заблокировать пользователя')
            cashu_api_admin.user_block(request.POST.get('btn_block'))
        elif request.POST.get('btn_unblock'):
            action.send(request.user, verb='api разблокировать пользователя')
            cashu_api_admin.user_unblock(request.POST.get('btn_unblock'))
        result = cashu_api_admin.get_users()
        return render(request, 'cash_u_api.html', context={"result": result.iterrows(),
                                                           "existing_user": existing_user})
    else:
        action.send(request.user, verb='переход в api-admin')
        result = cashu_api_admin.get_users()
        return render(request, 'cash_u_api.html', context={"result": result.iterrows(),
                                                           "existing_user": existing_user})


@permission_required('website.dashboards')
@login_required(login_url='/login/')
def dashboards(request):
    dashboard_login = "?userid=loandail&password=BHuQztA4ke"
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # TODO deprecated since 3.1 if request.is_ajax():
        try:
            dash_id = request.POST.get("dash_id", None)
            Dashboard.objects.filter(id=dash_id).delete()
        except:
            pass
        return HttpResponse()

    dashboard_error = "done"
    groups = Group.objects.values()
    df_groups = pandas.DataFrame(groups)
    df_dashboards = pandas.DataFrame(Dashboard.objects.values())

    if 'admin.delete_logentry' not in request.user.get_group_permissions():
        list_allowed = list(pandas.DataFrame(request.user.groups.values())['id'])
        list_allowed.append(14)
        df_dashboards = df_dashboards[df_dashboards['group_id'].isin(list_allowed)]
    if not df_dashboards.empty:
        df_dashboards = df_dashboards.merge(df_groups.rename(columns={'id': 'group_id', 'name': 'group_name'}),
                                            how='inner', on='group_id')

    if request.method == "POST" and request.POST.get('name-dsh') and request.POST.get('link-dsh'):
        if not request.POST.get('group-dsh'):
            dashboard_error = "Отдел не указан!"
        else:
            name = request.POST.get('name-dsh')
            link = request.POST.get('link-dsh')
            group_names = request.POST.get('group-dsh').split()

            for group_name in group_names:
                for group in groups:
                    if group['name'] == group_name:
                        group_id = group['id']
                        try:
                            Dashboard.objects.get(name=name, group_id=group_id)
                            dashboard_error = "Dashboard с данным именем и указанным отделом уже существует!"
                        except Dashboard.DoesNotExist:
                            Dashboard(name=name, link=link, group_id=group_id).save()
                            df_dashboards = pandas.DataFrame(Dashboard.objects.values())
                            if not df_dashboards.empty:
                                df_dashboards = df_dashboards.merge(
                                    df_groups.rename(columns={'id': 'group_id', 'name': 'group_name'}),
                                    how='inner', on='group_id')
    else:
        action.send(request.user, verb='переход в dashboards')

    return render(request, 'dashboards.html', context={"df_groups": df_groups.iterrows(),
                                                       "dashboard_error": dashboard_error,
                                                       'df_dashboards': df_dashboards.iterrows(),
                                                       'dashboard_login': dashboard_login})


@permission_required('website.bias')
@login_required(login_url='/login/')
def bias(request):
    try:
        bias_login = request.user.biasauth.login
        bias_pass = request.user.biasauth.password
    except:
        # return render(request, 'index.html', context={'error_bias': 'Пользователь не имеет прав доступа к BIAS!'})
        bias_login = ''
        bias_password = ''

    # cipher = Fernet(CIPHER_KEY)
    # bias_password = cipher.decrypt(bytes(bias_pass.replace("b'", "").replace("'", ""), encoding='utf8')).decode("utf-8")
    if request.method == "POST" and request.POST.get('btn_bias'):
        error_bias = ''
        adr_bias = request.POST.get('adr')

        bias_list = bias_script.get_bias(bias_login,
                                         bias_password,
                                         request.POST.get('fio'),
                                         request.POST.get('bdate'),
                                         request.POST.get('input_phone'),
                                         adr_bias)
        '''
        ,
                             request.POST.get('pasp'),
                             request.POST.get('biasdate'),
                             request.POST.get('inn'),
                             request.POST.get('bias_snils')'''

        df_bias = bias_list[0].drop_duplicates()
        df_bias_possible = bias_list[1].drop_duplicates()

        if bias_list[2]:
            adr_bias = bias_list[2]

        if df_bias.empty and df_bias_possible.empty:
            error_bias = 'Ничего не найдено!'

        if bias_list[3]:
            error_bias = 'Адрес введен некорректно!'

        if bias_list[4]:
            error_bias = str(bias_list[4])  # ?????

        if error_bias != '':
            BiasLog(text=error_bias, user_id=request.user.id).save()

        return render(request, 'bias.html', context={'df_bias': df_bias,
                                                     'df_bias_possible': df_bias_possible,
                                                     'fio': request.POST.get('fio'),
                                                     'bdate': request.POST.get('bdate'),
                                                     'input_phone': request.POST.get('input_phone'),
                                                     'adr': adr_bias,
                                                     'error_bias': error_bias})
    action.send(request.user, verb='переход в bias')
    return render(request, 'bias.html', context={
        'df_bias': pandas.DataFrame(),
        'df_bias_possible': pandas.DataFrame()
    })


@permission_required('website.bias')
@login_required(login_url='/login/')
def bias_profile(request):
    try:
        bias_login = request.user.biasauth.login
        bias_pass = request.user.biasauth.password
    except:
        # return render(request, 'index.html', context={'error_bias': 'Пользователь не имеет прав доступа к BIAS!'})
        bias_login = ''
        bias_pass = ''

    cipher = Fernet(CIPHER_KEY)
    bias_password = cipher.decrypt(bytes(bias_pass.replace("b'", "").replace("'", ""), encoding='utf8')).decode("utf-8")
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # TODO deprecated since 3.1 if request.is_ajax():
        try:
            request_number = request.POST.get('request_number', None).replace('+7', '')
            request_address = request.POST.get('request_address', None)
            df_bias = pandas.DataFrame()
            df_bias_possible = pandas.DataFrame()

            if request_number != '':
                bias_list = bias_script.get_bias(bias_login,
                                                 bias_password,
                                                 '',
                                                 '',
                                                 request_number,
                                                 '')
                df_bias = bias_list[0].drop_duplicates()
                df_bias_possible = bias_list[1].drop_duplicates()
            if request_address != '':
                bias_list = bias_script.get_bias(bias_login,
                                                 bias_password,
                                                 '',
                                                 '',
                                                 '',
                                                 request.POST.get('request_address', None))
                df_bias = bias_list[0].drop_duplicates()
                df_bias_possible = bias_list[1].drop_duplicates()
            df_bias = df_bias[~df_bias.fio.str.contains(request.POST.get('del_fio', None))]
            df_bias_possible = df_bias_possible[~df_bias_possible.fio.str.contains(request.POST.get('del_fio', None))]

            if df_bias.empty and df_bias_possible.empty:
                return HttpResponse('empty')
            else:
                lists = {}
                if not df_bias.empty:
                    lists['list_1'] = df_bias.to_dict()
                if not df_bias_possible.empty:
                    lists['list_2'] = df_bias_possible.to_dict()
                return JsonResponse(lists, safe=False)
        except Exception:
            pass
    if request.method == "POST" and request.POST.get('_fio'):
        action.send(request.user, verb='bias-открытие анкеты')
        if request.POST.get('_birthdate_result') == '':
            _birthdate = request.POST.get('_birthdate_main')
            if not _birthdate:
                _birthdate = ''
        else:
            _birthdate = request.POST.get('_birthdate_result')

        _input_phone = request.POST.get('_input_phone')
        if not _input_phone:
            _input_phone = ''

        _birthplace = request.POST.get('_birthplace')
        if not _birthplace:
            _birthplace = ''

        _adr = request.POST.get('_adr')
        if not _adr:
            _adr = ''

        _fio = request.POST.get('_fio')
        title = ''
        error_bias = ''

        context = {}
        profile_df = bias_script.check_profile(
            _fio,
            _birthdate,
            _input_phone,
            _adr,
            request.user.id
        )

        if type(profile_df) == str:
            context['error_bias'] = profile_df
            return render(request, 'bias_profile.html', context=context)

        if _adr and ('.' in _fio) and profile_df.empty:
            uid, title = bias_script.get_bias(
                bias_login,
                bias_password,
                '',
                '',
                '',
                _adr,
                _fio
            )
            result = bias_script.get_profile(
                bias_login,
                bias_password,
                request.user.id,
                title,
                _birthdate,
                _input_phone,
                _birthplace,
                _adr,
                profile_df,
                uid
            )
        else:
            result = bias_script.get_profile(
                bias_login,
                bias_password,
                request.user.id,
                _fio,
                _birthdate,
                _input_phone,
                _birthplace,
                _adr,
                profile_df
            )

        if type(result) == list:
            for bias_error in result:
                error_bias = error_bias + bias_error + ' '
            BiasLog(text=error_bias, user_id=request.user.id).save()

        if type(result) == str:
            BiasLog(text=result, user_id=request.user.id).save()  # приходит admin error , возможно, писать не нужно
            context['error_bias'] = result
            return render(request, 'bias_profile.html', context=context)

        if title:
            context['del_fio'] = title
        else:
            context['del_fio'] = _fio

        if error_bias:
            context['error_bias'] = error_bias
            return render(request, 'bias_profile.html', context=context)

        for res in result:
            try:
                if not res[36].empty:
                    context['df_person'] = res[36].iterrows()
            except:
                pass
            try:
                if not res[37].empty:
                    context['df_organization'] = res[37].iterrows()
            except:
                pass
            try:
                if not res[38].empty:
                    context['df_entrepreneur'] = res[38].iterrows()
            except:
                pass
            try:
                if not res[39].empty:
                    context['df_phone'] = res[39].iterrows()
            except:
                pass
            try:
                if not res[40].empty:
                    context['df_address'] = res[40].iterrows()
            except:
                pass
            try:
                if not res[41].empty:
                    context['df_document'] = res[41].iterrows()
            except:
                pass
            try:
                if not res[42].empty:
                    context['df_negative'] = res[42].iterrows()
            except:
                pass
            try:
                if not res[43].empty:
                    context['df_linked_person'] = res[43].iterrows()
            except:
                pass
            try:
                if not res[44].empty:
                    context['df_linked_entrepreneur'] = res[44].iterrows()
            except:
                pass
            try:
                if not res[45].empty:
                    context['df_linked_organization'] = res[45].iterrows()
            except:
                pass
            try:
                if not res[46].empty:
                    context['df_linked_estate'] = res[46].iterrows()
            except:
                pass
            try:
                if not res[47].empty:
                    context['df_linked_vehicle'] = res[47].iterrows()
            except:
                pass
            try:
                if not res[48].empty:
                    context['df_addition'] = res[48].iterrows()
            except:
                pass
        return render(request, 'bias_profile.html', context=context)

    action.send(request.user, verb='bias-открытие анкеты')
    return render(request, 'bias_profile.html')


@permission_required('website.upload')
@login_required(login_url='/login/')
def receipts(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # TODO deprecated since 3.1 if request.is_ajax():
        time.sleep(30)
        return HttpResponse()

    if request.method == "GET" and request.GET.get('hidden_input'):
        result = request.GET.get('hidden_input')
        issueFile = open(result, 'rb')
        response = FileResponse(issueFile, as_attachment=True)
        return response

    try:
        if request.method == "POST" and request.FILES['file_load']:
            myfile = request.FILES['file_load']
            fs = FileSystemStorage(location='media/receipts/in')
            filename = fs.save(myfile.name, myfile)
            result = atol_online.load_receipts(fs.path(filename),
                                               request.user.id)

            if result.startswith('Загрузка'):
                return render(request, 'receipts.html',
                              {'result': result, 'type': 'success'})
            else:
                return render(request, 'receipts.html',
                              {'result': result, 'type': 'error'})
    except:
        pass

    try:
        if request.method == "POST" and request.POST.get('databeg') and request.POST.get('dataend'):
            result = atol_online.get_receipts(request.user.id, request.POST.get('databeg'), request.POST.get('dataend'))

            if result.startswith('media'):
                return render(request, 'receipts.html',
                              {'result': result, 'type': 'done'})
            else:
                return render(request, 'receipts.html',
                              {'result': result, 'type': 'error'})
    except:
        pass

    df_dates = atol_online.check_dates(request.user.id)

    if df_dates:
        return render(request, 'receipts.html',
                      {'result': df_dates, 'type': 'error'})
    else:
        return render(request, 'receipts.html')
