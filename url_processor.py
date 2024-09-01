"""
File to handle everything with URL processing
"""

from youtube_transcript_api import YouTubeTranscriptApi
import streamlit as st
import os
from pytube import YouTube
import re
import time
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from listennotes import podcast_api
import urllib.parse
import requests
import assemblyai as aai
import asyncio


from firebase_utility import get_remaining_tokens
from utility import subtract_tokens


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


CLIENT_ID = st.secrets["spotify"]["CLIENT_ID"]
CLIENT_SECRET = st.secrets["spotify"]["CLIENT_SECRET"]
LISTEN_NOTES_API_KEY = st.secrets["LISTEN_NOTES_API_KEY"]
ASSEMBLY_AI_API_KEY = st.secrets["ASSEMBLY_AI_API_KEY"]
aai.settings.api_key = ASSEMBLY_AI_API_KEY


# from oculos proxies
PROXY_PASSWORD = st.secrets["PROXY_PASSWORD"]

proxy_ports = ["5868", "5128", "6732", "6754", "5735"]
proxy_usernames = ["ldsiesvc" for _ in range(len(proxy_ports))]
proxy_addresses = ["38.154.227.167", "45.127.248.127", "64.64.118.149", "167.160.180.203", "166.88.58.10"]


all_youtube_languages = [  # NOTE english is first since it has priority
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

# all languages available for assembly ai nano model
assembly_ai_language_codes = ['en',
 'en_au',
 'en_uk',
 'en_us',
 'es',
 'fr',
 'de',
 'it',
 'pt',
 'nl',
 'af',
 'sq',
 'am',
 'ar',
 'hy',
 'as',
 'az',
 'ba',
 'eu',
 'be',
 'bn',
 'bs',
 'br',
 'bg',
 'my',
 'ca',
 'zh',
 'hr',
 'cs',
 'da',
 'et',
 'fo',
 'fi',
 'gl',
 'ka',
 'el',
 'gu',
 'ht',
 'ha',
 'haw',
 'he',
 'hi',
 'hu',
 'is',
 'id',
 'ja',
 'jw',
 'kn',
 'kk',
 'km',
 'ko',
 'lo',
 'la',
 'lv',
 'ln',
 'lt',
 'lb',
 'mk',
 'mg',
 'ms',
 'ml',
 'mt',
 'mi',
 'mr',
 'mn',
 'ne',
 'no',
 'nn',
 'oc',
 'pa',
 'ps',
 'fa',
 'pl',
 'ro',
 'ru',
 'sa',
 'sr',
 'sn',
 'sd',
 'si',
 'sk',
 'sl',
 'so',
 'su',
 'sw',
 'sv',
 'tl',
 'tg',
 'ta',
 'tt',
 'te',
 'th',
 'bo',
 'tr',
 'tk',
 'uk',
 'ur',
 'uz',
 'vi',
 'cy',
 'yi',
 'yo']


# use nano model for transcription. Cheaper and supports more languages


class URLProcessor:
    def __init__(self):
        spotify_auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        self.sp = spotipy.Spotify(auth_manager=spotify_auth_manager)

    
    def retrieve_content(self, link: str):
        remaining_tokens = get_remaining_tokens()
        if remaining_tokens <= 0:
            st.error("You have no remaining credits. Please top up to continue.")
            return
        if "youtube" in link or "youtu.be" in link:
            return self._get_youtube_content(link)
        elif "spotify" in link:
            return self.get_spotify_transcript(link)

        logger.info("Website not added yet") 
        return None

    # youtube
    def _get_id_from_url_youtube(self, url):
        reg_exp = (
            r"^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*"
        )
        match = re.match(reg_exp, url)
        if match and len(match.group(7)) == 11:
            return match.group(7)
        else:
            return

    def _extract_text_youtube(self, video_id):
        for proxy_username, proxy_port, proxy_address in zip(proxy_usernames, proxy_ports, proxy_addresses):
            logger.info("Choosing new proxy")
            proxy_http = f"https://{proxy_username}:{PROXY_PASSWORD}@{proxy_address}:{proxy_port}" # using webshare.io proxies
            try:
                caption = YouTubeTranscriptApi.get_transcript(video_id, proxies={"http": proxy_http}, languages=all_youtube_languages) #  http is supposed to point to proxy_https, doesnt work otherwise
                text = " ".join([x["text"] for x in caption])
                return text
            except Exception as e:
                print(f"Error: {e}")
                logger.info(f"Error when extracting text from youtube video: {e}")
                time.sleep(3)
                logger.info("Retrying...")

    def _extract_title_youtube(self, video_url):
        try:
            video = YouTube(video_url)
            return video.title
        except Exception as e:
            print(f"Failed to get title with error: {e}")
            logger.info(f"Failed to get title with error: {e}")
            return ""

    def _get_youtube_content(self, url):
        video_id = self._get_id_from_url_youtube(url)
        text = self._extract_text_youtube(video_id)

        title = self._extract_title_youtube(url)

        if not text:
            print("Error: Could not extract text from youtube video")
            logger.info("Error: Could not extract text from youtube video")
            return
        content = f"Title: {title}, content: {text}"
        return content


    # spotify
    def get_spotify_transcript(self, spotify_url):
        """parent function to get transcript from spotify url"""
        try:
            podcast_episode_name, podcast_language = self._get_podcast_episode_name_and_language(spotify_url)
            listen_notes_audio_url, podcast_length = self._get_listen_notes_audio_url(podcast_episode_name)
            transcript = self._get_podcast_transcript(listen_notes_audio_url, podcast_language)
            # logger.info(f"Transcript: {transcript}")
            self.calculate_spotify_transcript_price(podcast_length)
            return transcript	
        except Exception as e:
            print(f"Could not get transcript for {spotify_url} with error: {e}")
        
    def calculate_spotify_transcript_price(self, podcast_length):
        """calculate and charge the price of a spotify transcript given podcast length in seconds"""
        price_usd_per_second = 0.12/3600 # 0.12 USD per hour
        price_usd = podcast_length * price_usd_per_second
        price_nok = price_usd * 10.47
        
        logging.info(f"Cost of podcast transcript query: {price_usd:.4f} USD or {price_nok:.4f} NOK")
        PODCAST_TRANSCRIPT_PROFIT_MULTIPLIER = int(os.getenv('PODCAST_TRANSCRIPT_PROFIT_MULTIPLIER'))
        asyncio.run(subtract_tokens(price_usd, PODCAST_TRANSCRIPT_PROFIT_MULTIPLIER))
        return price_usd


    def _get_podcast_episode_id(self, podcast_url):
        parsed_url = urllib.parse.urlparse(podcast_url)
        podcast_id = parsed_url.path.split("/")[-1]
        return podcast_id

    def _get_podcast_episode_name_and_language(self, spotify_url):
        # Extract the episode ID from the URL
        assert "episode" in spotify_url, "URL is not an episode URL. Must link to an episode URL"
        episode_id = self._get_podcast_episode_id(spotify_url)

        episode = self.sp.episode(episode_id)
        episode_name = episode.get("name", "Not found")

        podcast_language = episode.get("language", None)
        if (podcast_language is None) or (podcast_language not in assembly_ai_language_codes):
            podcast_language = "en"
            logger.info("Setting language to English as a baseline, since no valid language was detected")

        return episode_name, podcast_language

    def _get_listen_notes_audio_url(self, episode_name):
        client = podcast_api.Client(api_key=LISTEN_NOTES_API_KEY)
        response = client.search(
            q=episode_name,
            type='episode',
            only_in='title,description',
            page_size=1,
            )
        audio_url = response.json()["results"][0]["audio"]
        podcast_length = response.json()["results"][0]["audio_length_sec"]
        return audio_url, podcast_length

    def _get_podcast_transcript(self, audio_url, podcast_language):
        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.nano, language_code=podcast_language)
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(audio_url)
        full_text = " ".join([item.text for item in transcript.words])
        return full_text

        
