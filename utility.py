import streamlit as st
import os
import time
import logging
import re
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
from firebase_utility import get_remaining_tokens

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# set up proxy TODO make code cleaner into env variables
PROXY_ADDRESS = st.secrets["PROXY_ADDRESS"]
PROXY_PORT = st.secrets["PROXY_PORT"]
PROXY_USERNAME = st.secrets["PROXY_USERNAME"]
PROXY_PASSWORD = st.secrets["PROXY_PASSWORD"]
proxy_https = f"https://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_ADDRESS}:{PROXY_PORT}"

PROFIT_MULTIPLIER = int(os.getenv('PROFIT_MULTIPLIER'))

all_languages = [  # NOTE english is first since it has priority
    "en", "de", "fr", "ab", "aa", "af", "ak", "sq", "am", "ar", "hy", "as", "ay", "az", "bn", 
    "ba", "eu", "be", "bho", "bs", "br", "bg", "my", "ca", "ceb", "zh-Hans", 
    "zh-Hant", "co", "hr", "cs", "da", "dv", "nl", "dz", "eo", "et", 
    "ee", "fo", "fj", "fil", "fi", "gaa", "gl", "lg", "ka", 
    "el", "gn", "gu", "ht", "ha", "haw", "iw", "hi", "hmn", "hu", "is", 
    "ig", "id", "ga", "it", "ja", "jv", "kl", "kn", "kk", "kha", "km", 
    "rw", "ko", "kri", "ku", "ky", "lo", "la", "lv", "ln", "lt", "luo", 
    "lb", "mk", "mg", "ms", "ml", "mt", "gv", "mi", "mr", "mn", "mfe", 
    "ne", "new", "nso", "no", "ny", "oc", "or", "om", "os", "pam", "ps", 
    "fa", "pl", "pt", "pt-PT", "pa", "qu", "ro", "rn", "ru", "sm", "sg", 
    "sa", "gd", "sr", "crs", "sn", "sd", "si", "sk", "sl", "so", "st", 
    "es", "su", "sw", "ss", "sv", "tg", "ta", "tt", "te", "th", "bo", 
    "ti", "to", "ts", "tn", "tum", "tr", "tk", "uk", "ur", "ug", "uz", 
    "ve", "vi", "war", "cy", "fy", "wo", "xh", "yi", "yo", "zu"
]



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
    for _ in range(10): # try up to 10 times, wait 1 sec if it fails
        try:
            # caption = YouTubeTranscriptApi.get_transcript(video_id)
            caption = YouTubeTranscriptApi.get_transcript(video_id, proxies={"http": proxy_https}, languages=all_languages) #  http is supposed to point to proxy_https, doesnt work otherwise
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
    remaining_tokens = get_remaining_tokens()
    if remaining_tokens <= 0:
        st.error("You have no remaining credits. Please top up to continue.")
        return
    if "youtube" in link or "youtu.be" in link:
        return get_youtube_content(link)
    logger.info("Website not added yet") 
    return None





def display_credit_bar(total_credits, remaining_credits):
    st.write(f"Remaining Credits: {round(remaining_credits, 4)}")
    percentage_remaining = (remaining_credits / total_credits) * 100
    
    st.markdown(f"""
    <div style="position: relative; width: 100%; background-color: black; height: 30px; border-radius: 5px;">
        <div style="width: {percentage_remaining}%; background-color: green; height: 100%; border-radius: 5px;">
        </div>
    </div>
    """, unsafe_allow_html=True)