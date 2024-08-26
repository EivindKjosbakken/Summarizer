import streamlit as st
import os
import time
from openai import OpenAI
import logging
import re
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
from firebase_utility import get_user, db, subtract_user_tokens
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# set up proxy TODO make code cleaner into env variables
PROXY_ADDRESS = st.secrets["PROXY_ADDRESS"]
PROXY_PORT = st.secrets["PROXY_PORT"]
PROXY_USERNAME = st.secrets["PROXY_USERNAME"]
PROXY_PASSWORD = st.secrets["PROXY_PASSWORD"]
proxy = f"https://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_ADDRESS}:{PROXY_PORT}"

PROFIT_MULTIPLIER = int(os.getenv('PROFIT_MULTIPLIER'))


def get_openai_client():
    OPEN_AI_API_KEY = st.secrets["OPEN_AI_API_KEY"]
    assert (
        OPEN_AI_API_KEY is not None
        and OPEN_AI_API_KEY.startswith("sk-p")
        and OPEN_AI_API_KEY.endswith("kUA")
    ), "OpenAI API key is not set."
    return OpenAI(api_key=OPEN_AI_API_KEY)


def prompt_gpt(*, open_ai_client, prompt):
    response_text = (
        open_ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        .choices[0]
        .message.content
    )
    calculate_price(prompt, response_text)
    return response_text


def calculate_price(input_string, output_string):
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
    
    # subtract_tokens(price_usd)
    asyncio.run(subtract_tokens(price_usd))
    return price_usd

async def subtract_tokens(usd_spent: float):
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


#TODO lage en youtube agent ellerno?
def get_id_from_url_youtube(url):
    reg_exp = (
        r"^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*"
    )
    match = re.match(reg_exp, url)
    if match and len(match.group(7)) == 11:
        return match.group(7)
    else:
        return

def extract_text_youtube(video_id):
    for _ in range(5): # try up to 5 times, wait 1 sec if it fails
        try:
            # caption = YouTubeTranscriptApi.get_transcript(video_id)
            caption = YouTubeTranscriptApi.get_transcript(video_id, proxies={"http": proxy})
            text = " ".join([x["text"] for x in caption])
            return text
        except Exception as e:
            print(f"Error: {e}")
            logger.info(f"Error when extracting text from youtube video: {e}")
            time.sleep(1)
            logger.info("Retrying...")
    return

def extract_title_youtube(video_url):
    try:
        video = YouTube(video_url)
        return video.title
    except Exception as e:
        print(f"Failed to get title with error: {e}")
        logger.info(f"Failed to get title with error: {e}")
        return ""

def get_youtube_content(url):
    video_id = get_id_from_url_youtube(url)
    text = extract_text_youtube(video_id)

    title = extract_title_youtube(url)

    if not text:
        print("Error: Could not extract text from youtube video")
        logger.info("Error: Could not extract text from youtube video")
        return
    content = f"Title: {title}, content: {text}"
    return content

def retrieve_content(link: str):
    if "youtube" in link or "youtu.be" in link:
        return get_youtube_content(link)
    logger.info("Website not added yet") 
    return None


def get_prompt(content):
    """get prompt for summary"""
    return f"Summarize this document: {content}"


def display_credit_bar(total_credits, remaining_credits):
    st.write(f"Remaining Credits: {round(remaining_credits, 4)}")
    percentage_remaining = (remaining_credits / total_credits) * 100
    
    st.markdown(f"""
    <div style="position: relative; width: 100%; background-color: black; height: 30px; border-radius: 5px;">
        <div style="width: {percentage_remaining}%; background-color: green; height: 100%; border-radius: 5px;">
        </div>
    </div>
    """, unsafe_allow_html=True)