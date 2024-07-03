import os
from logto import LogtoClient
from dotenv import load_dotenv

load_dotenv()

# Logto configuration
LOGTO_ENDPOINT = os.getenv('LOGTO_ENDPOINT')
LOGTO_APP_ID = os.getenv('LOGTO_APP_ID')
LOGTO_APP_SECRET = os.getenv('LOGTO_APP_SECRET')
LOGTO_REDIRECT_URI = os.getenv('LOGTO_REDIRECT_URI')

client = LogtoClient(
    endpoint=LOGTO_ENDPOINT,
    app_id=LOGTO_APP_ID,
    app_secret=LOGTO_APP_SECRET,
    redirect_uri=LOGTO_REDIRECT_URI
)

def get_login_url():
    return client.get_authorize_url()

def get_access_token(auth_code):
    return client.get_access_token(auth_code)

def get_user_info(access_token):
    return client.get_user_info(access_token)