import networkx as nx
from django.contrib.staticfiles import finders
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine

def LoadGraph(check_phone,check_card,check_ip):
    engine_pentaho = create_engine('')
    params_list = []
    if(check_phone == 'on'):
        params_list.append('phone')
    if (check_card == 'on'):
        params_list.append('card_number_masked')
    if (check_ip == 'on'):
        params_list.append('ipaddress')

    query = """
        select *
        from graph_edges_test
        where label = ANY(:params_list)
        """
    df_in_db = pd.read_sql(sqlalchemy.text(query), con=engine_pentaho, params={'params_list':params_list} )
    G = nx.from_pandas_edgelist(df_in_db, edge_attr=True)
    return G

def FindLinks(peoplemain_id,rad,check_phone,check_card,check_ip):
    G = LoadGraph(check_phone,check_card,check_ip)
    peoplemain_id = int(peoplemain_id)
    neighb = nx.ego_graph(G, peoplemain_id, radius=rad, undirected=True)
    # pos=nx.spring_layout(neighb)
    pos = nx.kamada_kawai_layout(neighb)
    for n in neighb.nodes:
        neighb.nodes[n]['viz'] = {'color': {'r': "170", 'b': "170", 'g': "170"}, 'size': 5,
                                  'position': {'x': pos[n][0], 'y': pos[n][1], 'z': 0}}
    neighb.nodes[peoplemain_id]['viz']['color'] = {'r': "200", 'b': "0", 'g': "0"}
    path = 'sigmaTest/static/sigmaTest/data/temp.gexf'
    nx.write_gexf(neighb, path )
    return path



def GetInfo(peoplemain_id):

    val = peoplemain_id
    peoplemain_id = int(peoplemain_id)
    engine = create_engine('')


    #### ФИО и дата рождения
    query = """
    select peoplemain_id, surname || ' ' || name || ' ' ||  midname as fio, birthdate
          from
          (
            select peoplemain_id, surname, name, case when midname is null then '' else midname end as midname, birthdate,
              row_number() over(partition by peoplemain_id order by databeg desc) as row_num
            from peoplepersonal
            where peoplemain_id = (:peoplemain_id)
          ) a
          where row_num = 1
    """
    try:
        df_fio = pd.read_sql(sqlalchemy.text(query), con=engine, params={'peoplemain_id': peoplemain_id})
    except Exception:
        return "Error with connecting to database"

    fio = df_fio['fio'].tolist()[0]
    if(len(fio) == 0):
        return "Data not found for this id"
    main_val = val + "<br>" + str(peoplemain_id) + "<br>" + fio
    return main_val