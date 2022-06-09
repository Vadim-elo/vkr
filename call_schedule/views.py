import pandas as pd
from django.contrib.auth.decorators import permission_required, login_required
from django.db import connection
from django.db.models import Case, When, Value, CharField
from django.shortcuts import render
from call_schedule.models import History, ArrayFormat


@permission_required('website.call_schedule')
@login_required(login_url='/login/')
def delays(request):
    """
    В функции реализовано добавление инфо в график звонков, удаление и получение информации

    Права на реадктивроание есть только у статически указанных групп

    Посредством ORM осуществляется обращение к бд,
    остается доработка, чтобы заменить реализацию обращения к бд с помощью sql
    """
    weekday_error = ''
    weekdays = []
    days = []

    df_for_admin = pd.DataFrame()
    user_group_perms = request.user.get_group_permissions()
    if 'website.admin_collection' in user_group_perms \
            or 'website.admin_all' in user_group_perms:
        if request.POST.get('monday'):
            days.append('Понедельник')
            weekdays.append(1)
        if request.POST.get('tuesday'):
            days.append('Вторник')
            weekdays.append(2)
        if request.POST.get('wednesday'):
            days.append('Среда')
            weekdays.append(3)
        if request.POST.get('thursday'):
            days.append('Четверг')
            weekdays.append(4)
        if request.POST.get('friday'):
            days.append('Пятница')
            weekdays.append(5)

        termdelay = request.POST.get('input_termdelay')

        if request.method == 'POST' and len(weekdays) and termdelay:
            for index, weekday in enumerate(weekdays):
                try:
                    History.objects.get(weekday=weekday, termdelay=termdelay)
                    weekday_error = weekday_error + days[index] + ' '
                except History.DoesNotExist:
                    History(weekday=weekday, termdelay=termdelay).save()
            if weekday_error:
                weekday_error = f'Записи в календаре уже существуют за указанный срок просрочки и дни: ' \
                                f'{weekday_error} . Проверьте, возможно, они заблокированы!'

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # TODO deprecated since 3.1 if request.is_ajax():
            note_id = int(request.POST.get('note_id', 0).replace('checkbox', ''))
            is_active = request.POST.get('is_active', 0)
            History.objects.filter(id=note_id).update(is_active=is_active.title())

        df_for_admin = pd.DataFrame(list(
            History.objects.filter().annotate(
                nameday=Case(
                    When(weekday=1, then=Value('Понедельник')),
                    When(weekday=2, then=Value('Вторник')),
                    When(weekday=3, then=Value('Среда')),
                    When(weekday=4, then=Value('Четверг')),
                    When(weekday=5, then=Value('Пятница')),
                    output_field=CharField()
                )
            ).values()
        ))

        if not df_for_admin.empty:
            df_for_admin = df_for_admin.sort_values(by=['weekday']).reset_index(drop=True)

    '''
    доработка
    history_in = History.objects.filter(weekday=OuterRef('pk'))
    history_out = History.objects.values('weekday').annotate(
        newest_commenters=ArrayFormat(history_in.values('termdelay')),
    )
    '''

    # df_for_all = pd.read_sql(
    #     """
    #     select case
    #            when weekday = 1 then 'Понедельник'
    #            when weekday = 2 then 'Вторник'
    #            when weekday = 3 then 'Среда'
    #            when weekday = 4 then 'Четверг'
    #            when weekday = 5 then 'Пятница'
    #            end as weekday,
    #            termdelays
    #     from (
    #              select weekday,
    #                     (array(
    #                             select termdelay
    #                             from call_schedule_history c_in
    #                             where c_in.is_active
    #                               and c.weekday = c_in.weekday
    #                             order by 1
    #                         )) as termdelays
    #              from call_schedule_history c
    #              where is_active
    #              group by 1, 2
    #              order by 1
    #          ) a
    #     """,
    #     con=connection
    # )

    data = {'weekday': ['Понедельник'],
            'termdelays': [[1,2,3]]}

    # Create DataFrame
    df_for_all = pd.DataFrame(data)

    return render(request, 'call_schedule.html', context={
        'df_for_all': df_for_all,
        'df_for_admin': df_for_admin,
        'add_error': weekday_error
    })
