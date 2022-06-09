# -*- coding: utf-8 -*-
import traceback

import requests
import json
import re
import hashlib

login = ''
password = ''
url = 'https://new.sms16.ru/get/timestamp.php'
api = ''
sender = ''
host = ''


def get_timestamp():
    """ Фунция получения timestamp"""
    cont = requests.get(url, timeout=10)
    r = re.findall('\d+', cont.content.decode("utf-8"))
    timestamp = r[0]
    return timestamp


def sending(phone, text, login=login, sender=sender, api=api):
    """ Фунция отправки смс"""
    try:
        timestamp = get_timestamp()
    except requests.Timeout:
        return '(send) get_timestamp requests.Timeout' + '\n' + str(traceback.format_exc()), 'timeout'



    draft_sms = login + phone + sender + text + timestamp + api
    hash_code_sms = hashlib.md5(draft_sms.encode()).hexdigest()

    url_send = ("https://new.sms16.ru/get/send.php?login=%s&signature=%s&phone=%s&text=%s&sender=%s&timestamp=%s"
                % (login, hash_code_sms, phone, text, sender, timestamp))

    response = 'no response yet'
    try:
        try:
            response = json.loads(requests.get(url_send, timeout=10).content.decode('utf-8'))
        except ConnectionError:
            return str(response) + '\n' + str(traceback.format_exc()), 'timeout'

        for resp, body_resp in response[0].items():
            try:
                return resp, body_resp['id_sms']
            except:
                return response.text, 'error'
        return response.text, 'error'
    except:
        return str(response) + '\n' + str(traceback.format_exc()), 'error'


def status(message, login=login, api=api):
    """ Фунция получения статуса отправки смс"""
    try:
        timestamp = get_timestamp()
    except requests.Timeout:
        return '(send) get_timestamp requests.Timeout' + '\n' + str(traceback.format_exc()), '', 'timeout'

    draft_status = login + message + timestamp + api
    hash_code_status = hashlib.md5(draft_status.encode()).hexdigest()

    url_send = ('https://new.sms16.ru/get/status.php?login=%s&signature=%s&state=%s&timestamp=%s'
                % (login, hash_code_status, message, timestamp))

    response = 'no response yet'
    try:
        while True:
            try:
                response = json.loads(requests.get(url_send, timeout=10).content.decode('utf-8'))
            except ConnectionError:
                return str(response) + '\n' + str(traceback.format_exc()), '', 'timeout'
            for resp, body_resp in response.items():
                try:
                    return resp, body_resp['time'], body_resp['status']
                except:
                    if response['error'] == 18:
                        return str(response), '', None
                    else:
                        return response.text, '', 'error'
    except:
        return str(response) + '\n' + str(traceback.format_exc()), '', 'error'
