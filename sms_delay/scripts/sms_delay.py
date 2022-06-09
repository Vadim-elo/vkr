# -*- coding: utf-8 -*-
import datetime
import traceback

import pandas as pd
from dateutil.relativedelta import relativedelta
from django.core.mail import send_mail
from django.utils import timezone as utils_timezone
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError

from mysite.settings import db_analytics, TIME_ZONE, SLAVE_HOST, SLAVE_PORT, \
    SLAVE_USER, SLAVE_PASSWORD, SLAVE_NAME
from sms_delay.models import SMSLog
from sms_delay.scripts import auxiliary_func as func

TEXT_SMS = 'Some messgae'

PENTAHO = create_engine(db_analytics)
ADMIN_ERROR = 'Что-то пошло не так, пожалуйста, обратитесь в техническую поддержку loandail.team'
DBLINK_SLAVE = f'host={SLAVE_HOST} port={SLAVE_PORT} user={SLAVE_USER} password={SLAVE_PASSWORD} dbname={SLAVE_NAME}'


def creditaccount_info(peoplemain_id, user_id):
    """
    Функция возвращает dataframe истории сообщений клиенту по просрочке

    В запрос передается DBLINK_SLAVE - строка подключения к базе slave, номер телефона клиента, peoplemain_id
    """
    data = {'Name': ['Tom', 'nick', 'krish', 'jack'],
            'Age': [20, 21, 19, 18]}

    # Create DataFrame
    return pd.DataFrame(data)

    df_check_statuses = pd.read_sql(f"""
                select id_sms
                from marketing_newsletter_sms
                where peoplemain_id = '{peoplemain_id}'
                and type_newsletter in ('delay_credits_daily', 'daily_121', 'daily_180', 'sms_delay')
                and status is null
                """,
                                    con=PENTAHO
                                    )

    connection_pentaho = PENTAHO.raw_connection()
    cursor = connection_pentaho.cursor()
    for id_sms in tuple(df_check_statuses['id_sms']):
        resp_status, resp_time, message_status = func.status(id_sms)
        if message_status == 'error':
            SMSLog(
                text=f'Ошибка при обновлении статусов для peoplemain_id  = {str(peoplemain_id)},'
                     f' ошибка: {str(resp_status)}',
                user_id=user_id
            ).save()
        else:
            if resp_time:
                cursor.execute(
                    f'''
                    update marketing_newsletter_sms 
                    set 
                        time = '{pd.to_datetime(resp_time)}', 
                        status = '{message_status}'
                    where id_sms = '{str(id_sms)}'
                    '''
                )
                connection_pentaho.commit()

    cursor.close()

    df_checker = pd.read_sql(
        f"""
        with email_cte as (
                select day_of_send::date,
                       null::text as users_id,
                       'Отправлено'::text as status
                from marketing_newsletter_email
                where peoplemain_id = '{peoplemain_id}'
                and type_of_newsletter in ('daily_91', 'daily_121', 'daily_150', 'daily_180')
            ),
            sms_cte as (
                select day_of_send::date,
                       case when type_newsletter = 'sms_delay' then special_marks else null end as users_id,
                       case
                           when status = 'deliver' then 'Доставлено'
                           when status = 'not_deliver' then 'Не доставлено'
                           when status = 'expired' then 'Не доставлено'
                           else 'В процессе'
                       end as status
                from marketing_newsletter_sms
                where peoplemain_id = '{peoplemain_id}'
                and type_newsletter in ('delay_credits_daily', 'daily_121', 'daily_180', 'sms_delay')
            ),
                messeges_cte as (
                    select *
                    from dblink('{DBLINK_SLAVE}',
                             '   select messagedate, users_id, ''Доставлено'' as status
                                 from messages
                                 where users_id is not null -- сгенерирована вручную
                                 and external_status_id in (1036, 1035)
                                 and peoplemain_id = ''{peoplemain_id}''
                             '
                          ) as messeges(massagedate date, users_id text, status text)
                )

            select case when collectors.fio is null then 'Система'  else collectors.fio end as name, 
            uni.massagedate::date, uni.status, uni.type
                from (
                        select *, 'смс' as type 
                        from messeges_cte
                        union all
                        select *, 'смс' as type 
                        from sms_cte
                        union all
                        select *, 'email' as type 
                        from email_cte
                     )uni
                left join collectors
                on uni.users_id = collectors.users_id::text
                order by uni.massagedate
                desc
        """,
        con=PENTAHO
    )
    return df_checker


