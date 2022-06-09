# -*- coding: utf-8 -*-

from selenium import webdriver
import time
from bs4 import BeautifulSoup
import pandas as pd

log = 'kibl_porozov'
passw = 'GjwsV)KT'
fio = 'Порозов Виктор Сергеевич'

op = webdriver.ChromeOptions()
op.add_argument('--headless')
op.add_argument('--no-sandbox')
op.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome('/usr/bin/chromedriver',options=op)#

driver.get("some host")
driver.find_element_by_xpath("//input[@placeholder='Введите логин']").send_keys(log)

driver.find_element_by_xpath("//input[@placeholder='Введите пароль']").send_keys(passw)

driver.find_element_by_xpath("//button[text()='Вход']").click()

time.sleep(1)

driver.find_element_by_xpath("//input[@placeholder='Фамилия Имя Отчество']").send_keys(fio)

driver.find_element_by_xpath("//button[@title='Искать']").click()

time.sleep(1)
html = driver.page_source
time.sleep(1)

print(html.encode('utf-8'))
f = open('savepage.html', 'wb')
f.write(html.encode('utf-8'))
f.close()

match = BeautifulSoup(html, 'html.parser').findAll("div", {"class":"search-result"})

div_list = []
df=pd.DataFrame(columns=['fio','birthdate','birthplace'])

if len(match) > 0:
    for m in match:
        elem = BeautifulSoup(str(m), 'html.parser').findAll("div", {"class":"row"})
        if len(elem) > 0:
            for e in elem:
                row = BeautifulSoup(str(e), 'html.parser').find("a")
                div_list.append(row.get_text())
                divs = BeautifulSoup(str(e), 'html.parser').findAll("div", {"class":"ng-binding"})
                if len(divs) > 0:
                    for div in divs:
                        div_list.append(div.get_text().replace('  ','').replace('\n','').replace('Дата рождения: ','').replace('Место рождения: ',''))
                    if (len(div_list)==2):
                        div_list.append('')
                    div_list = [div_list]
                    #print(div_list)
                    df = df.append(pd.DataFrame(div_list, columns=['fio','birthdate','birthplace']), ignore_index=True)
                    div_list = []
pd.options.display.max_columns = 10
print(df)

