# -*- coding: utf-8 -*-
import json
import re
import time

from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import requests
from sqlalchemy import create_engine

from mysite.settings import vscaledb, DEBUG, DEPLOY

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from website.models import BiasLog


def get_bias(bias_login,bias_password,fio,bdate,input_phone,adr, _fio = ''):
    if not (fio or bdate or input_phone or adr):
        return pd.DataFrame(), None, None, 'Заполните хотя бы одно поле'
    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    op.add_argument("--disable-infobars")
    op.add_argument("--disable-extensions")
    op.add_argument('--no-sandbox')
    op.add_argument('--disable-dev-shm-usage')

    if DEBUG and not DEPLOY:
        chrome_path = 'D:/Users/user/Documents/Разовые скрипты/chromedriver.exe'
    else:
        chrome_path ='/usr/bin/chromedriver'
    driver = webdriver.Chrome(chrome_path,options=op)#

    driver.get("some host")

    driver.find_element_by_xpath("//input[@placeholder='Введите логин']").send_keys(bias_login)

    driver.find_element_by_xpath("//input[@placeholder='Введите пароль']").send_keys(bias_password)

    driver.find_element_by_xpath("//button[text()='Вход']").click()

    login_error = ''
    df_1 = pd.DataFrame(columns=['fio', 'birthdate', 'birthplace'])
    df_2 = df_1

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
        while condition:
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
        while condition:
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
        while condition:
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
            while condition:
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
        uid = driver.current_url.replace('some host','')

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//div[text()='Информация о поиске']")))

        title = driver.title[:-11]
        driver.quit()
        return uid, title

    html = driver.page_source

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