def to_client(text, phone, user_id, peoplemain_id, collector_id, creditaccount_approved):
    """
    Функция вызывает func.sending() (отправку сообщения клиенту) из модуля auxiliary_func,
    message_send содержит id sms (resp_send - телефон клиента), либо статус error (resp_send текст ошибки из sms16)

    В случае успешной операции вызывается func.status() для получаения статуса доставки сообщения, где на выходе
    resp_status - тело ошибки, resp_time - время отправки смс, message_status - статус доставки сообщения

    Готовый dataframe дополняется в marketing_newsletter_sms базы olap

    Следом вызывается creditaccount_info для получения истории отправкии сообщений по просрочке клиенту

    Функция возвращается статус, тело ошибки, таблицу истории сообщений по номеру договора, номер договора
    """
    df_all_sms = pd.DataFrame()

    resp_send, message_send = func.sending(phone, text)

    if message_send == 'error':
        SMSLog(
            text=f'Ошибка sending для {phone}  с тексто: {text}, ошибка: {str(resp_send)}',
            user_id=user_id
        ).save()
        return 'error', ADMIN_ERROR, df_all_sms, creditaccount_approved
    elif message_send == 'timeout':
        SMSLog(
            text=f'Ошибка timeout when sending для {phone}  с тексто: {text}, ошибка: {str(resp_send)}',
            user_id=user_id
        ).save()
        return 'error', \
               'Отправка сообщения невозможна, попробуйте через несколько минут.', \
               df_all_sms, \
               creditaccount_approved
    else:
        resp_status, resp_time, message_status = func.status(message_send)
        if message_status == 'error':
            SMSLog(
                text=f'Ошибка status для {phone}  с текстом: {text}, ошибка: {str(resp_status)}',
                user_id=user_id
            ).save()
            return 'error', \
                   'Ошибка получения статуса отправки смс, пожалуйста, ' \
                   'обратитесь в техническую поддержку loandail.team', \
                   df_all_sms, \
                   creditaccount_approved
        elif message_status == 'timeout':
            SMSLog(
                text=f'Ошибка timeout when status для {phone}  с текстом: {text}, ошибка: {str(resp_status)}',
                user_id=user_id
            ).save()
            resp_time = None
            message_status = None

    df = pd.DataFrame(columns=['peoplemain_id', 'value', 'id_sms', 'time', 'status', 'type_newsletter']).append(
        {
            'peoplemain_id': peoplemain_id,
            'value': resp_send,
            'id_sms': message_send,
            'time': pd.to_datetime(resp_time),
            'status': message_status,
            'day_of_send': datetime.datetime.now().date(),
            'type_newsletter': 'sms_delay',
            'special_marks': collector_id
        },
        ignore_index=True
    )
    df.to_sql('marketing_newsletter_sms', con=PENTAHO, if_exists='append', index=False)

    df_all_sms = creditaccount_info(peoplemain_id, user_id)
    if message_status == 'not_deliver':
        return 'error', 'Что-то пошло не так. Сообщение не доставлено!', df_all_sms, creditaccount_approved
    elif message_status == 'expired':
        return 'error', 'Сообщение не доставлено! Было предпринято несколько попыток отправки сообщения.', df_all_sms, \
               creditaccount_approved
    elif message_status is None:
        return 'success', 'Сообщение отправлено, статус доставки неизвестен. Пожалуйста, проверьте статус позже!', \
               df_all_sms, creditaccount_approved
    else:
        return 'success', 'Отправка прошла успешно', df_all_sms, creditaccount_approved


def check_timezone(timezone: int):
    """
    Функция проверяет входит ли время отправки в допустимое время с 9 до 20ч относительно временной зоны клиента,
    возвращает статус и тело уведомления
    """
    return 'success', ''
    now = utils_timezone.now().astimezone(utils_timezone.pytz.timezone(TIME_ZONE))
    available_hour = now.hour + timezone

    if 9 <= available_hour < 19:
        return 'success', ''
    elif 19 == available_hour:
        if now.minute < 50:
            return 'success', ''
    return 'fail', f'с {str(9 + timezone)} по 20ч по МСК'


