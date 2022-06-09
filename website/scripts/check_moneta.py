import pandas as pd
from sqlalchemy import create_engine
import sqlalchemy
import datetime as dt
from pandas import ExcelWriter
import xlsxwriter
import warnings
import os
homepath = os.getenv('USERPROFILE')
warnings.simplefilter("ignore")
from mysite.settings import db_slave,db_analytics
import logging

logger = logging.getLogger('UpLoads_logging_moneta')
logger.setLevel(logging.INFO)
fh = logging.FileHandler("media/uploads/moneta/logs_moneta.txt")
fh.setLevel(logging.INFO)
formatter = logging.Formatter('#######################################################################################\n%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

def main(date_beg,date_end):
    try:
        date_beg = dt.datetime.strptime(date_beg, '%Y-%m-%d').date()
        date_end = dt.datetime.strptime(date_end, '%Y-%m-%d').date()
        engine_pentaho = create_engine(db_analytics)
        engine_slave = create_engine(db_slave)

        query = """select * from moneta_matching where "Date"::date between (:date_beg) and (:date_end)"""
        df = pd.read_sql(sqlalchemy.text(query), params={'date_beg': date_beg, 'date_end': date_end}, con=engine_pentaho)
        df = df.drop(['Date_loaded'], axis=1)

        query = """select distinct eventdate::timestamp, pr.id as "Client Transaction ID", c.peoplemain_id,  
        amount_operation , cd.credit_id  from creditdetails cd 
          left join
        (select id, peoplemain_id from credit where issameorg) c
        on c.id=cd.credit_id
          left join
            (select processdate, id, credit_id, p.amount, (select name from partners pt where pt.id=p.partners_id) as processor from payment p
            where paymenttype_id=317 and p.ispaid and processdate is not null) pr
            on pr.credit_id=cd.credit_id and cd.another_id=pr.id
        where operation_id=468 
        and eventdate::date>=(:date_beg) and eventdate::date<=(:date_end) and processor='MonetaRU'"""
        df1 = pd.read_sql(sqlalchemy.text(query), params={'date_beg': date_beg, 'date_end': date_end},
                          con=engine_slave)

        df2 = df[df['Category'] == 'BUSINESS'][df['Amount'] != 1][
            df['Amount'] != -1].copy()
        df_f = pd.merge(df1, df2, how='outer', on='Client Transaction ID')
        df_fn = df_f[df_f['peoplemain_id'].isnull() == True]
        df_fn1 = df_f[df_f['Category'].isnull() == True]
        df_fnl = pd.merge(df_fn, df_fn1, how='outer', on='Client Transaction ID')

        destination = 'media/uploads/moneta/moneta_yandex_' + (
            dt.datetime.now().strftime("%m-%d_%H-%M")) + '.xlsx'
        workbook = xlsxwriter.Workbook(destination)
        workbook.close()
        writer = ExcelWriter(destination)
        df_fnl.to_excel(writer, 'Moneta')

        query = """select eventdate::timestamp, pr.id as "Client Transaction ID", c.peoplemain_id,  
        pr.amount, cd.credit_id  from creditdetails cd 
          left join
        (select id, peoplemain_id from credit where issameorg) c
        on c.id=cd.credit_id
          left join
            (select processdate, id, credit_id, p.amount, (select name from partners pt where pt.id=p.partners_id) as processor from payment p
            where paymenttype_id=316 and p.ispaid and processdate is not null) pr
            on pr.credit_id=cd.credit_id and cd.another_id=pr.id
        where operation_id=465 
        and eventdate::date>=(:date_beg) and eventdate::date<=(:date_end) and processor='MonetaRU'"""
        df1_po = pd.read_sql(sqlalchemy.text(query),
                             params={'date_beg': date_beg, 'date_end': date_end}, con=engine_slave)
        df2_p = df[df['Category'] == 'WITHDRAWAL'][df['Amount'] >= -30000].copy()

        df_f_po = pd.merge(df1_po, df2_p, how='outer', on='Client Transaction ID')
        df_f_po['dif'] = df_f_po['amount'] + df_f_po['Amount']
        df_fnl_po = df_f_po[df_f_po['dif'] != 0]

        df_fnl_po.to_excel(writer, 'Moneta_po')
        writer.save()
        return destination
    except sqlalchemy.exc.OperationalError as e:
        logger.exception(e)
        return 'Ошибка подключения к серверу!'
    except Exception as e:
        logger.exception(e)
        return 'Возникла непредвиденная ошибка! Пожалуйста, обратитесь к администратору.'
