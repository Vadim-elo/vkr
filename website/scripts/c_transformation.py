#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
import zipfile

import pandas as pd
from sqlalchemy import create_engine
import sqlalchemy
from pandas import ExcelWriter
import logging
import os
from datetime import datetime

from mysite.settings import db_slave, db_analytics

logger = logging.getLogger('UpLoads_logging_1c')
logger.setLevel(logging.INFO)
fh = logging.FileHandler("media/uploads/1c/logs_1c.txt")
fh.setLevel(logging.INFO)
formatter = logging.Formatter('#######################################################################################\n%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

def main(data_beg,data_end):
    try:
        data_beg = datetime.strptime(data_beg, '%Y-%m-%d')
        data_end = datetime.strptime(data_end, '%Y-%m-%d')
        engine_pentaho = create_engine(db_analytics)
        engine = create_engine(db_slave)

        str_date ='media/uploads/1c/' + datetime.now().strftime("%d-%m-%Y--%H-%M")
        if os.path.exists(str_date):
            pass
        else:
            os.mkdir(str_date)

        cession = pd.read_sql(sqlalchemy.text("select id from cession_ids"), con=engine_pentaho)['id'].tolist()
        engine_pentaho.dispose()

        #1.Таблица выдачи займов
        query="""select c.id, cr.uniquenomer, cr.id as crid, pp.peoplemain_id, pp.surname, pp."name", pp.midname, 
        pp.gender, pp.birthdate, pp.birthplace,  
        d.series, d."number", d.docorgcode, d.docorg, d.docdate, p.processdate::timestamp, date(c.creditdatabeg), 
        (select eventenddate::date from creditdetails cd where cd.credit_id=c.id and operation_id=465)-c.creditdatabeg::date as srok, 
        (select eventenddate::date from creditdetails cd where cd.credit_id=c.id and operation_id=465) as credit_end_initial,
        c.creditdataendfact::timestamp, c.creditsum, c.creditpercent,
        a."index", a.region_name, a.region, a.area_ext, a.area_name, a.area, 
        a.place_ext, a.place_name, a.place, a.city_ext, a.city_name, a.city,
        a.district_name, a.district, a.street_ext, a.street_name, a.street, 
        a.house, a.corpus, a.building, a.flat, b.mobile_phone, b.email, b.work_phone,
        b.home_phone1, b.home_phone2,
        case when c.creditsum>=10000 then (select case when pti is null then 
            (select pti::numeric(10,2)
            from
            (select run_id, cast(value as int) as creditrequest_id from v_aimodelvalues_params where name = 'businessObjectId') a
            left join
            (select run_id, value as pti from v_aimodelvalues_params v where  name = 'pti') v
            on v.run_id=a.run_id
            where a.creditrequest_id =cr.id) 
        else pti end as pti from creditrequest cr where cr.acceptedcredit_id=c.id)*100 
        else 0 end as pti
        from credit c
        left join creditrequest cr on cr.id=c.creditrequest_id 
        left join
        (select pp.peoplemain_id, pp.surname, pp."name", pp.midname, pp.birthdate, pp.birthplace, pp.databeg, pp.gender
        from
        (select distinct pp.peoplemain_id, pp.surname, pp."name", pp.midname, pp.birthdate, pp.birthplace, pp.databeg, pp.gender,
        row_number() over (partition by pp.peoplemain_id order by pp.databeg desc) as num
        from peoplepersonal pp
        where pp.isactive=1 and pp.gender is not null
        group by 1,2,3,4,5,6,7,8
        order by 1) pp
        where pp.num=1) pp
        on c.peoplemain_id=pp.peoplemain_id
        left join
        (select d.creditrequest_id, d.peoplemain_id, d.series, d."number", d.docdate, d.docorg, d.docorgcode
        from
        (select distinct d.creditrequest_id, d.peoplemain_id, d.series, d."number", d.docdate, d.docorg, 
        row_number() over (partition by d.peoplemain_id order by docdate desc) as num, d.docorgcode
        from document d where partners_id=6
        group by 2,1,3,4,5,6,8
        order by 2) d where d.num=1) d
        on c.peoplemain_id=d.peoplemain_id
        left join
        (select p.credit_id, p.processdate from
        (select p.credit_id, p.processdate, 
        row_number() over (partition by p.credit_id order by p.processdate desc) as num
        from payment p where p.paymenttype_id=316 and ispaid
        group by 1,2
        order by 1) p
        where p.num=1) p on c.id=p.credit_id
        left join
        (select a.peoplemain_id, a."index", a.region_name, a.region, a.area_ext, a.area_name, a.area, 
        a.place_ext, a.place_name, a.place, a.city_ext, a.city_name, a.city,
        a.district_name, a.district, a.street_ext, a.street_name, a.street, 
        a.house, a.corpus, a.building, a.flat from
        (select distinct a.peoplemain_id, a."index", a.region_name, a.region, a.area_ext, a.area_name, a.area, 
        a.place_ext, a.place_name, a.place, a.city_ext, a.city_name, a.city,
        a.district_name, a.district, a.street_ext, a.street_name, a.street, 
        a.house, a.corpus, a.building, a.flat, a.partners_id, a.databeg,
        row_number() over (partition by a.peoplemain_id order by a.databeg desc) as num
        from address a where isactive=1 and a.partners_id=6 and a.addrtype=175
        group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24
        order by 1) a where a.num=1) a
        on a.peoplemain_id=c.peoplemain_id
        left join 
        (select peoplemain_id, -- добавление контактов клиента
        max(case when contact_id=171 then value else null end) as mobile_phone,
        max(case when contact_id=170 then value else null end) as email,
        max(case when contact_id=180 then value else null end) as work_phone,
        max(case when contact_id=172 then value else null end) as home_phone1,
        max(case when contact_id=251 then value else null end) as home_phone2
        from
        (select peoplemain_id, contact_id, value, row_number() over (partition by peoplemain_id,contact_id order by id desc) as num  
        from peoplecontact where contact_id in (170, 171, 172, 180, 251) and available) a
        where num=1 group by 1) b -- конец добавления контактов клиента
        on c.peoplemain_id=b.peoplemain_id
        where issameorg and processdate is not null and c.creditdatabeg::date between (:data_beg) and (:data_end)"""
        df=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end}, con=engine)

        #2.Таблица выдачи денежных средств по займам after 20/02/2020
        query="""with bq as (select distinct p.processdate::timestamp, p.id, c.peoplemain_id, pt.pay_operator, p.credit_id, p.amount  
                    from payment p
                    left join
                    (select peoplemain_id, id from credit where issameorg) c
                        on p.credit_id=c.id
                        left join
                    (select p.id, p.name as pay_operator from partners p) pt
                    on p.partners_id=pt.id
                    where paymenttype_id=316 and ispaid and p.credit_id in (select id from credit where issameorg and creditdatabeg>'2019-02-21 12:00:00.000')
                    and p.processdate::date>=(:data_beg) and p.processdate::date<=(:data_end))
        select a.*, premium_account, teledoctor, insurance
        from
            bq a
        left join
            (select (select acceptedcredit_id as credit_id from creditrequest c where c.id=r.creditrequest_id), 
            max(case when ref_type_id in (55,56,57) then sum/100 else null end) as premium_account,
            max(case when ref_type_id in (74,75,76) then sum/100 else null end) as teledoctor,
            sum(case when paidinsurance_id is not null then sum/100 else null end) as insurance
            from receipts r
            where transaction_date between (:data_beg) and (:data_end)
             and transaction_status_id not in (1394, 1410)
            group by 1) r
        on r.credit_id=a.credit_id
        order by 1"""
        df1=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end}, con=engine)
        df1.fillna(0, inplace=True)

        query="""select processdate, max(id) as id, peoplemain_id, credit_id,
        max(amount) as amount,
        sum(premium_account) as premium_account,
        sum(teledoctor) as teledoctor,
        sum(insurance_comission) as insurance_comission,
        sum(insurance_compensation) as insurance_compensation
        from
            (select refund_date::timestamp as processdate, id, 
            (select peoplemain_id from creditrequest c where c.id=r.creditrequest_id),
            (select acceptedcredit_id from creditrequest c where c.id=r.creditrequest_id) as credit_id,
            0 as amount, 
            max(case when ref_type_id in (55,56,57) then sum/100 else null end) as premium_account,
            max(case when ref_type_id in (74,75,76) then sum/100 else null end) as teledoctor,
            max(case when ref_type_id in (36,37,38) then sum/100 else null end) as insurance_comission, 
            max(case when ref_type_id in (17,18,19) then sum/100 else null end) as insurance_compensation
            from receipts r
            where transaction_status_id=1410
            and refund_date between (:data_beg) and (:data_end)
            group by 1,2,3,4) a
        group by 1,3,4"""
        df1_1=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end}, con=engine)
        df1_1.fillna(0, inplace=True)

        #3.Таблица начисления процентов
        query="""select eventdate, id, credit_id, percent from
            (select a.*, row_number() over (partition by credit_id, eventdate::date order by eventdate::time) as num
                                           from
                (select a.* from
                (select eventdate::timestamp, id, credit_id, dif as percent, operation_id from
                    (select id, operation_id, eventdate, credit_id,
                    amount_all - (lag(amount_all) over (partition by credit_id order by id)) as dif
                    from 
                        (select id, operation_id, eventdate, credit_id,
                         case when operation_id!=468 then amount_all else amount_percent+amount_all+(amount_operation-amount_percent-coalesce(amount_overpay,0)) end as amount_all
                         from creditdetails 
                        where operation_id in (1006, 467,468)) a
                    order by credit_id) a
                    where dif is not null and operation_id=468) a
                    where a.percent>0 and a.credit_id in (select id from credit where issameorg and creditdatabeg>'2019-02-21 12:00:00.000')
                and eventdate::date>=(:data_beg) and eventdate::date<=(:data_end)
            union																				 
                select a.* from
                (select eventdate::timestamp, id, credit_id, dif as percent, operation_id from
                    (select id, operation_id, eventdate, credit_id,
                    amount_all - (lag(amount_all) over (partition by credit_id order by eventdate)) as dif
                    from 
                        (select id, operation_id, eventdate, credit_id,
                         amount_all
                         from creditdetails 
                        where operation_id in (1006, 467)) a
                    order by credit_id) a
                    where dif is not null) a
                    where a.percent>=0 and a.credit_id in (select id from credit where issameorg and creditdatabeg>'2019-02-21 12:00:00.000')
                and eventdate::date>=(:data_beg) and eventdate::date<=(:data_end)
             union
                select a.* from
                (select eventdate::timestamp, id, credit_id, dif as percent, operation_id from
                    (select id, operation_id, eventdate, credit_id,
                    case when  amount_all - (lag(amount_all) over (partition by credit_id order by eventdate))=0
                     then amount_all - (lag(amount_all,2) over (partition by credit_id order by eventdate)) 
                     else amount_all - (lag(amount_all) over (partition by credit_id order by eventdate)) end as dif
                    from 
                        (select id, operation_id, eventdate, credit_id,
                         amount_all
                         from creditdetails 
                        where operation_id in (1006, 467,1544)) a
                    order by credit_id) a
                    where dif is not null and operation_id=1544) a
                    where a.percent>=0 and a.credit_id in (select id from credit where issameorg and creditdatabeg>'2019-02-21 12:00:00.000')
                and eventdate::date>=(:data_beg) and eventdate::date<=(:data_end)
            ) a
        ) a
        where num=1 or operation_id=1544 """
        df2=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end}, con=engine)

        #4.Таблица оплаты займов - прямые поступления
        query="""select distinct eventdate::timestamp, pr.id, c.peoplemain_id, pr.processor, 
        amount_operation - coalesce(amount_percent,0) - coalesce(amount_overpay,0) - coalesce(amount_penalty,0) as amount_main, 
        amount_percent, amount_overpay, cd.credit_id  from creditdetails cd 
          left join
        (select id, peoplemain_id from credit where issameorg) c
        on c.id=cd.credit_id
          left join
            (select processdate, id, credit_id, p.amount, (select name from partners pt where pt.id=p.partners_id) as processor from payment p
            where paymenttype_id=317 and p.ispaid and processdate is not null) pr
            on pr.credit_id=cd.credit_id and cd.another_id=pr.id
        where operation_id=468 and cd.credit_id in (select id from credit where issameorg and creditdatabeg>'2019-02-21 12:00:00.000')
        and eventdate::date>=(:data_beg) and eventdate::date<=(:data_end) and processor in ('MonetaRU', 'AlfaBank', 'Yandex') -- 'Yandex' с 19.04"""
        df3=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end}, con=engine)

        query="""select distinct eventdate::timestamp, pr.id, c.peoplemain_id, pr.processor, 
        amount_operation - coalesce(amount_percent,0) - coalesce(amount_overpay,0) - coalesce(amount_penalty,0) as amount_main, 
        amount_percent, amount_overpay, cd.credit_id  from creditdetails cd 
          left join
        (select id, peoplemain_id from credit where issameorg) c
        on c.id=cd.credit_id
          left join
            (select processdate, id, credit_id, p.amount, (select name from partners pt where pt.id=p.partners_id) as processor from payment p
            where paymenttype_id=317 and p.ispaid and processdate is not null) pr
            on pr.credit_id=cd.credit_id and cd.another_id=pr.id
        where operation_id=468 and cd.credit_id not in (select id from credit where issameorg and creditdatabeg>'2019-02-21 12:00:00.000')
        and cd.credit_id not in (select unnest(:cession))
        and eventdate::date>=(:data_beg) and eventdate::date<=(:data_end) and processor in ('MonetaRU')--, 'AlfaBank', 'Yandex') -- 'Yandex' с 19.04"""
        df3_1=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end, 'cession':cession}, con=engine)

        #4.1Таблица оплаты займов - погашения за счет переплат и бонусов
        query="""with bq as (select id, peoplemain_id, eventdate, amount, operationtype_id, credit_id, -- basequery
        case when credit_id in (select id from credit where issameorg and creditdatabeg>'2019-02-21 12:00:00.000') then 1 else 0 end as isNew
        from peoplesums)  -- basequery/ end
        select fnl.eventdate, fnl.id, fnl.peoplemain_id, 'Система' as processor,  
        amount_operation - coalesce(amount_percent, 0) - coalesce(amount_overpay) as amount_main,
        amount_percent, amount_overpay, fnl.credit_id,
        fnl.istochnik
        from
        (select fnl.* from
        (select eventdate::timestamp, id, peoplemain_id, -amount as amount, credit_id, 
        case when last_isnew=0 then 'сформировать приходник' else 'за счет переплат' end as istochnik
        from
            (select a.*, row_number() over w, lag(amount) over w last_a, lag(isnew) over w last_isnew
            from
                (select 1 as id, peoplemain_id, '2019/02/21' as eventdate, -- свод остатков переплат по МФУ
                amount, 450 as operationtype_id, 1 as credit_id, 0 as isnew
                from
                (select peoplemain_id, sum(amount) as amount from bq where isnew=0
                group by 1) a where amount>0   -- свод остатков переплат по МФУ/ конец
                union
                select bq.* from bq where isnew=1) a
            window w as (partition by peoplemain_id order by id)
            )a  
        where last_isnew is not null
        union
        select eventdate::timestamp, id, peoplemain_id, -amount as amount, credit_id, 
        'за счет бонусов' as istochnik
        from peoplebonus where credit_id in (select id from credit where issameorg and creditdatabeg>'2019-02-21 12:00:00.000')) fnl
        where eventdate::date>=(:data_beg) and eventdate::date<=(:data_end)) fnl
        left join creditdetails cd
         on cd.credit_id=fnl.credit_id and cd.eventdate::date=fnl.eventdate::date and cd.amount_operation=fnl.amount 
         where cd.operation_id=468"""
        df3_2=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end}, con=engine)

        #4.2. списания займов
        query="""select eventdate::timestamp, id, (select peoplemain_id from credit c where c.id=cd.credit_id),
        amount_operation-amount_percent as amount_main, amount_percent, credit_id
        from creditdetails cd 
        where operation_id=1184 and credit_id in (select id from credit where issameorg and creditdatabeg>'2019-02-21 12:00:00.000')
        and eventdate::date between (:data_beg) and (:data_end)"""
        df3_3=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end}, con=engine)

        #5.Таблица закрытия займов
        query="""select creditdataendfact::timestamp, id from credit where issameorg and creditdataendfact is not null
        and creditdatabeg>'2019-02-21 12:00:00.000' and creditdataendfact::date>=(:data_beg) and creditdataendfact::date<=(:data_end)"""
        df4=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end}, con=engine)

        #еаблица с платежами МФо на Кибер
        query="""select processdate::date, sum(case when partners_id=69 then amount else null end) as amount_moneta,
        sum(case when partners_id=15 then amount else null end ) as amount_schet,
        sum(case when partners_id=17 then amount else null end ) as amount_yandex
        from
        (select c.id, c.peoplemain_id, p.processdate,p.amount, partners_id
        from
        (select peoplemain_id, id from credit 
        where issameorg and creditdatabeg<='2019-02-21 12:00:17.448+03' and id not in (select unnest(:cession))) c
        left join
        payment p
        on p.credit_id=c.id
        where p.ispaid and partners_id=69 and paymenttype_id=317 or ispaid and partners_id=15 and externalid2!='' and paymenttype_id=317
        or p.ispaid and partners_id=17 and paymenttype_id=317) a
        where processdate::date>=(:data_beg) and processdate::date<=(:data_end)
        group by 1"""
        df6=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end, 'cession':cession}, con=engine)

        #Данные по пролонгациям
        query="""select id, credit_id, eventdate::date as longdate, eventenddate::date as creditdataend_new 
        from creditdetails 
        where operation_id in (466, 1540) and credit_id in (select id from credit where issameorg and creditdatabeg>'2019-02-21 12:00:00.000')
        and eventdate::date between (:data_beg) and (:data_end)"""
        df7=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end}, con=engine)

        name1 = '/1_C_output_' + (data_beg.strftime("%m-%d--%H-%M")) + '.xlsx'
        destination1 = str_date + name1
        writer = ExcelWriter(destination1)

        df.to_excel(writer, 'Sheet1')
        df1.to_excel(writer, 'Sheet2')
        df1_1.to_excel(writer, 'Sheet2-чеки возврата')
        df2.to_excel(writer, 'Sheet3')
        df3.to_excel(writer, 'Sheet4')
        df3_2.to_excel(writer, 'Sheet4_перепл-бонус')
        df3_3.to_excel(writer, 'Sheet4_списания')
        df4.to_excel(writer, 'Sheet5')
        df6.to_excel(writer, 'Sheet7')
        df7.to_excel(writer, 'Пролонгации')
        writer.save()

        #3.Таблица начисления процентов
        query="""select eventdate, id, credit_id, percent from
        (select a.*, row_number() over (partition by credit_id, eventdate::date order by eventdate::time) as num
                                       from
        (select a.* from
        (select eventdate::timestamp, id, credit_id, dif as percent, operation_id from
            (select id, operation_id, eventdate, credit_id,
            amount_all - (lag(amount_all) over (partition by credit_id order by id)) as dif
            from 
                (select id, operation_id, eventdate, credit_id,
                 case when operation_id!=468 then amount_all else amount_percent+amount_all+(amount_operation-amount_percent-coalesce(amount_overpay,0)) end as amount_all
                 from creditdetails 
                where operation_id in (1006, 467,468)) a
            order by credit_id) a
            where dif is not null and operation_id=468) a
            where a.percent>0.01 and a.credit_id  = ANY(:cession)
        and eventdate::date>=(:data_beg) and eventdate::date<=(:data_end)
        union																				 
        select a.* from
        (select eventdate::timestamp, id, credit_id, dif as percent, operation_id from
            (select id, operation_id, eventdate, credit_id,
            amount_all - (lag(amount_all) over (partition by credit_id order by eventdate)) as dif
            from 
                (select id, operation_id, eventdate, credit_id,
                 amount_all
                 from creditdetails 
                where operation_id in (1006, 467)) a
            order by credit_id) a
            where dif is not null) a
            where a.percent>=0 and a.credit_id = ANY(:cession)
        and eventdate::date>=(:data_beg) and eventdate::date<=(:data_end)) a) a
        where num=1 and percent!=0"""
        df2=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end, 'cession':cession}, con=engine)

        #4.Таблица оплаты займов - прямые поступления
        query="""select distinct eventdate::timestamp, pr.id, c.peoplemain_id, pr.processor, 
        amount_operation - amount_percent - coalesce(amount_overpay,0) - coalesce(amount_penalty,0) as amount_main, 
        amount_percent, amount_overpay, cd.credit_id  from creditdetails cd 
          left join
        (select id, peoplemain_id from credit where issameorg) c
        on c.id=cd.credit_id
          left join
            (select processdate, id, credit_id, p.amount, (select name from partners pt where pt.id=p.partners_id) as processor from payment p
            where paymenttype_id=317 and p.ispaid and processdate is not null) pr
            on pr.credit_id=cd.credit_id and cd.another_id=pr.id
        where operation_id=468 and cd.credit_id = ANY(:cession)
        and eventdate::date>=(:data_beg) and eventdate::date<=(:data_end) and processor in ('MonetaRU', 'AlfaBank', 'Yandex') -- 'Yandex' с 19.04"""
        df3=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end, 'cession':cession}, con=engine)

        #4.1Таблица оплаты займов - погашения за счет переплат и бонусов
        query="""with bq as (select id, peoplemain_id, eventdate, amount, operationtype_id, credit_id, -- basequery
        case when credit_id in (select id from credit where issameorg and creditdatabeg>'2019-02-21 12:00:00.000') then 1 else 0 end as isNew
        from peoplesums)  -- basequery/ end
        select fnl.eventdate, fnl.id, fnl.peoplemain_id, 'Система' as processor,  
        amount_operation - coalesce(amount_percent, 0) - coalesce(amount_overpay) as amount_main,
        amount_percent, amount_overpay, fnl.credit_id,
        fnl.istochnik
        from
        (select fnl.* from
        (select eventdate::timestamp, id, peoplemain_id, -amount as amount, credit_id, 
        case when last_isnew=0 then 'сформировать приходник' else 'за счет переплат' end as istochnik
        from
            (select a.*, row_number() over w, lag(amount) over w last_a, lag(isnew) over w last_isnew
            from
                (select 1 as id, peoplemain_id, '2019/02/21' as eventdate, -- свод остатков переплат по МФУ
                amount, 450 as operationtype_id, 1 as credit_id, 0 as isnew
                from
                (select peoplemain_id, sum(amount) as amount from bq where isnew=0
                group by 1) a where amount>0   -- свод остатков переплат по МФУ/ конец
                union
                select bq.* from bq where isnew=1) a
            window w as (partition by peoplemain_id order by id)
            )a  
        where last_isnew is not null
        union
        select eventdate::timestamp, id, peoplemain_id, -amount as amount, credit_id, 
        'за счет бонусов' as istochnik
        from peoplebonus where credit_id = ANY(:cession)) fnl
        where eventdate::date>=(:data_beg) and eventdate::date<=(:data_end)) fnl
        left join creditdetails cd
         on cd.credit_id=fnl.credit_id and cd.eventdate::date=fnl.eventdate::date and cd.amount_operation=fnl.amount 
         where cd.operation_id=468"""
        df3_2=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end, 'cession':cession}, con=engine)

        #4.2. списания займов
        query="""select eventdate::timestamp, id, (select peoplemain_id from credit c where c.id=cd.credit_id),
        amount_operation-amount_percent as amount_main, amount_percent, credit_id
        from creditdetails cd 
        where operation_id=1184 and credit_id = ANY(:cession)
        and eventdate::date between (:data_beg) and (:data_end)"""
        df3_3=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end, 'cession':cession}, con=engine)

        #5.Таблица закрытия займов
        query="""select creditdataendfact::timestamp, id from credit where issameorg and creditdataendfact is not null
        and id = ANY(:cession) and creditdataendfact::date>=(:data_beg) and creditdataendfact::date<=(:data_end)"""
        df4=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end, 'cession':cession}, con=engine)

        #Данные по пролонгациям
        query="""select id, credit_id, (eventdate+interval '1 day')::date as longdate, eventenddate::date as creditdataend_new 
        from creditdetails 
        where operation_id in (466,1540) and credit_id = ANY(:cession)
        and eventdate::date between (:data_beg) and (:data_end)"""
        df7=pd.read_sql(sqlalchemy.text(query), params={'data_beg':data_beg, 'data_end':data_end, 'cession':cession}, con=engine)
        engine.dispose()

        name2 = '/output_cession_'+(data_beg.strftime("%m-%d--%H-%M"))+'.xlsx'
        destination2 = str_date + name2
        writer = ExcelWriter(destination2)
        df2.to_excel(writer, 'Sheet3')
        df3.to_excel(writer, 'Sheet4')
        df3_2.to_excel(writer, 'Sheet4_перепл-бонус')
        df3_3.to_excel(writer, 'Sheet4_списания')
        df4.to_excel(writer, 'Sheet5')
        df7.to_excel(writer, 'Пролонгации')
        writer.save()

        file_location = str_date + '/1c_output_' + (data_beg.strftime("%m-%d--%H-%M")) + '.zip'
        to_zip = zipfile.ZipFile(file_location, 'w')
        to_zip.write(destination1, name1, compress_type=zipfile.ZIP_DEFLATED)
        to_zip.write(destination2, name2, compress_type=zipfile.ZIP_DEFLATED)
        to_zip.close()
        return file_location
    except sqlalchemy.exc.OperationalError as e:
        logger.exception(e)
        return 'Ошибка подключения к серверу!'
    except Exception as e:
        logger.exception(e)
        return 'Возникла непредвиденная ошибка! Пожалуйста, обратитесь к администратору.'