def check_creditaccount_and_fio(creditaccount, fio):
    """
    Функция возвращает dataframe с данными, найденными по номеру договора клиента и фио сотрудника
    В запрос также передается DBLINK_SLAVE - строка подключения к  slave базе
    """

    # df = pd.read_sql(
    #     f"""
    #         select *
    #         from dblink('{DBLINK_SLAVE}',
    #             format('with credit_cte as (
    #                 select peoplemain_id, id as credit_id, creditaccount
    #                 from credit
    #                 where creditaccount = %s
    #                 ), bq as (
    #                 select credit_cte.*,peoplecontact.phone
    #                 from (
    #                     select value as phone,peoplemain_id,
    #                     row_number() over (
    #                         partition by peoplemain_id order by id desc
    #                     ) as num
    #                     from peoplecontact
    #                     where peoplemain_id in (select credit_cte.peoplemain_id from credit_cte)
    #                         and partners_id = 6
    #                         and contact_id = 171
    #                         and isactive = 1
    #                     ) peoplecontact
    #                     left join credit_cte
    #                     on peoplecontact.peoplemain_id = credit_cte.peoplemain_id
    #                 where num = 1
    #                 )
    #
    #             select bq.peoplemain_id, bq.creditaccount, bq.phone, amount_all, delay, collector.users_id,
    #                    collector.collector_phone, addresszone.timezone, fio.fio
    #             from bq
    #                 left join
    #                 (
    #                 select *
    #                 from (
    #                     select credit_id,
    #                         eventdate,
    #                         amount_all,
    #                         delay,
    #                         row_number() over (partition by credit_id order by eventdate desc) as num
    #                     from creditdetails
    #                     where eventdate::date = now()::date
    #                         and credit_id in (select credit_id from bq)
    #                     ) creditdetails
    #                 where num = 1
    #                 ) creditdetails
    #                 on bq.credit_id = creditdetails.credit_id
    #                 left join
    #                 (
    #                     select collector.credit_id, collector.users_id, peoplecontact.value as collector_phone
    #                     from collector
    #                     left join users
    #                     on collector.users_id = users.id
    #                     left join peoplecontact
    #                     on peoplecontact.peoplemain_id = users.peoplemain_id
    #                     where collector.credit_id in (select bq.credit_id from bq)
    #                     and peoplecontact.contact_id = 171
    #                     and peoplecontact.isactive = 1
    #                     and collector.dataend is null
    #                 )collector
    #                 on collector.credit_id = bq.credit_id
    #                 left join
    #                 (
    #                     select timezone, peoplemain_id
    #                     from (
    #                              select timezone,peoplemain_id,
    #                              row_number() over (
    #                                 partition by peoplemain_id order by id desc
    #                              ) as num
    #                              from address
    #                                       left join regions
    #                                                 on regions.code = address.region_short
    #                              where peoplemain_id in (select peoplemain_id from bq)
    #                                and partners_id = 6
    #                          ) addresszone
    #                     where num = 1
    #                 )addresszone
    #                 on addresszone.peoplemain_id = bq.peoplemain_id
    #                 left join
    #                 (select fio, peoplemain_id
    #                 from (
    #                          select concat(surname, '' '', name, '' '', midname) as fio,
    #                                 id, peoplemain_id,
    #                                 row_number() over (partition by peoplemain_id order by id desc) as num
    #                          from peoplepersonal
    #                          where peoplemain_id = (select peoplemain_id from bq)
    #                            and partners_id = 6
    #                            and gender is not null
    #                      )fio
    #                 where num = 1) fio
    #                 on fio.peoplemain_id = bq.peoplemain_id
    #             ', quote_literal({creditaccount}))
    #             )as credit_info(peoplemain_id text, creditaccount text, phone text, amount text, delay int,
    #                 collector_users_id text, collector_phone text, timezone int, fio text)
    #         left join
    #         (
    #             select users_id::text
    #             from collectors
    #             where trim(replace(fio,'  ',' ')) = '{fio}'
    #         ) collectors
    #         on credit_info.collector_users_id = collectors.users_id
    #         """, con=PENTAHO
    # )

    data = {
        'peoplemain_id': ['Tom'],
        'creditaccount': [20],
        'phone': [20],
        'amount_all': [20],
        'delay': [20],
        'users_id': [20],
        'collector_phone': [20],
        'timezone': [20],
        'fio': [20]
    }

    # Create DataFrame
    df = pd.DataFrame(data)
    print(df)
    return df


