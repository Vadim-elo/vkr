# -*- coding: utf-8 -*-
import datetime
import re
import time
import traceback

from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import requests
import asyncio
import aiohttp
from mysite.settings import DEBUG, DEPLOY,HEADERS_API, URL_API
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from website.models import BiasLog

ADMIN_ERROR = 'Ошибка анкеты! Пожалуйста, обратитесь к администратору, email: ogleznev@cash-u.com'


def configure_driver():
    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    op.add_argument("--disable-infobars")
    op.add_argument("--disable-extensions")
    op.add_argument('--no-sandbox')
    op.add_argument('--disable-dev-shm-usage')
    if DEBUG and not DEPLOY:
        chrome_path = 'D:/Users/user/Documents/Разовые скрипты/chromedriver.exe'
    else:
        chrome_path = '/usr/bin/chromedriver'
    return webdriver.Chrome(chrome_path, options=op)


def get_bias(bias_login, bias_password, fio, bdate, input_phone, adr, _fio=''):
    df_1 = pd.DataFrame(columns=['fio', 'birthdate', 'birthplace'])
    df_2 = df_1

    if not (fio or bdate or input_phone or adr):
        return df_1, df_2, None, None, 'Заполните хотя бы одно поле'

    driver = configure_driver()

    driver.get("https://igls2.bias.ru/")

    # print(driver.page_source, flush=True)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "login")))
    elem_login = driver.find_element_by_id("login")
    elem_login.click()
    elem_login.send_keys(bias_login)

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "pwd")))
    elem_pwd = driver.find_element_by_id("pwd")
    elem_pwd.click()
    elem_pwd.send_keys(bias_password)

    driver.find_element_by_xpath("//button[@type='submit']").click()

    login_error = ''

    try:
        WebDriverWait(driver, 1).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".text-danger"))
        )
        elem_error = driver.find_elements_by_css_selector(".text-danger")
        if len(elem_error[0].text) == 0:
            time.sleep(1)
        if len(elem_error[0].text) > 0:
            login_error = 'Ошибка доступа! Пожалуйста, обратитесь к администратору'
    except Exception:
        pass

    if login_error:
        driver.close()
        driver.quit()
        return df_1,df_2, None, None, login_error

    if fio:
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "fullname"))
            )
        except:
            pass
        fio_elem = driver.find_element_by_id('fullname')
        fio_elem.click()

        condition = True
        ter_test = 0
        while condition:
            iter_test = ter_test + 1
            if iter_test > 10:
                BiasLog(text='fio-bias iter - ' + str(iter_test), user_id=1).save()
            fio_elem.send_keys(fio)
            fio_value = fio_elem.get_attribute("value")
            if fio_value != fio:
                fio_elem.clear()
            else:
                condition = False

    if bdate:
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "birthdate"))
            )
        except:
            pass
        birth_elem = driver.find_element_by_id('birthdate')
        birth_elem.click()

        condition = True
        ter_test = 0
        while condition:
            iter_test = ter_test + 1
            if iter_test > 10:
                BiasLog(text='fio-bias iter - ' + str(iter_test), user_id=1).save()
            birth_elem.send_keys(bdate)
            birth_value = birth_elem.get_attribute("value")

            if birth_value != bdate:
                birth_elem.clear()
            else:
                condition = False

    if input_phone:
        input_phone = input_phone.replace('+7','').replace(' ','').replace('-','').replace('(','').replace(')','')
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "phone"))
            )
        except:
            pass
        phone_elem = driver.find_element_by_id('phone')
        phone_elem.click()

        condition = True
        ter_test = 0
        while condition:
            iter_test = ter_test + 1
            if iter_test > 10:
                BiasLog(text='fio-bias iter - ' + str(iter_test), user_id=1).save()
            phone_elem.send_keys(input_phone)
            phone_value = phone_elem.get_attribute("value").replace(' ','').replace('-','')
            if phone_value != input_phone:
                phone_elem.clear()
            else:
                condition = False

    adr_error = False
    adr_bias = None
    if adr:
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Начните ввод и выберите из списка']"))
            )
            adr_elem = driver.find_element_by_xpath("//input[@placeholder='Начните ввод и выберите из списка']")
            adr_elem.click()

            condition = True
            ter_test = 0
            while condition:
                iter_test = ter_test + 1
                if iter_test > 10:
                    BiasLog(text='fio-bias iter - ' + str(iter_test), user_id=1).save()
                adr_elem.send_keys(adr)
                adr_value = adr_elem.get_attribute("value")
                if adr_value != adr:
                    adr_elem.clear()
                else:
                    condition = False

            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".dropdown-menu.ng-scope"))
            )

            adr_lis = driver.find_element_by_css_selector(".dropdown-menu.ng-scope").find_element_by_tag_name('li')
            adr_bias = adr_lis.text
            adr_lis.click()
        except:
            adr_error = True
            driver.close()
            driver.quit()
            return df_1,df_2, None,  adr_error, None
    driver.find_element_by_xpath("//button[@title='Искать']").click()

    text_error = ''
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".text-danger"))
        )
        elem_error = driver.find_elements_by_css_selector(".text-danger")
        if len(elem_error[0].text) == 0:
            time.sleep(2)
        if len(elem_error[0].text) > 0:
            text_error = elem_error[0].text
    except Exception:
        pass

    if text_error:
        driver.close()
        driver.quit()
        return df_1,df_2, None, None, text_error

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".panel.panel-default.searchitem.ng-scope"))
        )
    except:
        pass

    if _fio:
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, f"//a[text()='{_fio}']"))
            )
        except:
            pass

        original_window = driver.current_window_handle
        driver.find_element_by_xpath(f"//a[text()='{_fio}']").click()

        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break
        uid = driver.current_url.replace('https://igls2.bias.ru/card/','')

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//div[text()='Информация о поиске']")))

        title = driver.title[:-11]
        driver.close()
        driver.quit()
        return uid, title

    html = driver.page_source

    driver.close()
    driver.quit()
    match = BeautifulSoup(html, 'html.parser').find("div", {"class":"search-result"})

    div_list = []

    if len(match) > 0:
        elem = BeautifulSoup(str(match), 'html.parser').findAll(re.compile('div|p'),{"class":re.compile('row|font-bold')})
        if len(elem) > 0:
            check_p = True
            for e in elem:
                if e.has_attr('ng-if'):
                    check_p = False
                else:
                    row = BeautifulSoup(str(e), 'html.parser').find("a")
                    div_list.append(row.get_text())
                    divs = BeautifulSoup(str(e), 'html.parser').findAll("div", {"class": "ng-binding"})
                    if len(divs) > 0:
                        birthdate = ''
                        birthplace = ''
                        for div in divs:
                            if 'Дата рождения:' in div.get_text():
                                birthdate = div.get_text().replace('Дата рождения:', '').replace(' ', '').replace('\n',
                                                                                                                  '')
                                if len(birthdate) < 10:
                                    birthdate = ''

                            if 'Место рождения:' in div.get_text():
                                birthplace = div.get_text().replace('Место рождения:', '').replace('  ', '').replace(
                                    '\n', '')
                                if len(birthplace) < 3:
                                    birthplace = ''

                        div_list.append(birthdate)
                        div_list.append(birthplace)

                        div_list = [div_list]
                        if check_p:
                            df_1 = df_1.append(pd.DataFrame(div_list, columns=['fio', 'birthdate', 'birthplace']),
                                           ignore_index=True)
                            div_list = []
                        else:
                            df_2 = df_2.append(pd.DataFrame(div_list, columns=['fio', 'birthdate', 'birthplace']),
                                               ignore_index=True)
                            div_list = []
    #pd.options.display.max_columns = 10
    return df_1,df_2, adr_bias,adr_error,None
    #except Exception as e:
    #    BiasLog(text='--------: ' + str(e), user_id=1).save()
    return df_1, df_2, None, None, None

