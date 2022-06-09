# coding=utf8
import traceback

import pandas as pd
import requests
from fuzzywuzzy import fuzz

from mysite.settings import HEADERS_API, URL_API

ADMIN_ERROR = 'Ошибка поиска по базам! Пожалуйста, обратитесь к администратору, email: ogleznev@cash-u.com'


def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text


def format_bdate(bdate):
    if bdate:
        bdate_list = bdate.split('.')
        if bdate_list[0] == '__':
            bdate_list[0] = "0"
        elif bdate_list[0].startswith('_'):
            bdate_list[0] = bdate_list[0].replace('_', '')
        elif bdate_list[0].endswith('_'):
            bdate_list[0] = "99"

        if bdate_list[1] == '__':
            bdate_list[1] = "0"
        elif bdate_list[1].startswith('_'):
            bdate_list[1] = bdate_list[1].replace('_', '')
        elif bdate_list[1].endswith('_'):
            bdate_list[1] = "99"

        try:
            year_type = type(int(bdate_list[2]))
        except:
            year_type = str

        if year_type == str:
            bdate_list[2] = "0"
        bdate_list.append(True)
    else:
        return ['0', '0', '0', False]
    return bdate_list


def get_df(query_id, params):
    jsonAPI = {
        "query_id": query_id,
        "params": params
    }
    responseAPI = requests.post(URL_API, headers=HEADERS_API, json=jsonAPI)
    if responseAPI.status_code != 200:
        if responseAPI.json()['detail'] == 'Empty result':
            df = pd.DataFrame()
        else:
            return query_id, responseAPI.json()['detail'], ADMIN_ERROR
    else:
        df = pd.DataFrame().from_dict(responseAPI.json())
    return df


def get_phones(phone, bdate, name, midname, address):
    bdate_list = format_bdate(bdate)
    phone_replaced = replace_all(phone, {"(": "", ")": "", "-": "", ".": "", "_": "", " ": ""})

    df_kb = get_df(100, phone_replaced + ';' + str(bdate_list[2]) + ';' + str(bdate_list[2]) + ';' +
                   str(bdate_list[1]) + ';' + str(bdate_list[1]) + ';' + str(bdate_list[0]) + ';' +
                   str(bdate_list[0]))
    if type(df_kb) != pd.DataFrame:  # test
        return df_kb

    if not bdate_list[3]:
        df_rustel = get_df(101, phone_replaced)
        if type(df_rustel) != pd.DataFrame:
            return df_rustel
    else:
        df_rustel = pd.DataFrame()

    df_fbrus = get_df(102, phone_replaced + ';' + str(bdate_list[2]) + ';' + str(bdate_list[2]) + ';' +
                      str(bdate_list[1]) + ';' + str(bdate_list[1]) + ';' + str(bdate_list[0]) + ';' +
                      str(bdate_list[0]) + ';' + phone_replaced + ';' +
                      str(bdate_list[2]) + ';' + str(bdate_list[1]) + ';' + str(bdate_list[0]))
    if type(df_fbrus) != pd.DataFrame:
        return df_fbrus

    df = pd.concat([df_kb, df_rustel, df_fbrus], ignore_index=True)
    df.replace(to_replace=[None], value='', inplace=True)
    df = df.drop_duplicates()

    if name:
        name = name.lower()
        df = df.loc[df['name'].isin([name, name[0]])]
    if midname:
        midname = midname.lower()
        df = df.loc[df['middlename'].isin([midname, midname[0]])]
    if address:
        address = address.lower().replace("%", " ").split()

        for part in address:
            df = df[df['adr'].str.contains(part) | df['adr2'].str.contains(part)]
    return df


