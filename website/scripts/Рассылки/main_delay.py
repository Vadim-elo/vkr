# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 12:50:11 2019

@author: A_Nurutdinov
""" 
import pandas as pd 
import db_upload_delay as db
#import website.scripts.Рассылки.db_upload_delay as db
import time
from sqlalchemy import create_engine
import auxiliary_func_delay as func
import datetime as dt
from mysite.settings import db_analytics


now = dt.datetime.now().date()

df_db = db.onetime_sending_sms()


############## testing
#ip = ['1001','1002']
#value = ['','']
#gr = [1,15]
#cr_sum = [4300, 2100]
#coll_phone = [None,'79213131315']
#dftest = {'peoplemain_id': ip,'value': value,'client_group': gr,'cr_sum':cr_sum,'coll_phone':coll_phone}
#df_db = pd.DataFrame(dftest)
###########

markers = pd.unique(df_db['client_group']).tolist() 
dfrp = db.refused_phones()

dfcommon = pd.merge(df_db, dfrp, how='left',  left_on='value', right_on='phone')
df_clear = dfcommon.loc[dfcommon['id'].isnull()==True]
d = df_clear.rename(columns={'peoplemain_id_x' : 'peoplemain_id'})
df_db_pure = d[['peoplemain_id', 'value', 'client_group','cr_sum','coll_phone']].copy()

df_end = pd.DataFrame()
for i in markers:
    phones = df_db_pure.loc[df_db_pure['client_group']==i, 'value'].tolist()    
    cr_sum_list =  df_db_pure.loc[df_db_pure['client_group']==i, 'cr_sum'].tolist()
    coll_phone_list =  df_db_pure.loc[df_db_pure['client_group']==i, 'coll_phone'].tolist()  
    df_sms, bad_phones = func.sending(phones,i,cr_sum_list,coll_phone_list)
    state = df_sms['id_sms'].tolist()
    time.sleep(100) 
    df_status = func.status(state) 
    df_merge = pd.merge(df_sms, df_status, how='left')
    df_end = df_end.append(df_merge, ignore_index=True) 

df_temp = pd.merge(df_db_pure, df_end, how='inner', left_on='value', right_on='phone')

dfcopy = df_temp.copy()

#####################################################################################

####################################################################################   
    
#####################################################################################
def special_marks_definition(i):
    if i == 1:
        a = 'delay_daily_1d' 
    elif i == 11:
        a = 'delay_daily_11d'
    elif i == 15:
        a = 'delay_daily_15d' 
    elif i == 20:
        a = 'delay_daily_20d'  
    elif i == 28:
        a = 'delay_daily_28d' 
    elif i == 31:
        a = 'delay_daily_31d'
    elif i == 40:
        a = 'delay_daily_40d' 
    elif i == 58:
        a = 'delay_daily_58d' 
    return a
####################################################################################
    
dfcopy['type_newsletter'] = 'delay_credits_daily'
dfcopy['special_marks']=pd.Series(map(special_marks_definition,dfcopy['client_group']))
####################################################################################


df_to_db = pd.DataFrame(dfcopy, columns = ['peoplemain_id', 'value', 'client_group', 'id_sms', 'time', 'status', 
                                           'type_newsletter', 'promocode', 'special_marks'])
df_to_db['time'] = pd.to_datetime(df_to_db['time'])

engine_pentaho = create_engine(db_analytics)
df_to_db['day_of_send'] = now
df_to_db.to_sql('marketing_newsletter_sms', con=engine_pentaho, if_exists='append', index=False)
