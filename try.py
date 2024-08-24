# code from: https://github.com/mkhorasani/Streamlit-Authenticator
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator import Hasher

import yaml
from yaml.loader import SafeLoader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config_file_path = "./config.yaml"
with open(config_file_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

# Pre-hashing all plain text passwords once
Hasher.hash_passwords(config["credentials"])

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
    config["pre-authorized"],
)

if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = True


def toggle_sidebar():
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible


# Function to update the config file
def update_config():
    with open(config_file_path, "w") as file:
        yaml.dump(config, file, default_flow_style=False)


if st.button("Toggle authentication siebar"):
    toggle_sidebar()

if st.session_state.sidebar_visible:
    with st.sidebar:
        authenticator.login(location="sidebar")
        if st.session_state["authentication_status"]:
            authenticator.logout()
            st.write(f'Welcome *{st.session_state["name"]}*')
            st.title("Some content")
        elif st.session_state["authentication_status"] is False:
            st.error("Username/password is incorrect")
        elif st.session_state["authentication_status"] is None:
            st.warning("Please enter your username and password")

        try:
            (
                email_of_registered_user,
                username_of_registered_user,
                name_of_registered_user,
            ) = authenticator.register_user(
                location="sidebar", captcha=False, pre_authorization=False, domains=None
            )
            if email_of_registered_user:
                st.success("User registered successfully")
            update_config()  # update the config file with the new user
        except Exception as e:
            st.error(e)

        try:
            (
                username_of_forgotten_password,
                email_of_forgotten_password,
                new_random_password,
            ) = authenticator.forgot_password(location="sidebar")
            if username_of_forgotten_password:
                st.success("New password to be sent securely")
                # The developer should securely transfer the new password to the user.
            elif username_of_forgotten_password == False:
                st.error("Username not found")
        except Exception as e:
            st.error(e)

        try:
            username_of_forgotten_username, email_of_forgotten_username = (
                authenticator.forgot_username(location="sidebar")
            )
            if username_of_forgotten_username:
                st.success("Username to be sent securely")
                # The developer should securely transfer the username to the user.
            elif username_of_forgotten_username == False:
                st.error("Email not found")
        except Exception as e:
            st.error(e)


if st.session_state["authentication_status"]:
    try:
        if authenticator.reset_password(
            st.session_state["username"], location="sidebar"
        ):
            st.success("Password modified successfully")
    except Exception as e:
        st.error(e)