def add_profile(user_id,_fio,_birthdate,_input_phone,_birthplace,_adr,connection, uid = ''):
    _input_phone = _input_phone.replace(' ', '').replace('-', '').replace(')', '').replace('(', '').replace('+7', '')

    if uid:
        data = {
            "passkey": "cc07195740d8bfb5d5bb9b0d53c3be4b3e988d7e",
            "timeout": 15,
            "uid": uid
        }
    else:
        data = {
            "passkey": "cc07195740d8bfb5d5bb9b0d53c3be4b3e988d7e",
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
    response = requests.post("some host", headers=headers, json=data, verify=False)

    try:
        return response.json()['errors']
    except:
        pass

    values = connection.execute(f"""insert into b_profile (fullname, birthdate,phone,fulladdress,birthplace)
                                    values('{_fio}','{_birthdate}','{_input_phone}','{_adr}','{_birthplace}') RETURNING id""")#5

    # ,sernum,issuedate,inn,snils,
    # ,'{_pasp}','{_biasdate}','{_inn}','{_bias_snils}'

    try:
        for value in values:
            last_id = value.id
    except Exception as e:
        BiasLog(text=e, user_id=user_id).save()
        pass

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
            connection.execute(f"""insert into b_person (profile_id,lastname,firstname,middlename,birthdate,birthplace,deathdate)
                                           values({last_id},'{lastName}','{firstName}','{middleName}','{birthdate}','{birthplace}','{deathDate}')""")#6
    except KeyError:
        pass
    except Exception as e:
        BiasLog(text=e, user_id=user_id).save()

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

            connection.execute(f"""insert into b_phone (profile_id,number,islandline,regionname)
                                           values({last_id},'{number}','{isLandline}','{regionName}')""")#7
    except KeyError:
        pass
    except Exception as e:
        BiasLog(text=e, user_id=user_id).save()

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

            connection.execute(f"""insert into b_organization (profile_id,inn,ogrn,fullname,shortname,regionname,regplace,regyear,regdate,enddate)
                                           values({last_id},'{inn}','{ogrn}','{fullName.replace("'","''")}','{shortName.replace("'","''")}','{regionName}','{regPlace.replace("'","''")}','{regYear}','{regDate}','{endDate}')""")#8
    except KeyError:
        pass
    except Exception as e:
        BiasLog(text=e, user_id=user_id).save()

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

            connection.execute(f"""insert into b_entrepreneur (profile_id,inn,ogrn,lastname,firstname,middlename,regionname,regplace,regyear,regdate,enddate)
                                           values({last_id},'{inn}','{ogrn}','{lastName}','{firstName}','{middleName}','{regionName}','{regPlace.replace("'","''")}','{regYear}','{regDate}','{endDate}')""")
            #9
    except KeyError:
        pass
    except Exception as e:
        BiasLog(text=e, user_id=user_id).save()

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

            connection.execute(f"""insert into b_vehicle (profile_id,vin,regplate,brand,model,color,manufactureyear)
                                           values({last_id},'{vin}','{regPlate}','{brand.replace("'","''")}','{model.replace("'","''")}','{color}','{manufactureYear}')""")#`10
    except KeyError:
        pass
    except Exception as e:
        BiasLog(text=e, user_id=user_id).save()

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
            connection.execute(f"""insert into b_estate (profile_id,cadnum,description)
                                           values({last_id},'{cadNum}','{description.replace("'","''")}')""")#11
    except KeyError:
        pass
    except Exception as e:
        BiasLog(text=e, user_id=user_id).save()

    try:
        for address in response.json()['profiles'][0]['addresses']:
            try:
                value = address['value']
            except:
                value = ''
            connection.execute(f"""insert into b_address (profile_id,value)
                                           values({last_id},'{value}')""")#12
    except KeyError:
        pass
    except Exception as e:
        BiasLog(text=e, user_id=user_id).save()

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

            connection.execute(f"""insert into b_document (profile_id,typedisplayname,sernum,issuedate,issuer,departmentcode,isexpired,expirationreason)
                                           values({last_id},'{typeDisplayName.replace("'","''")}','{serNum}','{issueDate}','{issuer}','{departmentCode}','{isExpired}','{expirationReason.replace("'","''")}')""")
            #13
    except KeyError:
        pass
    except Exception as e:
        BiasLog(text=e, user_id=user_id).save()

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

            connection.execute(f"""insert into b_negative (profile_id,typedisplayname,tags,atdate,article,multilinetext)
                                           values({last_id},'{typeDisplayName.replace("'","''")}','{tags_str.replace("'","''")}','{atDate}','{article.replace("'","''")}','{multilineText.replace("'","''")}')""")#14
    except KeyError:
        pass
    except Exception as e:
        BiasLog(text=e, user_id=user_id).save()

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
            connection.execute(f"""insert into b_addition (profile_id,atdate,multilinetext)
                                           values({last_id},'{atDate}','{multilineText.replace("'","''")}')""")#15
    except KeyError:
        pass
    except Exception as e:
        BiasLog(text=e, user_id=user_id).save()

    try:
        for linkedProfile in response.json()['profiles'][0]['linkedProfiles']:
            try:
                linkTypeDisplayName = linkedProfile['linkTypeDisplayName']
            except:
                linkTypeDisplayName = ''

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

                    person_values = connection.execute(f"""insert into b_person (lastname,firstname,middlename,birthdate,birthplace,deathdate)
                                                   values('{lastName}','{firstName}','{middleName}','{birthdate}','{birthplace}','{deathDate}') RETURNING id""")#16

                    for person_value in person_values:
                        last_person_id = person_value.id

                    connection.execute(f"""insert into b_linkedprofile (profile_id,linktypedisplayname,person_id)
                                                                   values({last_id},'{linkTypeDisplayName}',{last_person_id})""")#17
            except KeyError:
                pass
            except Exception as e:
                BiasLog(text=e, user_id=user_id).save()

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

                    organization_values = connection.execute(f"""insert into b_organization (inn,ogrn,fullname,shortname,regionname,regplace,regyear,regdate,enddate)
                                                   values('{inn}','{ogrn}','{fullName.replace("'","''")}','{shortName.replace("'","''")}','{regionName}','{regPlace.replace("'","''")}','{regYear}','{regDate}','{endDate}') RETURNING id""")#18

                    for organization_value in organization_values:
                        last_organization_id = organization_value.id

                    connection.execute(f"""insert into b_linkedprofile (profile_id,linktypedisplayname,organization_id)
                                                                   values({last_id},'{linkTypeDisplayName}',{last_organization_id})""")#19
            except KeyError:
                pass
            except Exception as e:
                BiasLog(text=e, user_id=user_id).save()

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

                    estate_values = connection.execute(f"""insert into b_estate (cadnum,description)
                                                   values('{cadNum}','{description.replace("'","''")}') RETURNING id""")#20

                    for estate_value in estate_values:
                        last_estate_id = estate_value.id

                    connection.execute(f"""insert into b_linkedprofile (profile_id,linktypedisplayname,estate_id)
                                                                   values({last_id},'{linkTypeDisplayName}',{last_estate_id})""")#21
            except KeyError:
                pass
            except Exception as e:
                BiasLog(text=e, user_id=user_id).save()

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

                    vehicle_values = connection.execute(f"""insert into b_vehicle (vin,regplate,brand,model,color,manufactureyear)
                                                   values('{vin}','{regPlate}','{brand.replace("'","''")}','{model.replace("'","''")}','{color}','{manufactureYear}') RETURNING id""")#22

                    for vehicle_value in vehicle_values:
                        last_vehicle_id = vehicle_value.id

                    connection.execute(f"""insert into b_linkedprofile (profile_id,linktypedisplayname,vehicle_id)
                                                                   values({last_id},'{linkTypeDisplayName}',{last_vehicle_id})""")#23
            except KeyError:
                pass
            except Exception as e:
                BiasLog(text=e, user_id=user_id).save()

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

                    entrepreneur_values =  connection.execute(f"""insert into b_entrepreneur (inn,ogrn,lastname,firstname,middlename,regionname,regplace,regyear,regdate,enddate)
                                                   values('{inn}','{ogrn}','{lastName}','{firstName}','{middleName}','{regionName}','{regPlace.replace("'","''")}','{regYear}','{regDate}','{endDate}') RETURNING id""")
                    #24

                    for entrepreneur_value in entrepreneur_values:
                        last_entrepreneur_id = entrepreneur_value.id

                    connection.execute(f"""insert into b_linkedprofile (profile_id,linktypedisplayname,entrepreneur_id)
                                                                   values({last_id},'{linkTypeDisplayName}',{last_entrepreneur_id})""")#25
            except KeyError:
                pass
            except Exception as e:
                BiasLog(text=e, user_id=user_id).save()

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

                    phone_values = connection.execute(f"""insert into b_phone (number,islandline,regionname)
                                                   values('{number}','{isLandline}','{regionName}') RETURNING id""")#26

                    for phone_value in phone_values:
                        last_phone_id = phone_value.id

                    connection.execute(f"""insert into b_linkedprofile (profile_id,linktypedisplayname,phone_id)
                                                                   values({last_id},'{linkTypeDisplayName}',{last_phone_id})""")#27
            except KeyError:
                pass
            except Exception as e:
                BiasLog(text=e, user_id=user_id).save()

            try:
                for linkedAddress in linkedProfile['profile']['addresses']:
                    try:
                        value = linkedAddress['value']
                    except:
                        value = ''
                    address_values = connection.execute(f"""insert into b_address (value) values('{value}') RETURNING id""")#28

                    for address_value in address_values:
                        last_address_id = address_value.id

                    connection.execute(f"""insert into b_linkedprofile (profile_id,linktypedisplayname,address_id)
                                           values({last_id},'{linkTypeDisplayName}',{last_address_id})""")#29
            except KeyError:
                pass
            except Exception as e:
                BiasLog(text=e, user_id=user_id).save()

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

                    document_values = connection.execute(f"""insert into b_document (typedisplayname,sernum,issuedate,issuer,departmentcode,isexpired,expirationreason)
                                                   values('{typeDisplayName.replace("'","''")}','{serNum}','{issueDate}','{issuer}','{departmentCode}','{isExpired}','{expirationReason.replace("'","''")}') RETURNING id""")
                    #30

                    for document_value in document_values:
                        last_document_id = document_value.id

                    connection.execute(f"""insert into b_linkedprofile (profile_id,linktypedisplayname,document_id)
                                           values({last_id},'{linkTypeDisplayName}',{last_document_id})""")
                    #31
            except KeyError:
                pass
            except Exception as e:
                BiasLog(text=e, user_id=user_id).save()

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

                    negative_values = connection.execute(f"""insert into b_negative (typedisplayname,tags,atdate,article,multilinetext)
                                                   values('{typeDisplayName.replace("'","''")}','{tags.replace("'","''")}','{atDate}','{article.replace("'","''")}','{multilineText.replace("'","''")}') RETURNING id""")
                    #32

                    for negative_value in negative_values:
                        last_negative_id = negative_value.id

                    connection.execute(f"""insert into b_linkedprofile (profile_id,linktypedisplayname,negative_id)
                                           values({last_id},'{linkTypeDisplayName}',{last_negative_id})""")
                    #33
            except KeyError:
                pass
            except Exception as e:
                BiasLog(text=e, user_id=user_id).save()

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

                    addition_values = connection.execute(f"""insert into b_addition (atdate,multilinetext)
                                                   values('{atDate}','{multilineText.replace("'","''")}') RETURNING id""")
                    #34


                    for addition_value in addition_values:
                        last_addition_id = addition_value.id

                    connection.execute(f"""insert into b_linkedprofile (profile_id,linktypedisplayname,addition_id)
                                           values({last_id},'{linkTypeDisplayName}',{last_addition_id})""")
                    #35
            except KeyError:
                pass
            except Exception as e:
                BiasLog(text=e, user_id=user_id).save()
    except KeyError:
        pass
    except Exception as e:
            BiasLog(text=e, user_id=user_id).save()
    connection.close()
    return last_id


def check_profile(_fio,_birthdate,_input_phone,_adr):
    db = create_engine(vscaledb)
    _input_phone = _input_phone.replace(' ', '').replace('-', '').replace(')', '').replace('(', '').replace('+7', '')
    query = f"""select id from b_profile where (fullname='{_fio}' or fullname like '{_fio.replace('.', '%')}')  and created_at > current_timestamp - '6 month'::interval"""  # запрос по фио
    # 49
    # like под вопросом , так как такого результата может не прийти

    if _birthdate != '':
        query = query + f""" and (birthdate='{_birthdate}' 
                                      or
                                      concat(split_part('{_birthdate}', '.', 3),'-',split_part('{_birthdate}', '.', 2),'-',split_part('{_birthdate}', '.', 1)) in 
                                      (select birthdate from b_person where  profile_id = b_profile.id)
                                      )"""  # 50

    if _input_phone != '':
        query = query + f" and '{_input_phone}' in (select number from b_phone where  profile_id = b_profile.id)"  # 51

    if _adr != '':
        query = query + f" and (select true from b_address where profile_id = b_profile.id and value like '{'%' + _adr + '%'}')"  # 52

    return pd.read_sql(query, con=db)

def get_profile(user_id,_fio,_birthdate,_input_phone,_birthplace,_adr,df, uid = ''):
    db = create_engine(vscaledb)

    if len(df) > 0:
        df_profile_id = df.id.iloc[0]
    if len(df) > 1:
        BiasLog(text=f'В базе найдено {len(df)} клиентов ' + _fio+', '+_birthdate+', '+_input_phone+', '+_birthplace+', '+_adr+', '+uid, user_id=user_id).save()
    connection = db.connect()

    if df.empty:
        if uid:
            df_profile_id = add_profile(user_id,_fio,_birthdate,_input_phone,_birthplace,_adr,connection, uid)
        else:
            df_profile_id = add_profile(user_id,_fio,_birthdate,_input_phone,_birthplace,_adr,connection)
            if type(df_profile_id) != int:
                return df_profile_id

    df_person = pd.read_sql(f"""select concat(lastname, ' ', firstname,' ', middlename) as  fullname,
     (case when birthdate != '' then to_char(birthdate::date, 'DD.MM.YYYY')  ELSE '' END) as birthdate,
        birthplace,(case when deathdate != '' then to_char(deathdate::date, 'DD.MM.YYYY') ELSE '' END) as deathdate
     from b_person where profile_id= '{df_profile_id}'""",con=db)#36

    df_organization = pd.read_sql(
        f"""select inn, ogrn, fullname, shortname, regionname, regplace, regyear, 
        (case when regdate != '' then to_char(regdate::date, 'DD.MM.YYYY')  ELSE '' END) as regdate, 
		(case when enddate != '' then to_char(enddate::date, 'DD.MM.YYYY') ELSE '' END) as enddate
        from b_organization where profile_id= '{df_profile_id}'""",
        con=db)
    #37

    df_entrepreneur = pd.read_sql(
        f"""select inn, ogrn, lastname, firstname, middlename, regionname, regplace, regyear,  
        (case when regdate != '' then to_char(regdate::date, 'DD.MM.YYYY')  ELSE '' END) as regdate, 
		(case when enddate != '' then to_char(enddate::date, 'DD.MM.YYYY') ELSE '' END) as enddate
        from b_entrepreneur where profile_id= '{df_profile_id}'""",
        con=db)
    #38


    df_phone = pd.read_sql(f"""select concat('+7',number) as number, islandline, regionname from b_phone where profile_id= '{df_profile_id}'""", con=db)#39

    df_address = pd.read_sql(f"""select value from b_address where profile_id= '{df_profile_id}'""", con=db)#40

    df_document =  pd.read_sql(f"""select typedisplayname, sernum,(case when issuedate != '' then to_char(issuedate::date, 'DD.MM.YYYY')  ELSE '' END) as issuedate, issuer, departmentcode, 
            (CASE
                WHEN isexpired = 'True'  THEN 'Недействителен'
                WHEN isexpired = 'False'  THEN 'Действителен'
             ELSE ''
             END) as isexpired
        from b_document where profile_id= '{df_profile_id}'""", con=db)#41

    df_negative = pd.read_sql(f"""select typedisplayname, tags,
    (case  
        when char_length(atdate)=4 then atdate
        when atdate != '' then to_char(atdate::date, 'DD.MM.YYYY')  
        ELSE '' 
     END) as atdate , article, multilinetext 
                                       from b_negative where profile_id= '{df_profile_id}'""", con=db)#42

    df_linked_person = pd.read_sql(f"""select linktypedisplayname , concat(lastname, ' ', firstname,' ', middlename) as  fullname, 
        (case when birthdate != '' then to_char(birthdate::date, 'DD.MM.YYYY')  ELSE '' END) as birthdate,
        birthplace,(case when deathdate != '' then to_char(deathdate::date, 'DD.MM.YYYY') ELSE '' END) as deathdate
        from b_linkedprofile
        left join b_person
        on person_id = b_person.id
        where b_linkedprofile.profile_id= '{df_profile_id}'
        and person_id is not NULL""", con=db)#43-----------------------------------------

    df_linked_entrepreneur = pd.read_sql(f"""select linktypedisplayname ,inn, ogrn, lastname, firstname, middlename, regionname, regplace, regyear,
        (case when regdate != '' then to_char(regdate::date, 'DD.MM.YYYY')  ELSE '' END) as regdate, 
		(case when enddate != '' then to_char(enddate::date, 'DD.MM.YYYY') ELSE '' END) as enddate
        from b_linkedprofile
        left join b_entrepreneur
        on entrepreneur_id = b_entrepreneur.id
        where b_linkedprofile.profile_id= '{df_profile_id}'
        and entrepreneur_id is not NULL""", con=db)#44

    df_linked_organization = pd.read_sql(f"""select linktypedisplayname ,inn, ogrn, fullname, shortname, regionname, regplace, regyear,
        (case when regdate != '' then to_char(regdate::date, 'DD.MM.YYYY')  ELSE '' END) as regdate, 
		(case when enddate != '' then to_char(enddate::date, 'DD.MM.YYYY') ELSE '' END) as enddate
        from b_linkedprofile
        left join b_organization
        on organization_id = b_organization.id
        where b_linkedprofile.profile_id= '{df_profile_id}'
        and organization_id is not NULL""", con=db)#45

    df_linked_estate = pd.read_sql(f"""select linktypedisplayname , cadnum, description
        from b_linkedprofile
        left join b_estate
        on estate_id = b_estate.id
        where b_linkedprofile.profile_id= '{df_profile_id}'
        and estate_id is not NULL""", con=db)#46

    df_linked_vehicle = pd.read_sql(f"""select linktypedisplayname , vin, regplate, brand, model, color, manufactureyear
                                                    from b_linkedprofile
                                                    left join b_vehicle
                                                    on vehicle_id = b_vehicle.id
                                                    where b_linkedprofile.profile_id= '{df_profile_id}'
                                                    and vehicle_id is not NULL""", con=db)#47

    df_addition = pd.read_sql(f"""select (case when atdate != '' then to_char(atdate::date, 'DD.MM.YYYY')  ELSE '' END) as atdate  , multilinetext
                                  from b_addition where profile_id= '{df_profile_id}'""", con=db)#48
    return df_person, df_organization,df_entrepreneur,df_phone , df_address, df_document, df_negative, df_linked_person, df_linked_organization, df_linked_estate, df_linked_vehicle, df_linked_entrepreneur, df_addition
