import os
from openai import OpenAI
import logging
import re
from youtube_transcript_api import YouTubeTranscriptApi
import re
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
import streamlit as st
from typing import Optional


logging.basicConfig(level=logging.INFO)



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
    return price_usd


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
    try:
        caption = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([x["text"] for x in caption])
        return text
    except Exception as e:
        print(f"Error: {e}")
        return


def extract_title_youtube(video_url):
    try:
        video = YouTube(video_url)
    except Exception as e:
        print(f"Failed to get title with error: {e}")
        return ""
    return video.title


def get_youtube_content(url):
    video_id = get_id_from_url_youtube(url)
    text = extract_text_youtube(video_id)

    title = extract_title_youtube(url)

    if not text:
        print("Error: Could not extract text from youtube video")
        return
    content = f"Title: {title}, content: {text}"
    return content


def retrieve_content(link: str):
    if "youtube" in link:
        return get_youtube_content(link)
    return None


def get_prompt(content):
    """get prompt for summary"""
    return f"Summarize this document: {content}"