async def fetch(j_api, session,user_id):
    if type(j_api) == list:
        j = j_api[0]
        j_second = j_api[1]
    else:
        j = j_api
        j_second = {}
    async with session.post(URL_API, headers=HEADERS_API, json=j) as response:
        response_json = await response.json()
        if response.status != 200:
            if response_json['detail'] == 'Empty result':
                df = pd.DataFrame()
            else:
                BiasLog(text=f'query - {str(j["query_id"])}: ' + response_json['detail'], user_id=user_id).save()
                raise Exception
        else:
            try:
                response_success = response_json[0]
            except:
                response_success = ''
            try:
                last_id = str(response_json['last_id'])
            except:
                last_id = ''
            if response_success == 'success':
                return
            elif last_id:
                j_api_next = {
                    "query_id": j_second['query_id'],
                    "params": j_second['params'] + ';' + last_id
                }
                async with session.post(URL_API, headers=HEADERS_API, json=j_api_next) as response_second:
                    response_json_second = await response_second.json()
                    if response_second.status != 200:
                        BiasLog(text=f'query - {str(j_api_next["query_id"])}: ' + response_json_second['detail'],
                                user_id=user_id).save()
                        raise Exception
                return
            else:
                df = pd.DataFrame().from_dict(response_json)
        return {j["query_id"]:df}

