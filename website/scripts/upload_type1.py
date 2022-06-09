import datetime as dt
import json
import os
import random
import traceback
import warnings
import zipfile
from datetime import timedelta

import pandas as pd
import requests
import sqlalchemy
from sqlalchemy import create_engine

from mysite.settings import db_slave
from website.models import UploadLog

homepath = os.getenv('USERPROFILE')
warnings.simplefilter("ignore")

columns1 = ['fio', 'uniquenomer', 'sum', 'paydate']
columns1_other_errors = ['fio', 'uniquenomer', 'sum', 'paydate', 'error', 'externalnumber']

now = dt.datetime.now()


def new_payment1(row):
    date = (row[1]['paydate'] - dt.datetime(1970, 1, 1) + timedelta(hours=16) + timedelta(
        seconds=int(row[0]))).total_seconds() * 1000
    num = 'cy' + str(date) + str(random.randint(1001, 99999))
    date = int(date)
    payment = {
        "incomingPayment":
            {
                "date": date,
                "num": num,
                "payer": {
                    "id": int(row[1]['peoplemain_id']),
                    "name": row[1]['fio_y']
                },
                "contract": {
                    "id": int(row[1]['acceptedcredit_id']),
                    "num": row[1]['uniquenomer']
                },
                "sum": row[1]['sum']
            }
    }
    return payment


def main(path, user_id):
    try:
        engine = create_engine(db_slave)
        bd = pd.read_excel(path, names=columns1, engine='openpyxl', dtype={'uniquenomer': str})
        bd = bd.dropna(how='all')

        ids = list(map(str, bd['uniquenomer']))
        ids = [id.strip() for id in ids]

        if 'nan' in ids:
            raise ValueError
        query = """
                    with bq as 
                    (
                        select uniquenomer, peoplemain_id, acceptedcredit_id 
                        from creditrequest 
                        where acceptedcredit_id is not null and uniquenomer in (select unnest(:ids))
                    )
                    select bq.uniquenomer, bq.peoplemain_id, bq.acceptedcredit_id, a.fio
                    from bq
                    left join
                    (
                        select fio, peoplemain_id 
                        from
                        (
                            select surname||' '||name||' '||midname as fio, 
                                row_number() over (partition by peoplemain_id order by id desc) as num,
                                peoplemain_id
                            from peoplepersonal 
                            where peoplemain_id in (select peoplemain_id from bq) and partners_id=6
                        ) a
                        where num=1
                        ) a
                    on a.peoplemain_id=bq.peoplemain_id"""
        df1 = pd.read_sql(sqlalchemy.text(query), params={'ids': ids}, con=engine)

        dff = bd.merge(df1, how='left', left_on='uniquenomer', right_on='uniquenomer')

        work_df = dff.dropna(axis=0, subset=['peoplemain_id'])

        if work_df.empty:
            UploadLog(text='Тип-1: недостоточно платежей или не найдены в бд', user_id=user_id).save()
            return 'Не найдено платежей для загрузки'

        api_endpoint = ''
        api_user = ''
        api_password = ''
        auth = (api_user, api_password)
        headers = {'Content-type': 'application/json; charset=utf-8', 'Accept': 'application/json, text/plain, */*'}

        df_error_upload = pd.DataFrame(columns=columns1)
        df_error_upload_other_errors = pd.DataFrame(columns=columns1_other_errors)

        for row in work_df.iterrows():
            if row[1]['fio_x'] == row[1]['fio_y']:
                payment = new_payment1(row)

                response = requests.post(url=api_endpoint, auth=auth, json=payment, headers=headers)
                ans2 = json.loads(response.content.decode('utf-8'))
                if response.status_code != 200:
                    df_error_upload_other_errors = df_error_upload_other_errors.append(
                        {'fio': row[1]['fio_y'], 'uniquenomer': row[1]['uniquenomer'],
                         'sum': row[1]['sum'], 'paydate': row[1]['paydate'], 'error': ans2['error']['message'],
                         'externalnumber': payment['incomingPayment']['num']}, ignore_index=True)
                else:
                    pass
            else:
                df_error_upload = df_error_upload.append({'fio': row[1]['fio_y'], 'uniquenomer': row[1]['uniquenomer'],
                                                          'sum': row[1]['sum'], 'paydate': row[1]['paydate']},
                                                         ignore_index=True)

        file_name = '(1)_' + now.strftime("%m-%d_") + str(random.randint(1001, 99999))
        path_out = 'media/uploads/payments/type1/out/'
        adding_name = 'дозагрузка' + file_name + '.xlsx'
        errors_name = 'ошибки' + file_name + '.xlsx'
        path_adding = path_out + adding_name
        path_errors = path_out + errors_name

        with pd.ExcelWriter(path_adding) as writer:
            df_error_upload.to_excel(writer, index=False)
        with pd.ExcelWriter(path_errors) as writer:
            df_error_upload_other_errors.to_excel(writer, index=False, engine='openpyxl')

        to_zip = zipfile.ZipFile(path_out + 'загрузки' + file_name + '.zip', 'w')
        to_zip.write(path_adding, adding_name, compress_type=zipfile.ZIP_DEFLATED)
        to_zip.write(path_errors, errors_name, compress_type=zipfile.ZIP_DEFLATED)
        to_zip.close()
        return file_name + '.zip'
    except json.decoder.JSONDecodeError:
        UploadLog(text='Тип-1: ' + traceback.format_exc(), user_id=user_id).save()
        return 'Ошибка подключения к КМ! Попробуйте позже'
    except ValueError:
        UploadLog(text='Тип-1: ' + traceback.format_exc(), user_id=user_id).save()
        return 'Неправельные входные данные! Проверьте файл загрузок'
    except sqlalchemy.exc.OperationalError:
        UploadLog(text='Тип-1: ' + traceback.format_exc(), user_id=user_id).save()
        return 'Ошибка подключения к серверу! Попробуйте позже'
    except Exception:
        UploadLog(text='Тип-1: ' + traceback.format_exc(), user_id=user_id).save()
        return 'Возникла непредвиденная ошибка! Пожалуйста, обратитесь к администратору'
