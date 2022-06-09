import datetime
import random
import traceback

import pandas
import json

from pandas import ExcelWriter
from  sqlalchemy.types import String

from sqlalchemy import create_engine, text

from mysite.settings import db_slave,  db_analytics
from website.models import UploadLog


def jParser(data):
    dataIn = json.loads(data)
    dataOut = {}
    dataOut['vat'] = dataIn['receipt']['items'][0]['vat']['type']
    dataOut['name'] = dataIn['receipt']['items'][0]['name']
    return dataOut

def load_receipts(path, user_id):
    try:
        df = pandas.read_csv(path, sep=';', encoding='windows-1251',
                             converters={'JSON входящего чека': jParser}, dtype={"External Id": str})
        df = df.join(df['JSON входящего чека'].apply(pandas.Series)).drop(
            ['Магазин', 'Моя компания', 'Источник данных', 'JSON входящего чека', 'JSON результата обработки'], axis=1)

        engine_pentaho = create_engine('')

        df_from_db = pandas.read_sql(text(
            f'''select "External Id" 
                        from atolreceipts 
                        where "External Id" in {str(tuple(df['External Id'].to_list()))}'''
        ), con=engine_pentaho)
        if int(len(df_from_db['External Id'])) > 0:
            df = df[~df['External Id'].isin(df_from_db['External Id'].to_list())]

        if df.empty:
            return 'Данные по чекам были внесены ранее!'
        else:
            df.to_sql('atolreceipts', if_exists='append', con=engine_pentaho, index=False,
                      dtype={"External Id": String()})
        return 'Загрузка прошла успешно!'
    except Exception:
        UploadLog(text='Атол-загрузка чеков: ' + traceback.format_exc(), user_id=user_id).save()
        return 'Возникла непредвиденная ошибка! Пожалуйста, обратитесь к администратору'

def check_dates(user_id):
    try:
        engine_pentaho = create_engine(db_analytics)
        df_check = pandas.read_sql(text(
            f'''select gs
                        from
                        (
                            select gs.gs, num
                            from
                            (
                                select generate_series('2021/06/01', (current_date-interval '1 day')::date, '1 day')::date as gs
                            ) gs
                            left join
                            (
                                select "Зарегистрирован на кассе"::date, count("Зарегистрирован на кассе") as num
                                from atolreceipts
                                group by 1
                                order by 1
                            ) a
                            on gs.gs=a."Зарегистрирован на кассе"
                        ) a
                        where num is null
                    '''
        ), con=engine_pentaho)
        result = 'Чеки не загружены за даты:   '
        check_list = df_check['gs'].to_list()
        if check_list:
            for gs in check_list:
                result = result + str(gs) + '     '
            return result
        else:
            ''
    except Exception:
        UploadLog(text='Атол - check_dates: ' + traceback.format_exc(), user_id=user_id).save()
        return 'Возникла непредвиденная ошибка! Пожалуйста, обратитесь к администратору'

def get_receipts(user_id, datebeg, dateend):
    try:
        engine_pentaho = create_engine(db_analytics)
        engine_slave = create_engine(db_slave)

        df_pentaho_1 = pandas.read_sql(text(
            f'''select * from atolreceipts 
                        where to_date(left("Зарегистрирован на кассе",10), 'YYYY-MM-DD') 
                        between to_date('{datebeg}', 'YYYY-MM-DD')
                        and to_date('{dateend}', 'YYYY-MM-DD') and "Тип чека" != 'Возврат прихода'
                    '''
        ), con=engine_pentaho)

        df_union_1 = pandas.read_sql(text(
            f'''with bq as (
                    SELECT id::text, credit_id, sum, date::text, ref_type_id 
                    from paidcomission 
                    where date::date
                    between to_date('{datebeg}', 'YYYY-MM-DD')
                    and to_date('{dateend}', 'YYYY-MM-DD') 
                    )
    
                select bq.*, b.* from bq
                left JOIN
                (
                    select transaction_id, transaction_status_id, paidinsurance_id::text, commission_id::text 
                    from receipts
                    where commission_id::text  in (select id from bq)
        
                )b
                ON bq.id = b.commission_id
                '''
        ), con=engine_slave)

        df_union_2 = pandas.read_sql(text(
            f'''with bq as (
                            SELECT id::text, credit_id, sum, date::text, ref_type_id 
        			        from paidinsurance 
                            where date::date
                            between to_date('{datebeg}', 'YYYY-MM-DD')
                            and to_date('{dateend}', 'YYYY-MM-DD') 
                            )

                        select bq.*, b.* from bq
                        left JOIN
                        (
                            select transaction_id, transaction_status_id, paidinsurance_id::text, commission_id::text 
                            from receipts
                            where paidinsurance_id::text  in (select id from bq)

                        )b
                        ON bq.id = b.paidinsurance_id
                        '''
        ), con=engine_slave)

        destination = 'media/receipts/out/receipts_' + datetime.datetime.now().strftime("%m-%d_") + str(random.randint(1001, 99999)) + '.xlsx'
        writer = ExcelWriter(destination)

        #print(df_pentaho_1)
        #print('----------------------------------------------')
        #print('----------------------------------------------')
        #print(df_union_1)
        df_union_1_out = df_union_1[~df_union_1['id'].isin(df_pentaho_1['External Id'])]
        #print(df_union_1_out)
        #print(' df_union_1_out')
        merge_1 = df_pentaho_1.merge(df_union_1, how='inner', left_on='External Id', right_on='id')
        #print(merge_1)
        #print('----------------------------------------------')

        #print(df_union_2)
        df_union_2_out = df_union_2[~df_union_2['id'].isin(df_pentaho_1['External Id'])]
        #print(df_union_2_out)
        #print('df_union_2_out')
        merge_2 = df_pentaho_1.merge(df_union_2, how='inner', left_on='External Id', right_on='id')
        #print(merge_2)
        #print('----------------------------------------------')
        concated_df = pandas.concat([merge_1, merge_2])
        concated_df = concated_df[concated_df['transaction_status_id'] != 1393]

        pandas.concat([df_union_1_out, df_union_2_out]).to_excel(writer,
                             sheet_name='Чеки не пробиты',
                             encoding='windows-1251')

        #print(concated_df, 'concated')

        df_nulls = pandas.read_sql(text(
            f'''select * from receipts where paidinsurance_id is NULL and commission_id is NULL 
                        and transaction_date between to_date('{datebeg}', 'YYYY-MM-DD')
                                             and to_date('{dateend}', 'YYYY-MM-DD') '''
        ), con=engine_slave)

        df_pentaho_2 = pandas.read_sql(text(
            f'''select * from atolreceipts 
                        where to_date(left("Зарегистрирован на кассе",10), 'YYYY-MM-DD') 
                        between to_date('{datebeg}', 'YYYY-MM-DD')
                        and to_date('{dateend}', 'YYYY-MM-DD') and "Тип чека" = 'Возврат прихода'
                    '''
        ), con=engine_pentaho)

        merge_nulls = df_pentaho_2.merge(df_nulls, how='outer', left_on='UUID чека', right_on='transaction_id')
        merge_nulls = merge_nulls[merge_nulls['transaction_status_id'] != 1410]

        pandas.concat([concated_df,merge_nulls]).to_excel(writer,
                                   sheet_name='Неверный статус чеков',
                                   encoding='windows-1251')

        writer.save()
        return destination
    except Exception:
        UploadLog(text='Атол - get_receipts: ' + traceback.format_exc(), user_id=user_id).save()
        return 'Возникла непредвиденная ошибка! Пожалуйста, обратитесь к администратору'