def get_fio(surname, name, midname, bdate, phone, address):
    try:
        bdate_list = format_bdate(bdate)
    except:
        raise IndexError(str(traceback.format_exc()) + f'bdate = ({str(bdate)}) - скобки для ограничения')

    surname = surname.lower()
    name = name.lower()
    midname = midname.lower()

    df_kb = get_df(103, surname + ';' + str(bdate_list[2]) + ';' + str(bdate_list[2]) + ';' +
                   str(bdate_list[1]) + ';' + str(bdate_list[1]) + ';' +
                   str(bdate_list[0]) + ';' + str(bdate_list[0]))
    if type(df_kb) != pd.DataFrame:
        return df_kb

    df_rusdem = get_df(104, surname + ';' + str(bdate_list[2]) + ';' + str(bdate_list[2]) + ';' +
                       str(bdate_list[1]) + ';' + str(bdate_list[1]) + ';' +
                       str(bdate_list[0]) + ';' + str(bdate_list[0]) + ';' + surname + ';' +
                       str(bdate_list[2]) + ';' + str(bdate_list[1]) + ';' + str(bdate_list[0]))
    if type(df_rusdem) != pd.DataFrame:
        return df_rusdem

    if not bdate_list[3]:
        df_rustel = get_df(105, surname)
        if type(df_rustel) != pd.DataFrame:
            return df_rustel
    else:
        df_rustel = pd.DataFrame()

    df_fbrus = get_df(106, surname + ';' + str(bdate_list[2]) + ';' + str(bdate_list[2]) + ';' +
                      str(bdate_list[1]) + ';' + str(bdate_list[1]) + ';' +
                      str(bdate_list[0]) + ';' + str(bdate_list[0]) + ';' + surname + ';' +
                      str(bdate_list[2]) + ';' + str(bdate_list[1]) + ';' + str(bdate_list[0]))
    if type(df_fbrus) != pd.DataFrame:
        return df_fbrus

    df = pd.concat([df_kb, df_rusdem, df_rustel, df_fbrus], ignore_index=True)
    df.replace(to_replace=[None], value='', inplace=True)

    if df.empty:
        return df, df
    else:
        df['total'] = df['total'].astype(int)
        if name == '':
            if midname == '':
                df_match = df
            else:
                df_match = df.loc[df['middlename'].isin([midname, midname[0]])]
        else:
            if midname == '':
                df_match = df.loc[df['name'].isin([name, name[0]])]
            else:
                df_match = df.loc[df['name'].isin([name, name[0]])].loc[df['middlename'].isin([midname, midname[0]])]

        df_match = df_match.drop_duplicates()
        df_sur_names = df[df.apply(lambda row: fuzz.token_sort_ratio(row['name'], name), axis=1) > 85].reset_index(
            drop=True)
        df_sur_mid = df[
            df.apply(lambda row: fuzz.token_sort_ratio(row['middlename'], midname), axis=1) > 85].reset_index(
            drop=True)
        df_sur = pd.concat([df_sur_mid, df_sur_names], ignore_index=True).drop_duplicates()

        df_sur = pd.merge(df_sur, df_match, how='outer', indicator=True)
        df_sur = df_sur.loc[df_sur._merge != 'both'].drop(['_merge'], axis=1)

        if phone:
            phone = replace_all(phone, {"(": "", ")": "", "-": "", ".": "", "_": "", " ": ""})
            df_sur = df_sur.loc[df_sur.phone == phone]
            df_match = df_match.loc[df_match.phone == phone]
        if address:
            address = address.lower().replace("%", " ").split()
            for part in address:
                df_sur = df_sur[df_sur['adr'].str.contains(part) | df_sur['adr2'].str.contains(part)]
                df_match = df_match[df_match['adr'].str.contains(part) | df_match['adr2'].str.contains(part)]
        return df_sur, df_match


def get_address(address, bdate, name, midname):
    bdate_list = format_bdate(bdate)
    address = "%" + address.lower().replace(" ", "%") + "%"

    df = get_df(107, address + ';' + str(bdate_list[2]) + ';' + str(bdate_list[2]) + ';' +
                str(bdate_list[1]) + ';' + str(bdate_list[1]) + ';' +
                str(bdate_list[0]) + ';' + str(bdate_list[0]) + ';' + address + ';' +
                str(bdate_list[2]) + ';' + str(bdate_list[2]) + ';' +
                str(bdate_list[1]) + ';' + str(bdate_list[1]) + ';' +
                str(bdate_list[0]) + ';' + str(bdate_list[0]) + ';' + address + ';' +
                str(bdate_list[2]) + ';' + str(bdate_list[1]) + ';' + str(bdate_list[0]) + ';' + address + ';' +
                str(bdate_list[2]) + ';' + str(bdate_list[1]) + ';' + str(bdate_list[0]))
    if type(df) != pd.DataFrame:
        return df

    df.replace(to_replace=[None], value='', inplace=True)
    df = df.drop_duplicates()

    if name:
        name = name.lower()
        df = df.loc[df['name'].isin([name, name[0]])]
    if midname:
        midname = midname.lower()
        df = df.loc[df['middlename'].isin([midname, midname[0]])]
    return df
