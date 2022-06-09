import logging
from datetime import datetime

import networkx
import pandas as pd
import requests

logger = logging.getLogger('VK')
logger.setLevel(logging.INFO)
fh = logging.FileHandler("vk_app/scripts/logs_vk.txt")
# fh = logging.FileHandler("logs_vk.txt")
fh.setLevel(logging.INFO)
formatter = logging.Formatter(
    '#######################################################################################\n%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

ACCESS_TOKEN = 'd603asdf7e1690d88a3asdgdsgdbfc3d3b5215320b'
API_VERSION = '5.126'
TIMEOUT = (6, 9)

URL_USERS_GET = 'https://api.vk.com/method/users.get'
URL_FRIENDS_GET = f'https://api.vk.com/method/friends.get'
URL_TAGS_GET = 'https://api.vk.com/method/photos.getTags'
URL_PHOTOS_GET = 'https://api.vk.com/method/photos.get'
URL_USER_PHOTOS_GET = 'https://api.vk.com/method/photos.getUserPhotos'
URL_GROUP_GET = 'https://api.vk.com/method/groups.getById'
URL_MUTUAL_GET = 'https://api.vk.com/method/friends.getMutual'
URL_FRIENDS_LISTS_GET = 'https://api.vk.com/method/friends.getLists'
URL_LIKES_LISTS_GET = 'https://api.vk.com/method/likes.getList'

base_payload = {'v': API_VERSION, 'access_token': ACCESS_TOKEN, 'timeout': TIMEOUT}


def get_likes_lists(owner_id, item_id):
    json_response = requests.get(URL_LIKES_LISTS_GET, params={
        **{'v': API_VERSION, 'access_token': ACCESS_TOKEN, 'timeout': TIMEOUT},
        **{'owner_id': owner_id,
           'item_id': item_id,
           'type': 'photo',
           'extended': 1},
    }).json()

    if json_response.get('error'):
        logger.exception(json_response.get('error'))
        return list()
    return json_response[u'response']


def get_friends_lists(id):
    json_response = requests.get(URL_FRIENDS_LISTS_GET, params={
        **{'v': API_VERSION, 'access_token': ACCESS_TOKEN, 'timeout': TIMEOUT},
        **{'user_id': id},
    }).json()

    if json_response.get('error'):
        logger.exception(json_response.get('error'))
        return list()
    return json_response[u'response']


def get_mutual(source_uid, target_uids):
    json_response = requests.get(URL_MUTUAL_GET, params={
        **{'v': API_VERSION, 'access_token': ACCESS_TOKEN, 'timeout': TIMEOUT},
        **{'source_uid': source_uid},
        **{'target_uids': target_uids}}).json()

    if json_response.get('error'):
        logger.exception(json_response.get('error'))
        return list()
    return json_response[u'response']


def get_group(group_id):
    json_response = requests.get(
        URL_GROUP_GET,
        params={
            **{'v': API_VERSION, 'access_token': ACCESS_TOKEN, 'timeout': TIMEOUT},
            **{'group_id': group_id}
        }
    ).json()

    if json_response.get('error'):
        logger.exception(json_response.get('error'))
        return list()
    return json_response[u'response']


def get_user_photos(user_id):
    json_response = requests.get(URL_USER_PHOTOS_GET, params={
        **{'v': API_VERSION, 'access_token': ACCESS_TOKEN, 'timeout': TIMEOUT},
        **{'user_id': user_id}}).json()

    if json_response.get('error'):
        logger.exception(json_response.get('error'))
        return list()
    return json_response[u'response']


def get_photos(user_id):
    json_response = requests.get(URL_PHOTOS_GET, params={
        **{'v': API_VERSION, 'access_token': ACCESS_TOKEN, 'timeout': TIMEOUT},
        **{'owner_id': user_id, 'rev': 1, 'extended': 1, 'count': 15, 'album_id': 'profile'}}).json()

    if json_response.get('error'):
        logger.exception(json_response.get('error'))
        return list()
    return json_response[u'response']


def get_tags(user_id):
    json_response = requests.get(URL_TAGS_GET, params={
        **{'v': API_VERSION, 'access_token': ACCESS_TOKEN, 'photo_id': '457244641', 'timeout': TIMEOUT},
        **{'owner_id': user_id}}).json()

    if json_response.get('error'):
        print(json_response.get('error'))
        return list()
    return json_response[u'response']


def get_friends(user_id):
    json_response = requests.get(URL_FRIENDS_GET, params={
        **{'v': API_VERSION, 'access_token': ACCESS_TOKEN, 'fields': 'bdate,domain,city, contacts, mutual_count',
           'timeout': TIMEOUT},
        **{'user_id': user_id}}).json()

    if json_response.get('error'):
        return json_response.get('error')
    return json_response[u'response']


def get_user(user_id):
    json_response = requests.get(URL_USERS_GET, params={
        **{'v': API_VERSION, 'access_token': ACCESS_TOKEN, 'fields': 'bdate,screen_name,relatives', 'timeout': TIMEOUT},
        **{'user_ids': user_id}}).json()

    if json_response.get('error'):
        return list()
    return json_response[u'response']


def get_gexf(df, center_name, path):
    G = networkx.from_pandas_edgelist(df, edge_attr=True)
    graph_vk = networkx.ego_graph(G, center_name, radius=1)
    pos = networkx.kamada_kawai_layout(graph_vk)

    for n in graph_vk.nodes:
        graph_vk.nodes[n]['viz'] = {'color': {'r': "0", 'b': "0", 'g': "255", 'a': "0.5"}, 'size': 1,
                                    'position': {'x': pos[n][0], 'y': pos[n][1], 'z': 0}}

    graph_vk.nodes[center_name]['viz']['color'] = {'r': "200", 'b': "0", 'g': "0", 'a': "0.5"}
    networkx.write_gexf(graph_vk, path)


def df_user_photos(id):
    if id.startswith('https://vk.com/id'):
        id = int(id.replace('https://vk.com/id', ''))
    else:
        id = id.replace('https://vk.com/', '')

    if type(id) == str:
        id = get_user(id)
        if len(id) == 0:
            return pd.DataFrame(), 'Ничего не найдено! Пожалуйста, проверьте правильность введенных данных.'
        else:
            id = id[0]['id']

    try:
        list_photos = []
        try:
            user_photos = get_user_photos(id)['items']
        except Exception as e:
            return pd.DataFrame(), 'Профиль данного пользователя является приватным или нет прав доступа!'
        for photo in user_photos[:6]:  # TODO :6 could be removed if timeout fixed
            if str(photo['owner_id']).startswith('-'):
                group = get_group(str(photo['owner_id']).strip('-'))
                type_str = 'Группа'
                name = group[0]['name']
                owner_id = 'https://vk.com/' + group[0]['screen_name']
            else:
                user = get_user(photo['owner_id'])
                type_str = 'Пользователь'
                name = user[0]['first_name'] + ' ' + user[0]['last_name']
                owner_id = 'https://vk.com/' + user[0]['screen_name']

            photo_link = ''
            for i in range(len(photo['sizes'])):
                if photo['sizes'][i]['type'] == 'm':
                    photo_link = photo['sizes'][i]['url']
                elif photo['sizes'][i]['type'] == 'o':
                    photo_link = photo['sizes'][i]['url']
                elif photo['sizes'][i]['type'] == 'p':
                    photo_link = photo['sizes'][i]['url']
                elif photo['sizes'][i]['type'] == 'q':
                    photo_link = photo['sizes'][i]['url']
                elif photo['sizes'][i]['type'] == 'r':
                    photo_link = photo['sizes'][i]['url']
                elif photo['sizes'][i]['type'] == 's':
                    photo_link = photo['sizes'][i]['url']
                elif photo['sizes'][i]['type'] == 'x':
                    photo_link = photo['sizes'][i]['url']
                elif photo['sizes'][i]['type'] == 'y':
                    photo_link = photo['sizes'][i]['url']
                elif photo['sizes'][i]['type'] == 'z':
                    photo_link = photo['sizes'][i]['url']
                elif photo['sizes'][i]['type'] == 'w':
                    photo_link = photo['sizes'][i]['url']
            list_photos.append(
                (datetime.fromtimestamp(photo['date']).strftime('%Y-%m-%d'), type_str, name, owner_id, photo_link))
        df = pd.DataFrame(list_photos, columns=['date_posted', 'type', 'name', 'owner_link', 'photo_link'])
        return df, 'Done'
    except Exception as e:
        raise
        return pd.DataFrame(), 'Непредвиденная ошибка! Пожалуйста, обратитесь к администратору!'


def friends_result(id):
    if id.startswith('https://vk.com/id'):
        id = int(id.replace('https://vk.com/id', ''))
    else:
        id = id.replace('https://vk.com/', '')

    target_name = get_user(id)[0]
    if type(id) == str:
        id = target_name['id']

    target_link = 'https://vk.com/id' + str(id)
    target_name_str = target_name['last_name'] + ' ' + target_name['first_name']

    try:
        target_rel = target_name['relatives']
        for key in target_rel:
            if key['type'] == 'child':
                key['type'] = 'Сын/Дочь'
            elif key['type'] == 'sibling':
                key['type'] = 'Брат/Сестра'
            elif key['type'] == 'parent':
                key['type'] = 'Отец/Мать'
            elif key['type'] == 'grandparant':
                key['type'] = 'Дедушка/Бабушка'
            elif key['type'] == 'grandchild':
                key['type'] = 'Внук/Внучка'
    except:
        pass

    friends = get_friends(id)
    friends_lists = get_friends_lists(id)

    friends_table = []
    i = 0
    friends_m = []
    try:
        return friends['error_msg']
    except:
        pass

    for friend in friends['items']:
        try:
            if friend['is_closed'] == False:
                friends_m.append(friend['id'])
        except:
            pass
        i = i + 1
        name = friend['last_name'] + ' ' + friend['first_name']
        try:
            if len(friend['bdate']) in {3, 4, 5}:
                bdate = friend['bdate'] + '.%'
            else:
                bdate = friend['bdate']
            if bdate[1] == '.':
                bdate = '0' + bdate
            if bdate[4] == '.':
                bdate = bdate[:3] + '0' + bdate[3:]
        except:
            bdate = '%'
        try:
            city = friend['city']['title']
        except:
            city = ''
        try:
            mobile = friend['mobile_phone']
        except:
            mobile = ''
        try:
            home_phone = friend['home_phone']
        except:
            home_phone = ''
        rel_type = []
        try:
            for rel in target_rel:
                if rel['id'] == friend['id']:
                    rel_type.append(rel['type'])
        except:
            pass

        try:
            rel_list = friend['lists']
            for rel in rel_list:
                for item in friends_lists['items']:
                    if item['id'] == rel:
                        rel_type.append(item['name'])
        except:
            pass
        relation = '/'.join(map(str, rel_type))

        friends_table.append((friend['id'],
                              name + ' % ' + bdate,
                              'https://vk.com/' + friend['domain'],
                              city,
                              relation,
                              mobile,
                              home_phone))

    df_friends = pd.DataFrame(friends_table,
                              columns=['id', 'name', 'link', 'city', 'relation', 'mobile_phone', 'home_phone'])

    def chunks(lst):
        for i in range(0, len(lst), 100):
            yield lst[i:i + 100]

    mutual_df_full = pd.DataFrame()
    list_chunk = list(chunks(friends_m))

    for item in range(len(list_chunk)):
        mutual_resp = get_mutual(id, ','.join(map(str, list_chunk[item])))
        mutual_df = pd.DataFrame(mutual_resp)
        mutual_df_full = pd.concat([mutual_df, mutual_df_full], ignore_index=True)

    try:
        df_finished = pd.merge(df_friends, mutual_df_full, on='id', how='outer')
    except KeyError:
        return 'Что-то пошло не так! Ошибка при поиске общих друзей!'

    df_finished['common_count'].fillna(0, inplace=True)
    df_finished['common_count'] = df_finished['common_count'].astype(int)
    """
    #----------------------------------------------------------------------------------------------
    #user_id = 176793100

    users_liked = []
    photos_15 = get_photos(id)['items']
    for photo in photos_15:
        users_liked = users_liked + get_likes_lists(id,photo['id'])['items']
    print(pd.DataFrame(users_liked))

    user_list= []
    for user in users_liked:
        user_list.append(user['id'])

    my_dict = {i: user_list.count(i) for i in user_list}
    dict_sorted = {k: v for k, v in sorted(my_dict.items(), key=lambda item: item[1], reverse=True)[:15]}

    print(dict_sorted)


    #list_fin.append({'id':id,'first_name':user['first_name'],'last_name':user['last_name']})

    for item in dict_sorted:
        item['']

        #print(item['likes'])
    """
    return df_finished, target_name_str, target_link


def vk_main():
    # my_id = 152715902
    id = 176793100

    target_name = get_user(id)[0]

    friends = get_friends(id)

    target_str_name = target_name['first_name'] + ' ' + target_name['last_name']

    graph = []

    for friend in friends['items']:
        name = friend['first_name'] + ' ' + friend['last_name']
        graph.append((target_str_name, name))

    df = pd.DataFrame(graph, columns=['source', 'target'])

    df['id'] = df.index
    path = 'static/temp.gexf'
    get_gexf(df, target_str_name, path)
    return path


# print('https://vk.com/'+get_user(176793100)[0]['screen_name']) #ссылка на пользователя
# print('https://vk.com/public'+str(176793100)) #ссылка на группу
# закрытый профиль 201997667

# pd.options.display.max_colwidth = 600

'''
print(get_photos(347890085))
p = get_photos(347890085)['items']
for item in p:
    print(item)
    if item['has_tags'] == True:
        print(item['id'])
print(p)
'''