async def fetch_many(loop, j_apis,user_id):
    async with aiohttp.ClientSession() as session:
        tasks = [loop.create_task(fetch(j_api, session,user_id)) for j_api in j_apis]
        return await asyncio.gather(*tasks)

def asnyc_aiohttp_get_all(j_api,user_id):
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(fetch_many(loop, j_api,user_id))

def add_profile(bias_login, bias_password,user_id,_fio,_birthdate,_input_phone,_birthplace,_adr, uid = ''):
    _input_phone = _input_phone.replace(' ', '').replace('-', '').replace(')', '').replace('(', '').replace('+7', '')
    if uid:
        data = {
            "login": bias_login,
            "password": bias_password,
            "timeout": 15,
            "uid": uid
        }
    else:
        data = {
            "login": bias_login,
            "password": bias_password,
            "timeout": 15,
            "services": [
                "600000"
            ],
            "searchFields": [
                {
                    "name": "fullname",
                    "value": _fio
                },
                {
                    "name": "birthdate",
                    "value": _birthdate
                },
                {
                    "name": "phone",
                    "value": _input_phone
                },
                {
                    "name": "fulladdress",
                    "value": _adr
                }
            ]
        }
        '''
        {
                    "name": "sernum",
                    "value": _pasp
                },
                {
                    "name": "issuedate",
                    "value": _biasdate
                },
                {
                    "name": "inn",
                    "value": _inn
                },
                {
                    "name": "snils",
                    "value": _bias_snils
                },
        '''

    headers = {
        "Content-Type": "text/json",
        "Accept": "text/json"
    }
    response = requests.post("https://igls2.bias.ru/api/request", headers=headers, json=data, verify=False)

    try:
        return response.json()['errors']
    except:
        pass
    jsonAPI = {
        "query_id": 5,
        "params": _fio + ';' + _birthdate + ';' + _input_phone + ';' + _adr + ';' + _birthplace
    }
    responseAPI = requests.post(URL_API, headers=HEADERS_API, json=jsonAPI)
    if responseAPI.status_code != 200:
        BiasLog(text='query - 5: ' + responseAPI.json()['detail'], user_id=user_id).save()
        return ADMIN_ERROR

    last_id = responseAPI.json()['last_id']

    j_apis = list()
    try:
        for person in response.json()['profiles'][0]['persons']:
            try:
                lastName = person['lastName']
            except:
                lastName = ''

            try:
                firstName = person['firstName']
            except:
                firstName = ''

            try:
                middleName = person['middleName']
            except:
                middleName = ''

            try:
                birthdate = person['birthdate']
            except:
                birthdate = ''

            try:
                birthplace = person['birthplace']
            except:
                birthplace = ''

            try:
                deathDate = person['deathDate']
            except:
                deathDate = ''

            jsonAPI = {
                "query_id": 6,
                "params": str(last_id) + ';' + lastName + ';' + firstName + ';' + middleName + ';' + birthdate + ';' + birthplace + ';' + deathDate
            }
            j_apis.append(jsonAPI)
    except KeyError:
        pass
    except Exception:
        BiasLog(text='add_profile-persons: ' + traceback.format_exc(), user_id=user_id).save()

    try:
        for phone in response.json()['profiles'][0]['phones']:
            try:
                number = phone['number'].replace(' ', '').replace('-', '').replace(')', '').replace('(', '').replace('+7','')
            except:
                number = ''

            try:
                isLandline = phone['isLandline']
            except:
                isLandline = ''

            try:
                regionName = phone['regionName']
            except:
                regionName = ''

            jsonAPI = {
                "query_id": 7,
                "params": str(
                    last_id) + ';' + number + ';' + isLandline + ';' + regionName
            }
            j_apis.append(jsonAPI)
    except KeyError:
        pass
    except Exception:
        BiasLog(text='add_profile-phones: ' + traceback.format_exc(), user_id=user_id).save()

    try:
        for organization in response.json()['profiles'][0]['organizations']:
            try:
                inn = organization['inn']
            except:
                inn = ''

            try:
                ogrn = organization['ogrn']
            except:
                ogrn = ''

            try:
                fullName = organization['fullName']
            except:
                fullName = ''

            try:
                shortName = organization['shortName']
            except:
                shortName = ''

            try:
                regionName = organization['regionName']
            except:
                regionName = ''

            try:
                regPlace = organization['regPlace']
            except:
                regPlace = ''

            try:
                regYear = organization['regYear']
            except:
                regYear = ''

            try:
                regDate = organization['regDate']
            except:
                regDate = ''

            try:
                endDate = organization['endDate']
            except:
                endDate = ''

            jsonAPI = {
                "query_id": 8,
                "params": str(last_id) + ';' + inn + ';' + ogrn + ';' + fullName.replace("'","''")+ ';' +
                          shortName.replace("'","''")+ ';' + regionName+ ';' + regPlace.replace("'","''")+ ';' +
                          regYear+ ';' + regDate+ ';' + endDate
            }
            j_apis.append(jsonAPI)
    except KeyError:
        pass
    except Exception:
        BiasLog(text='add_profile-organizations: ' + traceback.format_exc(), user_id=user_id).save()

    try:
        for entrepreneur in response.json()['profiles'][0]['entrepreneurs']:
            try:
                inn = entrepreneur['inn']
            except:
                inn = ''

            try:
                ogrn = entrepreneur['ogrn']
            except:
                ogrn = ''

            try:
                lastName = entrepreneur['lastName']
            except:
                lastName = ''

            try:
                firstName = entrepreneur['firstName']
            except:
                firstName = ''

            try:
                middleName = entrepreneur['middleName']
            except:
                middleName = ''

            try:
                regionName = entrepreneur['regionName']
            except:
                regionName = ''

            try:
                regPlace = entrepreneur['regPlace']
            except:
                regPlace = ''

            try:
                regYear = entrepreneur['regYear']
            except:
                regYear = ''

            try:
                regDate = entrepreneur['regDate']
            except:
                regDate = ''

            try:
                endDate = entrepreneur['endDate']
            except:
                endDate = ''

            jsonAPI = {
                "query_id": 9,
                "params": str(last_id) + ';' + inn + ';' + ogrn + ';' + lastName + ';' + firstName + ';' + middleName + ';' +
                          regionName + ';' + regPlace.replace("'","''") + ';' + regYear + ';' + regDate + ';' + endDate
            }
            j_apis.append(jsonAPI)
    except KeyError:
        pass
    except Exception:
        BiasLog(text='add_profile-entrepreneurs: ' + traceback.format_exc(), user_id=user_id).save()

    try:
        for vehicle in response.json()['profiles'][0]['vehicles']:
            try:
                vin = vehicle['vin']
            except:
                vin = ''

            try:
                regPlate = vehicle['regPlate']
            except:
                regPlate = ''

            try:
                brand = vehicle['brand']
            except:
                brand = ''

            try:
                model = vehicle['model']
            except:
                model = ''

            try:
                color = vehicle['color']
            except:
                color = ''

            try:
                manufactureYear = vehicle['manufactureYear']
            except:
                manufactureYear = ''

            jsonAPI = {
                "query_id": 10,
                "params": str(last_id) + ';' + vin + ';' + regPlate + ';' + brand.replace("'","''") + ';' +
                          model.replace("'","''") + ';' + color + ';' + manufactureYear
            }
            j_apis.append(jsonAPI)
    except KeyError:
        pass
    except Exception:
        BiasLog(text='add_profile-vehicles: ' + traceback.format_exc(), user_id=user_id).save()

    try:
        for estate in response.json()['profiles'][0]['estates']:
            try:
                cadNum = estate['cadNum']
            except:
                cadNum = ''

            try:
                description = estate['description']
            except:
                description = ''

            jsonAPI = {
                "query_id": 11,
                "params": str(last_id) + ';' + cadNum + ';' + description.replace("'","''")
            }
            j_apis.append(jsonAPI)
    except KeyError:
        pass
    except Exception:
        BiasLog(text='add_profile-estates: ' + traceback.format_exc(), user_id=user_id).save()

    try:
        for address in response.json()['profiles'][0]['addresses']:
            try:
                value = address['value']
            except:
                value = ''

            jsonAPI = {
                "query_id": 12,
                "params": str(last_id) + ';' + value
            }
            j_apis.append(jsonAPI)
    except KeyError:
        pass
    except Exception:
        BiasLog(text='add_profile-addresses: ' + traceback.format_exc(), user_id=user_id).save()

    try:
        for document in response.json()['profiles'][0]['documents']:
            try:
                typeDisplayName = document['typeDisplayName']
            except:
                typeDisplayName = ''

            try:
                serNum = document['serNum']
            except:
                serNum = ''

            try:
                issueDate = document['issueDate']
            except:
                issueDate = ''

            try:
                issuer = document['issuer']
            except:
                issuer = ''

            try:
                departmentCode = document['departmentCode']
            except:
                departmentCode = ''

            try:
                isExpired = document['isExpired']
            except:
                isExpired = ''

            try:
                expirationReason = document['expirationReason']
            except:
                expirationReason = ''

            jsonAPI = {
                "query_id": 13,
                "params": str(last_id) + ';' + typeDisplayName.replace("'","''")+ ';' + serNum+ ';' + issueDate+ ';' + issuer+ ';' +
                          departmentCode+ ';' + str(isExpired)+ ';' + expirationReason.replace("'","''")
            }
            j_apis.append(jsonAPI)
    except KeyError:
        pass
    except Exception:
        BiasLog(text='add_profile-documents: ' + traceback.format_exc(), user_id=user_id).save()

    try:
        for negative in response.json()['profiles'][0]['negatives']:
            try:
                typeDisplayName = negative['typeDisplayName']
            except:
                typeDisplayName = ''

            try:
                tags = negative['tags']
                tags_str = ''
                for tag in tags:
                    tags_str = tags_str + tag + ''
            except:
                tags_str = ''

            try:
                atDate = negative['atDate']
            except:
                atDate = ''

            try:
                article = negative['article']
            except:
                article = ''

            try:
                multilineText = negative['multilineText']
            except:
                multilineText = ''

            jsonAPI = {
                "query_id": 14,
                "params": str(last_id) + ';' + typeDisplayName.replace("'","''") + ';' +
                          tags_str.replace("'","''") + ';' + atDate + ';' + article.replace("'","''") + ';' +
                          multilineText.replace("'","''")
            }
            j_apis.append(jsonAPI)
    except KeyError:
        pass
    except Exception:
        BiasLog(text='add_profile-negatives: ' + traceback.format_exc(), user_id=user_id).save()

    try:
        for addition in response.json()['profiles'][0]['additions']:
            try:
                atDate = addition['atDate']
            except:
                atDate = ''

            try:
                multilineText = addition['multilineText']
            except:
                multilineText = ''

            jsonAPI = {
                "query_id": 15,
                "params": str(last_id) + ';' + atDate + ';' + multilineText.replace("'","''")
            }
            j_apis.append(jsonAPI)
    except KeyError:
        pass
    except Exception:
        BiasLog(text='add_profile-additions: ' + traceback.format_exc(), user_id=user_id).save()

    try:
        for linkedProfile in response.json()['profiles'][0]['linkedProfiles']:
            try:
                linkTypeDisplayName = linkedProfile['linkTypeDisplayName']
            except:
                linkTypeDisplayName = ''
            jsonAPI_list = list()
            try:
                for linkedPerson in linkedProfile['profile']['persons']:
                    try:
                        lastName = linkedPerson['lastName']
                    except:
                        lastName = ''

                    try:
                        firstName = linkedPerson['firstName']
                    except:
                        firstName = ''

                    try:
                        middleName = linkedPerson['middleName']
                    except:
                        middleName = ''

                    try:
                        birthdate = linkedPerson['birthdate']
                    except:
                        birthdate = ''

                    try:
                        birthplace = linkedPerson['birthplace']
                    except:
                        birthplace = ''

                    try:
                        deathDate = linkedPerson['deathDate']
                    except:
                        deathDate = ''

                    jsonAPI_list[:] = []
                    jsonAPI = {
                        "query_id": 16,
                        "params": lastName+ ';' + firstName + ';' + middleName+ ';' + birthdate+ ';' +
                                  birthplace+ ';' + deathDate
                    }
                    jsonAPI_list.append(jsonAPI)

                    jsonAPI = {
                        "query_id": 17,
                        "params": str(last_id) + ';' + linkTypeDisplayName
                    }
                    jsonAPI_list.append(jsonAPI)
                    j_apis.append(jsonAPI_list)
            except KeyError:
                pass
            except Exception:
                BiasLog(text='add_profile-linked-profile-persons: ' + traceback.format_exc(), user_id=user_id).save()

            try:
                for linkedOrganization in linkedProfile['profile']['organizations']:
                    try:
                        inn = linkedOrganization['inn']
                    except:
                        inn = ''

                    try:
                        ogrn = linkedOrganization['ogrn']
                    except:
                        ogrn = ''

                    try:
                        fullName = linkedOrganization['fullName']
                    except:
                        fullName = ''

                    try:
                        shortName = linkedOrganization['shortName']
                    except:
                        shortName = ''

                    try:
                        regionName = linkedOrganization['regionName']
                    except:
                        regionName = ''

                    try:
                        regPlace = linkedOrganization['regPlace']
                    except:
                        regPlace = ''

                    try:
                        regYear = linkedOrganization['regYear']
                    except:
                        regYear = ''

                    try:
                        regDate = linkedOrganization['regDate']
                    except:
                        regDate = ''

                    try:
                        endDate = linkedOrganization['endDate']
                    except:
                        endDate = ''

                    jsonAPI_list[:] = []
                    jsonAPI = {
                        "query_id": 18,
                        "params": inn + ';' + ogrn + ';' + fullName.replace("'","''") + ';' + shortName.replace("'","''") + ';' +
                                  regionName + ';' + regPlace.replace("'","''")+ ';' + regYear+ ';' + regDate+ ';' + endDate
                    }
                    jsonAPI_list.append(jsonAPI)

                    jsonAPI = {
                        "query_id": 19,
                        "params": str(last_id) + ';' + linkTypeDisplayName
                    }
                    jsonAPI_list.append(jsonAPI)
                    j_apis.append(jsonAPI_list)
            except KeyError:
                pass
            except Exception:
                BiasLog(text='add_profile-linked-profile-organizations: ' + traceback.format_exc(), user_id=user_id).save()

            try:
                for linkedEstate in linkedProfile['profile']['estates']:
                    try:
                        cadNum = linkedEstate['cadNum']
                    except:
                        cadNum = ''

                    try:
                        description = linkedEstate['description']
                    except:
                        description = ''

                    jsonAPI_list[:] = []
                    jsonAPI = {
                        "query_id": 20,
                        "params": cadNum + ';' + description.replace("'","''")
                    }
                    jsonAPI_list.append(jsonAPI)

                    jsonAPI = {
                        "query_id": 21,
                        "params": str(last_id) + ';' + linkTypeDisplayName
                    }
                    jsonAPI_list.append(jsonAPI)
                    j_apis.append(jsonAPI_list)
            except KeyError:
                pass
            except Exception:
                BiasLog(text='add_profile-linked-profile-estates: ' + traceback.format_exc(), user_id=user_id).save()

            try:
                for linkedVehicle in linkedProfile['profile']['vehicles']:
                    try:
                        vin = linkedVehicle['vin']
                    except:
                        vin = ''

                    try:
                        regPlate = linkedVehicle['regPlate']
                    except:
                        regPlate = ''

                    try:
                        brand = linkedVehicle['brand']
                    except:
                        brand = ''

                    try:
                        model = linkedVehicle['model']
                    except:
                        model = ''

                    try:
                        color = linkedVehicle['color']
                    except:
                        color = ''

                    try:
                        manufactureYear = linkedVehicle['manufactureYear']
                    except:
                        manufactureYear = ''

                    jsonAPI_list[:] = []
                    jsonAPI = {
                        "query_id": 22,
                        "params": vin + ';' + regPlate+ ';' + brand.replace("'","''")+ ';' + model.replace("'","''")+ ';' +
                                  color+ ';' + manufactureYear
                    }
                    jsonAPI_list.append(jsonAPI)

                    jsonAPI = {
                        "query_id": 23,
                        "params": str(last_id) + ';' + linkTypeDisplayName
                    }
                    jsonAPI_list.append(jsonAPI)
                    j_apis.append(jsonAPI_list)
            except KeyError:
                pass
            except Exception:
                BiasLog(text='add_profile-linked-profile-vehicles: ' + traceback.format_exc(), user_id=user_id).save()

            try:
                for linkedEntrepreneur in linkedProfile['profile']['entrepreneurs']:
                    try:
                        inn = linkedEntrepreneur['inn']
                    except:
                        inn = ''

                    try:
                        ogrn = linkedEntrepreneur['ogrn']
                    except:
                        ogrn = ''

                    try:
                        lastName = linkedEntrepreneur['lastName']
                    except:
                        lastName = ''

                    try:
                        firstName = linkedEntrepreneur['firstName']
                    except:
                        firstName = ''

                    try:
                        middleName = linkedEntrepreneur['middleName']
                    except:
                        middleName = ''

                    try:
                        regionName = linkedEntrepreneur['regionName']
                    except:
                        regionName = ''

                    try:
                        regPlace = linkedEntrepreneur['regPlace']
                    except:
                        regPlace = ''

                    try:
                        regYear = linkedEntrepreneur['regYear']
                    except:
                        regYear = ''

                    try:
                        regDate = linkedEntrepreneur['regDate']
                    except:
                        regDate = ''

                    try:
                        endDate = linkedEntrepreneur['endDate']
                    except:
                        endDate = ''

                    jsonAPI_list[:] = []
                    jsonAPI = {
                        "query_id": 24,
                        "params": inn + ';' + ogrn+ ';' + lastName+ ';' + firstName+ ';' +
                                  middleName+ ';' + regionName+ ';' + regPlace.replace("'","''")+ ';' +
                                  regYear+ ';' + regDate+ ';' + endDate
                    }
                    jsonAPI_list.append(jsonAPI)

                    jsonAPI = {
                        "query_id": 25,
                        "params": str(last_id) + ';' + linkTypeDisplayName
                    }
                    jsonAPI_list.append(jsonAPI)
                    j_apis.append(jsonAPI_list)
            except KeyError:
                pass
            except Exception:
                BiasLog(text='add_profile-linked-profile-entrepreneurs: ' + traceback.format_exc(), user_id=user_id).save()

            try:
                for linkedPhone in linkedProfile['profile']['phones']:
                    try:
                        number = linkedPhone['number'].replace(' ', '').replace('-', '').replace(')', '').replace('(', '').replace('+7','')
                    except:
                        number = ''

                    try:
                        isLandline = linkedPhone['isLandline']
                    except:
                        isLandline = ''

                    try:
                        regionName = linkedPhone['regionName']
                    except:
                        regionName = ''

                    jsonAPI_list[:] = []
                    jsonAPI = {
                        "query_id": 26,
                        "params": number + ';' + isLandline + ';' + regionName
                    }
                    jsonAPI_list.append(jsonAPI)

                    jsonAPI = {
                        "query_id": 27,
                        "params": str(last_id) + ';' + linkTypeDisplayName
                    }
                    jsonAPI_list.append(jsonAPI)
                    j_apis.append(jsonAPI_list)
            except KeyError:
                pass
            except Exception:
                BiasLog(text='add_profile-linked-profile-phones: ' + traceback.format_exc(), user_id=user_id).save()

            try:
                for linkedAddress in linkedProfile['profile']['addresses']:
                    try:
                        value = linkedAddress['value']
                    except:
                        value = ''

                    jsonAPI_list[:] = []
                    jsonAPI = {
                        "query_id": 28,
                        "params": value
                    }
                    jsonAPI_list.append(jsonAPI)

                    jsonAPI = {
                        "query_id": 29,
                        "params": str(last_id) + ';' + linkTypeDisplayName
                    }
                    jsonAPI_list.append(jsonAPI)
                    j_apis.append(jsonAPI_list)
            except KeyError:
                pass
            except Exception:
                BiasLog(text='add_profile-linked-profile-addresses: ' + traceback.format_exc(), user_id=user_id).save()

            try:
                for linkedDocument in linkedProfile['profile']['documents']:
                    try:
                        typeDisplayName = linkedDocument['typeDisplayName']
                    except:
                        typeDisplayName = ''

                    try:
                        serNum = linkedDocument['serNum']
                    except:
                        serNum = ''

                    try:
                        issueDate = linkedDocument['issueDate']
                    except:
                        issueDate = ''

                    try:
                        issuer = linkedDocument['issuer']
                    except:
                        issuer = ''

                    try:
                        departmentCode = linkedDocument['departmentCode']
                    except:
                        departmentCode = ''

                    try:
                        isExpired = linkedDocument['isExpired']
                    except:
                        isExpired = ''

                    try:
                        expirationReason = linkedDocument['expirationReason']
                    except:
                        expirationReason = ''

                    jsonAPI_list[:] = []
                    jsonAPI = {
                        "query_id": 30,
                        "params": typeDisplayName.replace("'","''") + ';' + serNum + ';' + issueDate+ ';' +
                                  issuer+ ';' + departmentCode+ ';' + str(isExpired) + ';' + expirationReason.replace("'","''")
                    }
                    jsonAPI_list.append(jsonAPI)

                    jsonAPI = {
                        "query_id": 31,
                        "params": str(last_id) + ';' + linkTypeDisplayName
                    }
                    jsonAPI_list.append(jsonAPI)
                    j_apis.append(jsonAPI_list)
            except KeyError:
                pass
            except Exception:
                BiasLog(text='add_profile-linked-profile-documents: ' + traceback.format_exc(), user_id=user_id).save()

            try:
                for linkedNegative in linkedProfile['profile']['negatives']:
                    try:
                        typeDisplayName = linkedNegative['typeDisplayName']
                    except:
                        typeDisplayName = ''

                    try:
                        tags = linkedNegative['tags']
                    except:
                        tags = ''

                    try:
                        atDate = linkedNegative['atDate']
                    except:
                        atDate = ''

                    try:
                        article = linkedNegative['article']
                    except:
                        article = ''

                    try:
                        multilineText = linkedNegative['multilineText']
                    except:
                        multilineText = ''

                    jsonAPI_list[:] = []
                    jsonAPI = {
                        "query_id": 32,
                        "params": typeDisplayName.replace("'","''") + ';' + tags.replace("'","''") + ';' + atDate+ ';' +
                                  article.replace("'","''")+ ';' + multilineText.replace("'","''")
                    }
                    jsonAPI_list.append(jsonAPI)

                    jsonAPI = {
                        "query_id": 33,
                        "params": str(last_id) + ';' + linkTypeDisplayName
                    }
                    jsonAPI_list.append(jsonAPI)
                    j_apis.append(jsonAPI_list)
            except KeyError:
                pass
            except Exception:
                BiasLog(text='add_profile-linked-profile-negatives: ' + traceback.format_exc(), user_id=user_id).save()

            try:
                for linkedAddition in linkedProfile['profile']['additions']:
                    try:
                        atDate = linkedAddition['atDate']
                    except:
                        atDate = ''

                    try:
                        multilineText = linkedAddition['multilineText']
                    except:
                        multilineText = ''

                    jsonAPI_list[:] = []
                    jsonAPI = {
                        "query_id": 34,
                        "params": atDate + ';' + multilineText.replace("'","''")
                    }
                    jsonAPI_list.append(jsonAPI)

                    jsonAPI = {
                        "query_id": 35,
                        "params": str(last_id) + ';' + linkTypeDisplayName
                    }
                    jsonAPI_list.append(jsonAPI)
                    j_apis.append(jsonAPI_list)
            except KeyError:
                pass
            except Exception:
                BiasLog(text='add_profile-linked-profile-additions: ' + traceback.format_exc(), user_id=user_id).save()
    except KeyError:
        pass
    except Exception:
            BiasLog(text='add_profile-linked: ' + traceback.format_exc(), user_id=user_id).save()
    asnyc_aiohttp_get_all(j_apis, user_id)
    return last_id


