import streamlit as st
import os
import time
import logging
import re
from firebase_utility import db, subtract_user_tokens

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def display_credit_bar(total_credits, remaining_credits):
    st.write(f"Remaining Credits: {round(remaining_credits, 4)}")
    percentage_remaining = (remaining_credits / total_credits) * 100

    # Determine the color based on the remaining credits
    if remaining_credits > 0:
        bar_color = "green" 
    else:
        bar_color = "red"
        percentage_remaining = 100

    
    st.markdown(f"""
    <div style="position: relative; width: 100%; background-color: black; height: 30px; border-radius: 5px;">
        <div style="width: {percentage_remaining}%; background-color: {bar_color}; height: 100%; border-radius: 5px;">
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