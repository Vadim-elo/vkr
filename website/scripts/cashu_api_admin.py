
import pandas as pd
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.sql import text as alchemy_text
from mysite.settings import db_analytics

SQLALCHEMY_DATABASE_URL = db_analytics

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def user_in(username, password):
    engine_pentaho = create_engine(SQLALCHEMY_DATABASE_URL)
    connection = engine_pentaho.connect()
    df = pd.read_sql(alchemy_text("select exists(select username from api_users where username=:username)"),
                     con=engine_pentaho,
                     params={'username':username})
    if df.values[0][0]== True:
         return True
    else:
        h_password = get_password_hash(password)
        connection.execute(alchemy_text("insert into api_users values(:username,:password,False)"), username=username,
                           password=h_password)
        connection.close()
        engine_pentaho.dispose()
        return False

def user_block(username):
    engine_pentaho = create_engine(SQLALCHEMY_DATABASE_URL)
    connection = engine_pentaho.connect()
    connection.execute(alchemy_text("UPDATE api_users SET disabled = true where username = :username"), username=username)
    connection.close()
    engine_pentaho.dispose()

def user_unblock(username):
    engine_pentaho = create_engine(SQLALCHEMY_DATABASE_URL)
    connection = engine_pentaho.connect()
    connection.execute(alchemy_text("UPDATE api_users SET disabled = false where username = :username"),
                       username=username)
    connection.close()
    engine_pentaho.dispose()

def get_users():
    # engine_pentaho = create_engine(SQLALCHEMY_DATABASE_URL)
    # df = pd.read_sql(alchemy_text("select * from api_users"), con=engine_pentaho)
    data = [['tom', 'hashed password'], ['nick', 'hashed password'], ['juli', 'hashed password']]

    # Create the pandas DataFrame
    df = pd.DataFrame(data, columns=['username', 'hashed_password'])
    df = df.iloc[::-1]
    return df
#user_in('test',get_password_hash('test'))