from django.contrib.auth.models import User
from django.contrib.auth.models import Group
import pandas as pd


def create_users():
    df_users = pd.read_excel('media/employees.xlsx')
    for index, row in df_users.iterrows():
        try:
            if str(row['email']) == 'nan':
                email = 'test@cash-u.com'
            else:
                email = str(row['email']).replace(' ', '')

            try:
                User.objects.get(username=row['username'])
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=row['username'].replace(' ', ''),
                    first_name=row['Имя'].title().replace(' ', ''),
                    last_name=row['Фамилия'].title().replace(' ', ''),
                    email=email,
                    password=row['password'].replace(' ', '')
                )
                print('user added')
                group = Group.objects.get(name=row['Отдел'].title())
                group.user_set.add(user)
                print('department added')
        except Exception as e:
            print(e)

# create_user_loandail.create_users()
# from .scripts import create_user_loandail