def check_profile(_fio,_birthdate,_input_phone,_adr,user_id):
    _input_phone = _input_phone.replace(' ', '').replace('-', '').replace(')', '').replace('(', '').replace('+7', '')

    query_id = 49
    params = _fio + ';' + _fio.replace('.', '%')

    _birthdate_param = ''

    if _birthdate:
        _birthdate_param = _birthdate + ';' + \
                 _birthdate + ';' + _birthdate + ';' + _birthdate

    _input_phone_param = ''
    if _input_phone:
        _input_phone_param = _input_phone

    _adr_param = ''
    if _adr:
        _adr_param = '%' + _adr + '%'

    if _birthdate_param and _input_phone_param and _adr_param:
        query_id = 52
        params = params + ';' + _birthdate_param + ';' + _input_phone_param + ';' + _adr_param
    elif _birthdate_param and _input_phone_param:
        query_id = 51
        params = params + ';' + _birthdate_param + ';' + _input_phone_param
    elif _birthdate_param and _adr_param:
        query_id = 53
        params = params + ';' + _birthdate_param + ';' + _adr_param
    elif _input_phone_param and _adr_param:
        query_id = 54
        params = params + ';' + _input_phone_param + ';' + _adr_param
    elif _birthdate_param:
        query_id = 50
        params = params + ';' + _birthdate_param
    elif _input_phone_param:
        query_id = 55
        params = params + ';' + _input_phone_param
    elif _adr_param:
        query_id = 56
        params = params + ';' + _adr_param

    jsonAPI = {
        "query_id": query_id,
        "params": params
    }
    responseAPI = requests.post(URL_API, headers=HEADERS_API, json=jsonAPI)

    if responseAPI.status_code != 200:
        if responseAPI.json()['detail'] == 'Empty result':
            return pd.DataFrame()
        BiasLog(text=f'query - {str(query_id)}: ' + responseAPI.json()['detail'], user_id=user_id).save()
        return ADMIN_ERROR

    return pd.DataFrame().from_dict(responseAPI.json())

def get_profile(bias_login,bias_password,user_id,_fio,_birthdate,_input_phone,_birthplace,_adr,df, uid = ''):
    if len(df) > 1:
        BiasLog(
            text=f'В базе найдено {len(df)} клиентов ' + _fio + ', ' + _birthdate + ', ' + _input_phone + ', ' + _birthplace + ', ' + _adr + ', ' + uid,
            user_id=user_id).save()

    if df.empty:
        if uid:
            df_profile_id = add_profile(bias_login, bias_password,user_id, _fio, _birthdate, _input_phone, _birthplace, _adr, uid)
        else:
            df_profile_id = add_profile(bias_login, bias_password,user_id, _fio, _birthdate, _input_phone, _birthplace, _adr)
            if type(df_profile_id) != int:
                return df_profile_id
    else:  # len(df) > 0
        df_profile_id = df.id.iloc[0]

    j_apis = list()
    for query_id in range(36, 49):
        jsonAPI = {
            "query_id": query_id,
            "params": str(df_profile_id)
        }
        j_apis.append(jsonAPI)
    try:
        return tuple(asnyc_aiohttp_get_all(j_apis,user_id))
    except:
        return ADMIN_ERROR
