import pandas
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render
from sms_delay.scripts import sms_delay


@permission_required('website.sms')
@login_required(login_url='/login/')
def sms(request):
    """
    В функции происходит вызов отправки смс клиенту и проверка на возможность отправки
    """
    df_all_sms = pandas.DataFrame()

    creditaccount = request.POST.get("creditaccount")

    creditaccount_approved = request.POST.get("creditaccount_approved")
    text_mailing = request.POST.get("text_mailing")
    client_phone = request.POST.get("client_phone")
    peoplemain_id = request.POST.get("peoplemain_id")
    collector_id = request.POST.get("collector_id")

    if creditaccount_approved and text_mailing and client_phone and peoplemain_id and collector_id:
        result = sms_delay.to_client(
            text_mailing,
            client_phone,
            request.user.id,
            peoplemain_id,
            collector_id,
            creditaccount_approved
        )

        return render(request, 'sms_delay.html', context={
            'message': result[1],
            'message_type': result[0],
            'df_all_sms': result[2],
            'creditaccount': result[3],
        })

    if creditaccount:
        result = sms_delay.check_info(
            creditaccount,
            request.user.last_name + ' ' + request.user.first_name,
            request.user.id
        )

        if len(result) == 2:
            return render(request, 'sms_delay.html', context={
                'creditaccount': creditaccount,
                'message': result[1],
                'message_type': result[0],
                'text_sms': sms_delay.TEXT_SMS,
                'df_all_sms': df_all_sms
            })
        elif len(result) == 3:
            return render(request, 'sms_delay.html', context={
                'creditaccount': creditaccount,
                'message': result[1],
                'message_type': result[0],
                'text_sms': sms_delay.TEXT_SMS,
                'df_all_sms': result[2]
            })
        else:
            return render(request, 'sms_delay.html', context={
                'creditaccount': creditaccount,
                'message': 'Проверка выполнена успешно!',
                'message_type': 'success',
                'text_sms': result[0],
                'client_phone': result[1],
                'peoplemain_id': result[2],
                'collector_id': result[3],
                'fio_client': result[4],
                'df_all_sms': result[5]
            })

    return render(request, 'sms_delay.html', context={
        'text_sms': sms_delay.TEXT_SMS,
        'df_all_sms': df_all_sms
    })