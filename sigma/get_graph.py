import networkx as nx
from django.contrib.staticfiles import finders
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
import os
from mysite.settings import db_analytics
from mysite.settings import db_slave 

SQLALCHEMY_DATABASE_URL = db_analytics
SQLALCHEMY_DATABASE_URL_SLAVE = db_slave 

def GetEdgesFromDB(list_id,params_list):
    engine_pentaho = create_engine(SQLALCHEMY_DATABASE_URL)

    query = """
    select "Source","Target","Label" as label
    from graph_edges
    where ("Source" = ANY(:list_id)
        or "Target"= ANY(:list_id))
        and "Label" = ANY(:params_list)
    """
    df_in_db = pd.read_sql(sqlalchemy.text(query), con=engine_pentaho, params={'params_list':params_list,'list_id': list_id})

    G = nx.from_pandas_edgelist(df_in_db, source='Source', target='Target', edge_attr=True)

    return G


def LoadGraph(peoplemain_id,check_phone,check_card,check_ip,check_email,radius):
    params_list = []
    if(check_phone == 'on'):
        params_list.append('phone')
    if (check_card == 'on'):
        params_list.append('card_number')
    if (check_ip == 'on'):
        params_list.append('ip_address')
    if (check_email == 'on'):
        params_list.append('email')

    G = GetEdgesFromDB(peoplemain_id,params_list)

    for i in range(1, radius):
        list_id = list(G.nodes)
        G = GetEdgesFromDB(list_id,params_list)

    return G

def FindLinks(peoplemain_id,rad,check_phone,check_card,check_ip,check_email):
    peoplemain_id = int(peoplemain_id)

    path = 'static/sigma/data/main.gexf'
    if os.path.isfile(path):
        os.remove(path)
    try:
        G = LoadGraph([peoplemain_id],check_phone,check_card,check_ip,check_email,rad)

        pos = nx.kamada_kawai_layout(G)
        for n in G.nodes:
            G.nodes[n]['viz'] = {'color': {'r': "170", 'b': "170", 'g': "170", 'a': "0.75"}, 'size': 5,
                                      'position': {'x': pos[n][0], 'y': pos[n][1], 'z': 0}}
        G.nodes[peoplemain_id]['viz']['color'] = {'r': "220", 'b': "0", 'g': "0", 'a': "0.75"}

        nx.write_gexf(G, path)
        return path
    except:
        return 'Error'


def GetInfo(peoplemain_id):

    peoplemain_id = int(peoplemain_id)
    engine = create_engine(SQLALCHEMY_DATABASE_URL_SLAVE )


    #### ФИО и дата рождения
    query = """
    select a.peoplemain_id, surname || ' ' || name || ' ' ||  midname as fio, birthdate, pc1.value as phone, pc2.value as email
          from
          (
            select peoplemain_id, surname, name, case when midname is null then '' else midname end as midname, birthdate,
              row_number() over(partition by peoplemain_id order by databeg desc) as row_num
            from peoplepersonal
            where peoplemain_id = (:peoplemain_id)
          ) a

    left join peoplecontact pc1 on pc1.peoplemain_id = a.peoplemain_id and pc1.partners_id=6 and pc1.contact_id =171 
    left join peoplecontact pc2 on pc2.peoplemain_id = a.peoplemain_id and pc2.partners_id=6 and pc2.contact_id =170
    where row_num = 1
    """
    try:
        df_personal = pd.read_sql(sqlalchemy.text(query), con=engine, params={'peoplemain_id': peoplemain_id})
    except Exception:
        return "Ну удалось подключиться к базе данных"

    fio = df_personal['fio'].tolist()[0]
    birthday = df_personal['birthdate'].tolist()[0]
    phone = df_personal['phone'].tolist()[0]
    email = df_personal['email'].tolist()[0]
    if(len(fio) == 0):
        return "Нет данных для этого id"
    main_val =  "peoplemain_id: " +str(peoplemain_id) + "<br>" + fio + "<br>" + "Дата рождения: " + str(birthday) + "<br>" + "Телефон: " + phone + "<br>" + "email: " + email
    return main_val