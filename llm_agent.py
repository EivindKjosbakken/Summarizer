from firebase_utility import db, subtract_user_tokens, get_remaining_tokens
import streamlit as st
from openai import OpenAI
import asyncio
import os

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# set up proxy TODO make code cleaner into env variables
PROXY_ADDRESS = st.secrets["PROXY_ADDRESS"]
PROXY_PORT = st.secrets["PROXY_PORT"]
PROXY_USERNAME = st.secrets["PROXY_USERNAME"]
PROXY_PASSWORD = st.secrets["PROXY_PASSWORD"]
proxy = f"https://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_ADDRESS}:{PROXY_PORT}"

PROFIT_MULTIPLIER = int(os.getenv('PROFIT_MULTIPLIER'))


class LlmAgent:
    def __init__(self):
        self.open_ai_client = self.get_openai_client()
                  
    def get_openai_client(self):
        OPEN_AI_API_KEY = st.secrets["OPEN_AI_API_KEY"]
        assert (
            OPEN_AI_API_KEY is not None
            and OPEN_AI_API_KEY.startswith("sk-p")
            and OPEN_AI_API_KEY.endswith("kUA")
        ), "OpenAI API key is not set."
        return OpenAI(api_key=OPEN_AI_API_KEY)


    def prompt_gpt(self, prompt):
        # first check if user has remaining credits
        remaining_tokens = get_remaining_tokens()
        if remaining_tokens <= 0:
            st.error("You have no remaining credits. Please top up to continue.")
            return
        response_text = (
            self.open_ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. If someone asks who your creator is or who you are, answer 'Grøkk Naked'"},
                    {"role": "user", "content": prompt},
                ],
            )
            .choices[0]
            .message.content
        )
        self.calculate_price(prompt, response_text)
        return response_text

    def prompt_gpt_stream(self, messages):
        """similar to prompt gpt, but returns a stream (print out model output as it is generated). Also manually inputs messages used for prompt"""
        stream = self.open_ai_client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=messages,
            stream=True,
        )
        return stream


    def calculate_price(self, input_string, output_string):
        # first convert the input and output strings to tokens
        input_tokens = len(input_string.replace("\n", " ").split()) / 0.75
        output_tokens = len(output_string.replace("\n", " ").split()) / 0.75
        # calculate the price in USD
        INPUT_TOKEN_PRICE = 0.15 / 1e6  # price per token
        OUTPUT_TOKEN_PRICE = 0.60 / 1e6
        price_usd = input_tokens * INPUT_TOKEN_PRICE + output_tokens * OUTPUT_TOKEN_PRICE
        price_nok = price_usd * 10.47
        # print(f"Cost of query: {price_usd:.4f} USD or {price_nok:.4f} NOK ")
        logging.info(f" Cost of query: {price_usd:.4f} USD or {price_nok:.4f} NOK")
        
        asyncio.run(self.subtract_tokens(price_usd)) # async subtract tokens. Async to avoid increase waiting time for llm response
        return price_usd

    async def subtract_tokens(self, usd_spent: float):
        """subtracts tokens from a user every time they use a service"""
        cent_spent = usd_spent * 100 # only use cent in db
        # round to nearest 100
        cent_spent = round(cent_spent, 4)
        
        # get user tokens
        email = st.session_state.user_info['email']
        tokens_to_subtract = cent_spent * PROFIT_MULTIPLIER
        remaining_tokens = subtract_user_tokens(db, email, tokens_to_subtract)
        print(f"Subtracted {cent_spent} tokens from user {email}. User has {remaining_tokens} tokens left")
        st.session_state.remaining_tokens = remaining_tokens


    def get_prompt(self, content):
        """get prompt for summary"""
        return f"Summarize this: {content}"