# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 12:50:11 2019

@author: user
"""
import pandas as pd
from sqlalchemy import create_engine
import sqlalchemy
from mysite.settings import db_analytics, db_slave


def refused_phones():
    engine = create_engine(db_analytics)
    query = """
    select *
    from refused_phones
    """
    df = pd.read_sql(sqlalchemy.text(query), con=engine)
    return df

def onetime_sending_sms():
    engine=create_engine(db_slave)
    query="""
    with bq as (select credit_id, delay, (select peoplemain_id from credit c where c.id=a.credit_id), amount_all 
		from
		(select credit_id, 
		 case when delay is null then lead(delay) over (partition by credit_id, eventdate::date order by id desc) else delay end as delay, 
		row_number() over (partition by credit_id, eventdate::date order by id desc)  as num,
		amount_all
		from creditdetails
		where (eventdate at time zone 'msk')::date = current_date
		) a
	where num=1 and delay in (1,5,11,15,20,28,31,40,58)),
bq1 as (select bq.peoplemain_id, value,
	amount_all as cr_sum, delay as client_group, users_id, bq.credit_id
	from bq
	left join
		(select peoplemain_id, value, 
		row_number() over (partition by peoplemain_id order by id desc)  as num
		from peoplecontact 
		where partners_id=6 
		and contact_id =171 and value !='' and peoplemain_id in (select peoplemain_id from bq) 
		) a    
	on bq.peoplemain_id=a.peoplemain_id
	left join 
		(select * from collector where credit_id in (select credit_id from bq) and dataend is null) c
	on bq.credit_id=c.credit_id
	where value is not null and amount_all!=0)

select bq1.*, a.coll_phone
from bq1
left join
	(select peoplemain_id, value as coll_phone, (select id from users u where u.peoplemain_id=pc.peoplemain_id)
	 from peoplecontact pc
	 where peoplemain_id in 
	(select peoplemain_id from users where id in (select users_id from bq1))) a
on bq1.users_id=a.id
    """
    df=pd.read_sql(sqlalchemy.text(query), con=engine)
    df['type_of_newsletter'] = 'delay_credits_daily'
    return df 



def status_replay():
    engine_pentaho = create_engine(db_analytics)
    query = """
        select *
        from marketing_newsletter_sms
        where status is null and id_sms is not null
    """
    df_ws = pd.read_sql(sqlalchemy.text(query), con=engine_pentaho) #вытаскиваю записи без статусов
    return df_ws








