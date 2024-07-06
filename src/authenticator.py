import streamlit as st
import os
import requests
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from dotenv import load_dotenv
import streamlit as st

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

# Verify JWT token
def verify_jwt(token):
    jwks = get_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
        ec_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                ec_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "alg": key["alg"],
                    "crv": key["crv"],
                    "x": key["x"],
                    "y": key["y"]
                }
        if ec_key:
            payload = jwt.decode(
                token,
                ec_key,
                algorithms=ALGORITHMS,
                issuer=LOGTO_ISSUER
            )
            return payload
        else:
            raise JWTError("Unable to find appropriate key")
    except ExpiredSignatureError:
        raise JWTError("Token has expired")
    except JWTClaimsError:
        raise JWTError("Incorrect claims, please check the audience and issuer")
    except JWTError as e:
        raise e
    except Exception as e:
        raise JWTError(f"Unable to parse authentication token: {e}")

def authenticate_request():
    token = st.query_params.get("token")
    if not token:
        return None, "missing required Logto-ID-Token parameter"
    
    try:
        user_info = verify_jwt(token)
        return user_info, None
    except JWTError as e:
        return None, str(e)