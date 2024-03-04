import streamlit as st
import streamlit_authenticator as stauth

# Define the authentication function
def authenticate():
    # Read the credentials from the secrets.toml file
    creds_raw = st.secrets["credentials"]["usernames"]
    creds = {username: {key: value for key, value in user.items()} for username, user in creds_raw.items()}
    
    # Instantiate the Authenticator
    authenticator = stauth.Authenticate(
        credentials={"usernames": creds},
        cookie_name=st.secrets["cookie"]["name"],
        key=st.secrets["cookie"]["key"],
        cookie_expiry_days=st.secrets["cookie"]["expiry_days"],
    )
    
    # Try the login process and return True or False based on the result
    name, authenticated, username = authenticator.login("main")
    if authenticated:
        return True
    else:
        return False
