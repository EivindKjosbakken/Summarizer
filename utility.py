from dotenv import load_dotenv
import os
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

def get_openai_client():
    OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
    assert OPEN_AI_API_KEY is not None and OPEN_AI_API_KEY.startswith("sk-p") and OPEN_AI_API_KEY.endswith("kUA"), "OpenAI API key is not set."
    return OpenAI(api_key=OPEN_AI_API_KEY)

def prompt_gpt(*, open_ai_client, prompt):
    return open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        ).choices[0].message.content



def calculate_price(input_string, output_string):
    # first convert the input and output strings to tokens
    input_tokens = len(input_string.replace("\n", " ").split())/0.75
    output_tokens = len(output_string.replace("\n", " ").split())/0.75
    # calculate the price in USD
    INPUT_TOKEN_PRICE = 0.15 / 1e6 # price per token
    OUTPUT_TOKEN_PRICE = 0.60 / 1e6
    price_usd = input_tokens * INPUT_TOKEN_PRICE + output_tokens * OUTPUT_TOKEN_PRICE
    price_nok = price_usd*10.47
    # print(f"Cost of query: {price_usd:.4f} USD or {price_nok:.4f} NOK ")
    logging.info(f" Cost of query: {price_usd:.4f} USD or {price_nok:.4f} NOK")
    return price_usd
