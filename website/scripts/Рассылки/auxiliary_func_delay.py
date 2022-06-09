# -*- coding: utf-8 -*-
from datetime import datetime

import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.sql import text as alchemy_text

from mysite.settings import db_analytics


def del_group(name, user):
    engine_pentaho = create_engine(db_analytics)
    disable = datetime.now()
    with engine_pentaho.connect() as conn:
        conn.execute(alchemy_text("UPDATE delay_sms SET disabled = :disabled WHERE name = :name and disabled IS NULL"),
                     name=str(name), disabled=disable, user=user)
        conn.close()
    return


def get_group():
    # engine_pentaho = create_engine(db_analytics)
    # q = "select * from delay_sms where disabled IS NULL order by name desc"
    # df = pd.read_sql(sqlalchemy.text(q), con=engine_pentaho)
    data = [['1', 'some text'], ['2', 'some text'], ['7', 'another text']]

    # Create the pandas DataFrame
    df = pd.DataFrame(data, columns=['name', 'text'])
    df = df.iloc[::-1]
    return df


def push_group(name, text, user):
    engine_pentaho = create_engine(db_analytics)
    q = "select true from delay_sms where name=:name and disabled IS NULL"
    df = pd.read_sql(sqlalchemy.text(q), con=engine_pentaho, params={"name": name})
    if df.empty:
        enable = datetime.now()
        disable = None
        pd.DataFrame({'name': [name],
                      'text': [text],
                      'user': [user],
                      'enabled': [enable],
                      'disabled': [disable],
                      }).to_sql('delay_sms', con=engine_pentaho, if_exists='append', index=False)
        return False
    else:
        return True


def split(lst, size):
    array = []
    while len(lst) > size:
        piece = lst[:size]
        array.append(piece)
        lst = lst[size:]
    array.append(lst)
    return array


def create_text(client_gr, cr_sum, coll_phone):
    text = []
    if (client_gr == 1 or client_gr == 5):
        for i in range(len(cr_sum)):
            text.append('Ваш заем просрочен на ' + str(
                cr_sum[i]) + ' руб! Срочно погасите долг. ООО МКК Киберлэндинг 8-800-505-07-75')
    elif (client_gr == 11):
        for i in range(len(coll_phone)):
            text.append(
                'У Вас имеется просроченная задолженность! Во избежание процедуры принудительного взыскания, просим срочно ее погасить. ООО МКК «Киберлэндинг», тел. ' + str(
                    coll_phone[i]))
    elif (client_gr == 15):
        for i in range(len(coll_phone)):
            text.append(
                'Ввиду наличия просроченной задолженности, Вам предварительно одобрена рассрочка по оплате займа. Свяжитесь с ООО МКК «Киберлэндинг», тел. ' + str(
                    coll_phone[i]))
    elif (client_gr == 20):
        for i in range(len(coll_phone)):
            text.append(
                'Ввиду неисполнения Вами обязательств по оплате займа, отсутствия контакта с компанией, инициирован выезд сотрудников по адресу регистрации. Свяжитесь с ООО МКК «Киберлэндинг», тел. ' + str(
                    coll_phone[i]))
    elif (client_gr == 28):
        for i in range(len(coll_phone)):
            text.append(
                'У Вас имеется просроченная задолженность! Уведомляем о возможной переуступке прав требования третьему лицу (продаже долга коллекторскому агентству). Свяжитесь с ООО МКК «Киберлэндинг», тел. ' + str(
                    coll_phone[i]))
    elif (client_gr == 31):
        for i in range(len(coll_phone)):
            text.append(
                'Ввиду неисполнения Вами обязательств по оплате займа, инициирована передача кредитного досье в "Бюро кредитных историй", с занесением в черный список. Свяжитесь с ООО МКК «Киберлэндинг», тел. ' + str(
                    coll_phone[i]))
    elif (client_gr == 40):
        for i in range(len(coll_phone)):
            text.append(
                'Ввиду наличия просроченной задолженности, для Вас имеется индивидуальное предложение о приостановлении начисления процентов. Свяжитесь с ООО МКК Киберлэндинг, перезвоните по тел. ' + str(
                    coll_phone[i]))
    elif (client_gr == 58):
        for i in range(len(coll_phone)):
            text.append(
                'У Вас имеется просроченная задолженность! Уведомляем, что судебный пристав вправе наложить арест на любой источник дохода (з/п, пособия, пенсия). Свяжитесь с ООО МКК «Киберлэндинг», тел. ' + str(
                    coll_phone[i]))
    return text
