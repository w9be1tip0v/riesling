import os
import requests
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from dotenv import load_dotenv
import streamlit as st
import base64
import json

load_dotenv()

LOGTO_ISSUER = os.getenv('LOGTO_ISSUER')
LOGTO_JWKS_URI = os.getenv('LOGTO_JWKS_URI')
ALGORITHMS = ["ES384"]

# Fetch JWKS data from Logto
def get_jwks():
    response = requests.get(LOGTO_JWKS_URI)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to fetch JWKS data")

# Get public key from JWKS
def get_public_key(token):
    jwks = get_jwks()
    unverified_header = jwt.get_unverified_header(token)
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            return {
                'kty': key['kty'],
                'crv': key['crv'],
                'x': key['x'],
                'y': key['y'],
            }
    raise JWTError('Public key not found.')

# Decode JWT token and get claims
def decode_id_token(token):
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid ID token")

    payload = parts[1]
    decoded_payload = base64.urlsafe_b64decode(payload + "==")
    claims = json.loads(decoded_payload)
    return claims

# Authenticate request
def authenticate_request():
    token = st.query_params.get("token")
    if not token:
        return None, "missing required Logto-ID-Token parameter"

    try:
        claims = decode_id_token(token)
        return claims, None
    except ValueError as e:
        return None, str(e)