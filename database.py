from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# For Production
username = os.environ.get('MYSQL_ROOT_USERNAME')
password = os.environ.get('MYSQL_ROOT_PASSWORD')
host = os.environ.get('MYSQL_HOST')
port = os.environ.get('MYSQL_PORT')
dbname = os.environ.get('MYSQL_DATABASE')


# For Development
#username = 'root'
#password = 'root'
#host = 'localhost'
#port = 3306
#dbname = 'laundry'

MYSQL_DATABASE_URL = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{dbname}"

engine = create_engine(
    MYSQL_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
