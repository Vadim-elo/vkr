# -*- coding: utf-8 -*-
import zipfile
import pandas as pd
from sqlalchemy import create_engine
import sqlalchemy
from pandas import ExcelWriter
from datetime import datetime
import logging
import os
from mysite.settings import db_slave, db_analytics

logger = logging.getLogger('UpLoads_logging_portfolio')
logger.setLevel(logging.INFO)
fh = logging.FileHandler("media/uploads/payments/logs_portfolio.txt")
fh.setLevel(logging.INFO)
formatter = logging.Formatter('#######################################################################################'
                              '\n%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
#data_end = datetime.strptime("2020-12-11", '%Y-%m-%d').strftime('%Y:%m:%d')

def main(data_end,percent_xlsx,main_xlsx,cession_total_xlsx,percent_cession_xlsx):
    try:
        data_end = datetime.strptime(data_end, '%Y:%m:%d')
        engine_pentaho = create_engine(db_analytics)
        engine=create_engine(db_slave)

        str_date = 'media/uploads/portfolio/out/' + datetime.now().strftime("%d-%m-%Y")
        if os.path.exists(str_date):
            pass
        else:
            os.mkdir(str_date)

        df=pd.read_excel(percent_xlsx)

        df1=pd.DataFrame(columns=['uniquenomer', 'amount_percent_1c'])
        df1['uniquenomer']=df['ООО МКК "Киберлэндинг"']
        df1['amount_percent_1c']=df['Unnamed: 6']
        df2=df1.dropna(subset=['uniquenomer']).copy()
        f=lambda x: x.startswith('10')
        df2['prefix']=df2['uniquenomer'].apply(f)
        df3=df2[df2['prefix']==True]
        df4=df3.drop(['prefix'],axis=1).copy()
        df4['uniquenomer']=df4['uniquenomer'].str.split(" ").str[0]

        df_m=pd.read_excel(main_xlsx)

        df1_m=pd.DataFrame(columns=['uniquenomer', 'amount_main_1c'])
        df1_m['uniquenomer']=df_m['ООО МКК "Киберлэндинг"']
        df1_m['amount_main_1c']=df_m['Unnamed: 6']
        df2_m=df1_m.dropna(subset=['uniquenomer']).copy()
        f=lambda x: x.startswith('10')
        df2_m['prefix']=df2_m['uniquenomer'].apply(f)
        df3_m=df2_m[df2_m['prefix']==True]
        df4_m=df3_m.drop(['prefix'],axis=1).copy()
        df4_m['uniquenomer']=df4_m['uniquenomer'].str.split(" ").str[0]
        one_c=pd.merge(df4_m,df4,how='outer',on='uniquenomer')
        one_c.fillna(0,inplace=True)

        query="""select credit_id, (select uniquenomer from creditrequest c where c.acceptedcredit_id=a.credit_id), delay, 
        case when operation_id in (465, 466) then 0 else amount_percent end as amount_percent, amount_main 
        from
        (select credit_id, operation_id, eventdate::date,
         case when delay is null then lead(delay) over (partition by credit_id, eventdate::date order by id desc) else delay end as delay, 
        row_number() over (partition by credit_id, eventdate::date order by eventdate::time desc)  as num,
        amount_all-amount_main as amount_percent, amount_main
        from creditdetails
        where 
        eventdate::date=(:data_end) and credit_id in (select id from credit where issameorg and creditdatabeg>'2019-02-21 12:00:00.000')
        ) a
        where delay is not null and num=1"""
        sptn=pd.read_sql(sqlalchemy.text(query),params={'data_end':data_end}, con=engine)

        fnl=pd.merge(one_c,sptn, how='outer', on='uniquenomer')
        fnl.fillna(0, inplace=True)

        name1 = '/portfolio_checkup.xlsx'
        destination1 = str_date + name1
        writer = ExcelWriter(destination1)

        fnl['od_diff']=fnl['amount_main']-fnl['amount_main_1c']
        fnl['perc_diff']=fnl['amount_percent']-fnl['amount_percent_1c']
        chq1=fnl[fnl['perc_diff']>=0.01]
        chq2=fnl[fnl['perc_diff']<=-0.01]
        chq_1=chq1.append(chq2)
        chq3=fnl[fnl['od_diff']>=0.01]
        chq4=fnl[fnl['od_diff']<=-0.01]
        chq_2=chq3.append(chq4)
        chq_f=chq_1.append(chq_2)
        fnl_chq=chq_f.drop_duplicates(keep='last')
        fnl_chq.to_excel(writer, 'results')

        writer.save()

        cession = pd.read_sql(sqlalchemy.text("select id from cession_ids"), con=engine_pentaho)['id'].tolist()
        engine_pentaho.dispose()

        t=pd.read_excel(cession_total_xlsx)
        t1=pd.DataFrame(columns=['uniquenomer', 'total_1c','main_1c','perc_1c'])
        t1['uniquenomer']=t['ООО МКК "Киберлэндинг"']
        n=0
        for i in t['ООО МКК "Киберлэндинг"']:
            if n<=len(t['ООО МКК "Киберлэндинг"'])-3:
                m=n+1
                p=n+2
                t1['main_1c'][n]=t['Unnamed: 6'][m]
                t1['perc_1c'][n]=t['Unnamed: 6'][p]
                n=n+1
        t1['total_1c']=t['Unnamed: 8']
        t2=t1.dropna(subset=['uniquenomer']).copy()
        f=lambda x: x.startswith('10')
        t2['prefix']=t2['uniquenomer'].apply(f)
        t3=t2[t2['prefix']==True]
        t4=t3.drop(['prefix'],axis=1).copy()
        t4['uniquenomer']=t4['uniquenomer'].str.split(" ").str[0]

        df=pd.read_excel(percent_cession_xlsx)
        df1=pd.DataFrame(columns=['uniquenomer', 'amount_percent_1c'])
        df1['uniquenomer']=df['ООО МКК "Киберлэндинг"']
        df1['amount_percent_1c']=df['Unnamed: 6']
        df2=df1.dropna(subset=['uniquenomer']).copy()
        f=lambda x: x.startswith('10')
        df2['prefix']=df2['uniquenomer'].apply(f)
        df3=df2[df2['prefix']==True]
        df4=df3.drop(['prefix'],axis=1).copy()
        df4['uniquenomer']=df4['uniquenomer'].str.split(" ").str[0]

        one_cess=pd.merge(t4,df4,how='outer', on=['uniquenomer'])
        one_cess.fillna(0, inplace=True)
        one_cess['perc_1c']=one_cess['perc_1c']+one_cess['amount_percent_1c']
        one_cession=one_cess.drop(columns=['total_1c','amount_percent_1c'], axis=1).copy()


        query="""select credit_id, (select uniquenomer from creditrequest c where c.acceptedcredit_id=a.credit_id), delay, 
        case when operation_id in (465, 466) then 0 else amount_percent end as amount_percent, amount_main 
        from
        (select credit_id, operation_id, eventdate::date,
         case when delay is null then lead(delay) over (partition by credit_id, eventdate::date order by id desc) else delay end as delay, 
        row_number() over (partition by credit_id, eventdate::date order by eventdate::time desc)  as num,
        amount_all-amount_main as amount_percent, amount_main
        from creditdetails
        where 
        eventdate::date=(:data_end) and credit_id in (select unnest(:cession))) a
        where delay is not null and num=1"""
        sptn=pd.read_sql(sqlalchemy.text(query),params={'cession':cession,'data_end':data_end}, con=engine)
        engine.dispose()

        fnl_cession=pd.merge(one_cession,sptn, how='outer', on='uniquenomer')
        fnl_cession['od_diff']=fnl_cession['amount_main']-fnl_cession['main_1c']
        fnl_cession['perc_diff']=fnl_cession['amount_percent']-fnl_cession['perc_1c']
        fnl_cession['checkup']=fnl_cession['perc_diff']+fnl_cession['od_diff']
        chq=fnl_cession[fnl_cession['checkup']!=0]
        chq1=fnl_cession[fnl_cession['checkup']>=0.01]
        chq2=fnl_cession[fnl_cession['checkup']<=-0.01]
        fnl_chq=chq1.append(chq2)

        name2 = '/portfolio_checkup_cession.xlsx'
        destination2 = str_date + name2
        writer = ExcelWriter(destination2)
        fnl_chq.to_excel(writer,'Sheet1')
        writer.save()

        to_zip = zipfile.ZipFile(str_date + '/portfolio_output.zip', 'w')
        to_zip.write(destination1, name1, compress_type=zipfile.ZIP_DEFLATED)
        to_zip.write(destination2, name2, compress_type=zipfile.ZIP_DEFLATED)
        to_zip.close()
        return 'portfolio_output'
    except sqlalchemy.exc.OperationalError as e:
        logger.exception(e)
        return 'Ошибка подключения к серверу!'
    except Exception as e:
        logger.exception(e)
        return 'Возникла непредвиденная ошибка! Пожалуйста, обратитесь к администратору.'