def check_delays(peoplemain_id, delay):
    """
    В функции собирается dataframe с проверкой отправок смс клиенту за периоды: день, неделя, месяц
    Проверяются смс из marketing_newsletter_sms, относящиеся к просрочке, из messages, сообщений, сгенерированных
    самостоятельно сотрудниками. Просиходит учитывание звонков робота на 1,2 и 3 день(в запросе и далее по скрипту).

    Функция также проверяет отправки, учитывая стратегию отправки смс (delay_sms)

    Функция возвращает уведомление сотруднику, либо статус success успешной отправки сообщения клиенту
    в зависимости от подсчитанных ( и возможных) отправок смс клиенту за указанные периоды.
    """
    return 'success'
    query = f"""
        with sms_cte as (
            select day_of_send::date,
                   type_newsletter
            from marketing_newsletter_sms
            where peoplemain_id = '{peoplemain_id}'
            and status in ('deliver', null)
            and type_newsletter in ('delay_credits_daily', 'daily_121', 'daily_180', 'sms_delay')
        ),
        email_cte as (
            select day_of_send::date
            from marketing_newsletter_email
            where peoplemain_id = '{peoplemain_id}'
            and type_of_newsletter in ('daily_91', 'daily_121', 'daily_150', 'daily_180')
        ),
        messeges_cte as (
         select *
         from dblink('{DBLINK_SLAVE}',
                     '   select messagedate
                         from messages
                         where users_id is not null -- сгенерирована вручную
                         and external_status_id in (1036, 1035)
                         and peoplemain_id = ''{peoplemain_id}''
                     '
                  ) as messeges(massagedate date)
        ),
        delay_sms_cte as (
            select name::int
            from delay_sms
            where disabled is null
            and name::int > 0
        )
        select *
        from (
                 select sum(this_day) as this_day
                 from (
                          select count(*) as this_day
                          from email_cte
                          where day_of_send = current_date
                          union all
                          select count(*) as this_day
                          from sms_cte
                          where day_of_send = current_date
                          union all
                          select count(*)
                          from messeges_cte
                          where massagedate = current_date
                          union all
                          select (case--strategy
                                      when 'delay_credits_daily' in (
                                          select type_newsletter
                                          from sms_cte
                                          where day_of_send = current_date
                                      ) then 0
                                      else
                                          (
                                              case
                                                  when {delay} in (
                                                      select name from delay_sms_cte
                                                  ) then 1
                                                  else 0
                                                  end
                                              )
                              end) as this_day
                          union all 
                          select (case--robot
                                      when {delay} in (1,2,3) then 1
                                      else 0
                              end) as this_day
                      ) a
             ) today_check,
             (
                 select sum(this_week) as this_week
                 from (
                          select count(*) as this_week
                          from email_cte
                          where to_char(day_of_send, 'IW') = to_char(current_date, 'IW')
                          union all
                          select count(*) as this_week
                          from sms_cte
                          where to_char(day_of_send, 'IW') = to_char(current_date, 'IW')
                          union all
                          select count(*)
                          from messeges_cte
                          where to_char(massagedate, 'IW') = to_char(current_date, 'IW')
                      ) a
             ) week_check,
             (
                 select sum(this_month) as this_month
                 from (
                          select count(*) as this_month
                          from email_cte
                          where to_char(day_of_send, 'MM') = to_char(current_date, 'MM')
                          union all
                          select count(*) as this_month
                          from sms_cte
                          where to_char(day_of_send, 'MM') = to_char(current_date, 'MM')
                          union all
                          select count(*)
                          from messeges_cte
                          where to_char(massagedate, 'MM') = to_char(current_date, 'MM')
                      ) a
             ) month_check,
             (
                 select array(select name from delay_sms_cte)
             ) ds
        """
    df_checker = pd.read_sql(query, con=PENTAHO)

    date_of_fisrt_day_of_next_month = datetime.date.today() + relativedelta(months=1, day=1)
    lastday_of_current_month = date_of_fisrt_day_of_next_month - datetime.timedelta(days=1)

    count_days_before_next_month = int(str(date_of_fisrt_day_of_next_month - datetime.date.today()).split()[0])

    days_before_monday = 7 - datetime.date.today().weekday()

    list_of_delays_before_monday = list(range(delay + 1, delay + days_before_monday))
    list_of_delays_current_week = list(range(delay - 7 + days_before_monday, delay + days_before_monday))

    list_of_delays_current_month = list(range(delay - int(lastday_of_current_month.day) +
                                              count_days_before_next_month, delay + count_days_before_next_month))
    list_of_delays_before_next_month = list(range(delay + 1, delay + count_days_before_next_month))

    list_names_of_sms_delays = df_checker.array.item()

    count_of_possible_robocalls_current_week = len(
        [x for x in list_of_delays_current_week if x in [1, 2, 3]]
    )

    count_of_possible_robocalls_current_month = len(
        [x for x in list_of_delays_current_month if x in [1, 2, 3]]
    )

    count_of_possible_sms_before_next_week = len(
        [x for x in list_of_delays_before_monday if x in list_names_of_sms_delays]
    )

    count_of_possible_sms_before_next_month = len(
        [x for x in list_of_delays_before_next_month if x in list_names_of_sms_delays]
    )

    if df_checker.this_month.item() + \
            count_of_possible_sms_before_next_month + count_of_possible_robocalls_current_month > 15:
        return f"В текущем месяце уведомить клиента невозможно, доступная дата отправки " \
               f"{str(date_of_fisrt_day_of_next_month)}"
    else:
        if df_checker.this_week.item() + count_of_possible_sms_before_next_week + \
                count_of_possible_robocalls_current_week > 3:
            return f"В текущую неделю уведомить клиента невозможно, доступная дата отправки " \
                   f"{datetime.date.today() + datetime.timedelta(days=days_before_monday)}"
        else:
            if df_checker.this_day.item() > 1:
                return f"""В текущий день уведомить клиента невозможно, доступная дата отправки завтра"""
            else:
                return 'success'


