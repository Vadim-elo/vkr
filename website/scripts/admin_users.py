import io

import pandas
from django.db import connection as connection_django
from sqlalchemy import create_engine, event
from mysite.settings import db_analytics


def get_users():  # group_ids, admin_id
    """
    Возвращает dataframe, содержащий данные о пользователях, состоящих в группах из group_ids,
    при том, что группы выводяться только созданные текущим пользователем
    """
    # query = f"""
    #     select auth_user.id, last_name ,first_name,username,is_active, auth_group.name as department,
    #     auth_user_groups.group_id,
	# 	(
	# 		array(
	# 			select website_customgroup.group
	# 			from website_customgroupuser
	# 			inner join website_customgroup
	# 			on website_customgroupuser.group_id = website_customgroup.id
	# 			where website_customgroupuser.user_id = auth_user.id
	# 			and website_customgroup.is_active=true
	# 			and website_customgroupuser.dateend is null
	# 		)
	# 	) as groups
    #     from auth_user
    #     left join auth_user_groups
    #     on auth_user.id = auth_user_groups.user_id
    #     left join auth_group
    #     on auth_group.id = auth_user_groups.group_id
    # """
    data = {'id': ['Tom', 'nick', 'krish', 'jack'],
            'last_name': [20, 21, 19, 18],
            'first_name': [20, 21, 19, 18],
            'username': [20, 21, 19, 18],
            'is_active': [20, 21, 19, 18],
            'department': [20, 21, 19, 18],
            'group_id': [20, 21, 19, 18],
            }

    # Create DataFrame
    df = pandas.DataFrame(data)
    # df = pandas.read_sql_query(query, connection_django)
    return df  # where  group_id = 4
# and website_customgroup.admin_id = {admin_id}


def update_collectors():
    """
    Заменяет таблицу collectors_loandail в olap базе обновленными данными по пользователям
     с целью группировки сотрудников по группам в pentaho
     """
    df = pandas.read_sql_query('''         
    select fio,split_part(collector_group, '_', 1) as collector_group, split_part(collector_group, '_', 2) as bucket,
    group_id, group_is_active, datebeg, dateend, user_is_active, users_id
    from (
             select concat(last_name, ' ', first_name) as fio,
                    website_customgroup."group" as collector_group,
                    auth_user_groups.group_id, website_customgroup.is_active as group_is_active,
                    website_customgroupuser.datebeg,website_customgroupuser.dateend,
                    auth_user.is_active as user_is_active,
                    wu.users_id
             from auth_user
                      left join website_customgroupuser
                                on website_customgroupuser.user_id = auth_user.id
                      left join website_customgroup
                                on website_customgroupuser.group_id = website_customgroup.id
                      left join auth_user_groups
                                on auth_user.id = auth_user_groups.user_id
                      left join website_usersid wu
                                on auth_user.id = wu.user_id
             where website_customgroup."group" ~ '_'
             --and website_customgroupuser.admin_id = 21
         )a
         '''
                               , connection_django
                               )

    connection_pentaho = create_engine(db_analytics).raw_connection()
    cursor = connection_pentaho.cursor()

    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Index'}, inplace=True)

    command = '''DROP TABLE IF EXISTS collectors_loandail;
    CREATE TABLE collectors_loandail
    (
    "Index" serial primary key,
    "fio" text,
    "collector_group" text,
    "bucket" text,
    "group_id" integer,
    "group_is_active" boolean,
    "datebeg" date,
    "dateend" date,
    "user_is_active" boolean,
    "users_id" int
    );'''

    cursor.execute(command)
    connection_pentaho.commit()

    output = io.StringIO()
    df.to_csv(output, sep='\t', header=False, index=False)
    output.seek(0)
    cur = connection_pentaho.cursor()

    cur.copy_from(output, 'collectors_loandail', null="")
    connection_pentaho.commit()
    cur.close()

# for ORM style
'''queryset_groups = CustomGroup.objects.filter(
    id__in=CustomGroupUser.objects.filter(
        admin_id=request.user.id
    ).values_list('group_id')
).values_list('group', flat=True)


print(
    User.objects.filter().values_list(
        'id',
        'last_name',
        'first_name',
        'username',
        'is_active'
    ).annotate(groups=queryset_groups)
)
'''
