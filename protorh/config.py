import os
from dotenv import load_dotenv

env_file_path = os.path.join(os.path.dirname(__file__), 'protorh.env')

if os.path.exists(env_file_path):
    load_dotenv(dotenv_path=env_file_path)



salt = os.getenv('salt')
SECRET_KEY = os.getenv('SECRET_KEY')
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_PORT = os.getenv('DATABASE_PORT')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')