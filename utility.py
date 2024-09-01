import streamlit as st
import os
import time
import logging
import re
from firebase_utility import db, subtract_user_tokens

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# set up proxy TODO make code cleaner into env variables
PROXY_ADDRESS = st.secrets["PROXY_ADDRESS"]
PROXY_PORT = st.secrets["PROXY_PORT"]
PROXY_USERNAME = st.secrets["PROXY_USERNAME"]
PROXY_PASSWORD = st.secrets["PROXY_PASSWORD"]
proxy_https = f"https://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_ADDRESS}:{PROXY_PORT}"

PROFIT_MULTIPLIER = int(os.getenv('PROFIT_MULTIPLIER'))




def display_credit_bar(total_credits, remaining_credits):
    st.write(f"Remaining Credits: {round(remaining_credits, 4)}")
    percentage_remaining = (remaining_credits / total_credits) * 100
    
    st.markdown(f"""
    <div style="position: relative; width: 100%; background-color: black; height: 30px; border-radius: 5px;">
        <div style="width: {percentage_remaining}%; background-color: green; height: 100%; border-radius: 5px;">
        </div>
    </div>
    """, unsafe_allow_html=True)


async def subtract_tokens(usd_spent: float, profit_multiplier: int):
    """subtracts tokens from a user every time they use a service"""
    cent_spent = usd_spent * 100 # only use cent in db
    # round to nearest 100
    cent_spent = round(cent_spent, 4)
    
    # get user tokens
    email = st.session_state.user_info['email']
    tokens_to_subtract = cent_spent * profit_multiplier
    remaining_tokens = subtract_user_tokens(db, email, tokens_to_subtract)
    print(f"Subtracted {tokens_to_subtract} tokens from user {email}. User has {remaining_tokens} tokens left")
    st.session_state.remaining_tokens = remaining_tokens