def check_info(creditaccount, fio, user_id):
    """
    Функция отправляет сообщение о просрочке клиенту по заданному номеру договора

    Происходит проверка существования записи в базе и привязки к текущему пользователю (check_creditaccount_and_fio)

    Если df содержит больше одной записи, то это непредвиденный случай, нужно рассматривать

    Если users_id пуст, то имя сотрудника не совпадает с привязанным к договору коллектором

    Происходит проверка на возможность отправки в текущую дату (check_delays)

    Проверяется возможность отправки в текущем timezone (check_timezone)
    """

    try:
        int(creditaccount)
    except ValueError:
        return 'error', 'Введенный номер договора содержит текствые символы'

    try:
        df = check_creditaccount_and_fio(creditaccount, fio)
    except ProgrammingError as e:
        SMSLog(
            text='Dataframe вернул критическую ошибку для creditaccount = ' + str(creditaccount) +
                 '\n error: ' + str(e) + '\n traceback: ' + str(traceback.format_exc()),
            user_id=1
        ).save()
        return 'error', ADMIN_ERROR

    if len(df) > 1:
        SMSLog(
            text='Dataframe вернул больше одной записи для creditaccount = ' + str(creditaccount),
            user_id=user_id
        ).save()
        return 'error', ADMIN_ERROR

    if df.empty:
        return 'error', 'Введенный номер договора не существует или уже закрыт'

    df_all_sms = creditaccount_info(df.peoplemain_id.item(), user_id)

    if df.users_id.item() is None:
        return 'error', 'Отправка сообщения невозможна, так как у вас в работе нет данного договора!', df_all_sms

    message = check_delays(df.peoplemain_id.item(), df.delay.item())

    if message == 'success':
        """ все ок, то проверяется, можно ли отправить сообщение в заданное время, где 3 - время МСК"""

        if df.timezone.item():
            message_timezone, message_part = check_timezone(3) # df.timezone.item() - 3
        else:
            mail_text = f'Номер в запросе creditaccount = {str(creditaccount)}, фио сотрудника: {fio}'
            SMSLog(text='Ошибка timezone ' + mail_text, user_id=user_id).save()

            send_mail('Ошибка timezone при проверке статуса в отправке смс по номеру договора',
                      mail_text,
                      'analysis@cash-u.com',
                      ['ogleznev@cash-u.com'],
                      fail_silently=True,
                      )
            return 'error', 'Ошибка! В системе отсутствует информация о часовом поясе клиента, ' \
                            'за дополнительной информацией обратитесь в техническую поддержку loandail.team'

        if message_timezone == 'success':
            text_to_send = TEXT_SMS# TEXT_SMS.replace('**', df.collector_phone.item()).replace('*', df.amount.item())

            return text_to_send, df.phone.item(), df.peoplemain_id.item(), df.users_id.item(), df.fio.item(), df_all_sms
        elif message_timezone == 'fail':
            return 'error', f"В текущий день уведомить клиента невозможно, " \
                            f"часовой пояс клиента МСК + ({str(df.timezone.item() - 3)}ч), " \
                            f"доступная дата отправки завтра " + message_part, df_all_sms
        else:
            SMSLog(text=message_timezone, user_id=user_id).save()
            return 'error', ADMIN_ERROR
    else:
        return 'error', message, df_all_sms
