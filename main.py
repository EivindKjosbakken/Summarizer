import streamlit as st
import os
from openai import OpenAI
from utility import prompt_gpt, get_openai_client, calculate_price
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator import Hasher
import fitz
from utility import retrieve_content, get_prompt
import yaml
from yaml.loader import SafeLoader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config_file_path = "./config.yaml"
with open(config_file_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

# load keys
open_ai_client = get_openai_client()


# Pre-hashing all plain text passwords once
Hasher.hash_passwords(config["credentials"])

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
    config["pre-authorized"],
)

# authentication code

if "sidebar_visible" not in st.session_state: st.session_state.sidebar_visible = True

if "authentication_status" not in st.session_state: st.session_state["authentication_status"] = False

def toggle_sidebar():
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible


# Function to update the config file
def update_config():
    with open(config_file_path, "w") as file:
        yaml.dump(config, file, default_flow_style=False)


if st.button("Toggle authentication sidebar"):
    toggle_sidebar()

if st.session_state.sidebar_visible:
    with st.sidebar:
        authenticator.login(location="sidebar", clear_on_submit=True)
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
                location="sidebar", captcha=False, pre_authorization=False, domains=None, clear_on_submit=True
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


# init states
if "greeting_sent" not in st.session_state:
    st.session_state.greeting_sent = (
        False  # This flag will track if the greeting has been sent
    )
# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "summary" not in st.session_state:
    st.session_state.summary = "This is a placeholder for the summary of the content."

if "text_content" not in st.session_state:
    st.session_state.text_content = ""

# start of the app
st.title("Summarizer")
st.write("## Content Summarizer and Chat")


with st.container():
    st.write("---")
    col1, col2 = st.columns(2)

    # First column: PDF upload section
    with col1:
        st.write("Upload a PDF file to summarize and chat with the document.")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        if st.button("Create summary of PDF"):
            if uploaded_file is None:
                st.write(":red[Please upload a PDF file first.]")
            if not st.session_state["authentication_status"]:
                st.write(":red[Please login to use this feature.]")
            else:
                pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                full_text = ""
                for page_number in range(pdf_document.page_count):
                    page = pdf_document.load_page(page_number)
                    page_text = page.get_text("text")
                    full_text += page_text + "\n\n"
                pdf_document.close()
                st.session_state.text_content = full_text

                # TODO remove after testing
                if len(full_text) > 10000: full_text = full_text[:10000]

                prompt = "Summarize this document: " + full_text

                response_text = prompt_gpt(open_ai_client=open_ai_client, prompt=prompt)
                st.session_state.summary = response_text

    # Second column: Link input section
    with col2:
        st.write(
            "Link to a podcast, video, or article to summarize and chat with the content. Note that if the content is behind a paywall it cannot be accessed. Consider uploading content as PDF instead."
        )
        link = st.text_input("Paste a link", type="default")
        if st.button("Create a summary from the content in the link"):
            if not st.session_state["authentication_status"]:
                st.write(":red[Please login to use this feature.]")
            else:
                st.write(f"Retrieving summary...")

                content = retrieve_content(link)
                if not content:
                    st.write("Could not retrieve content from the link.")
                else:
                    if len(content) > 10000: content = content[:10000] #TODO remove later 
                    st.session_state.text_content = content
                    prompt = get_prompt(content)
                    response_text = prompt_gpt(open_ai_client=open_ai_client, prompt=prompt)
                    st.session_state.summary = response_text


st.write("\n\n")

# summary section
with st.container():
    st.write("## Summary")
    if st.session_state.summary is not None:
        st.write(st.session_state.summary)

# chat section
# with st.container():
st.write("## Chat")

if st.session_state.summary is None:
    st.write("The chat function will open once you have uploaded some content.")
else:
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not st.session_state.greeting_sent:
        with st.chat_message("assistant"):
            st.markdown("How can I help you today?")
        st.session_state.messages.append(
            {"role": "assistant", "content": "How can I help you today?"}
        )
        st.session_state.greeting_sent = (
            True  # Update the flag to prevent future greetings
        )

    prompt = st.chat_input("Enter your question here")

    if (
        prompt
    ):  # NOTE do not have container, that messes up so chat gets below the prompt
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Prepare the messages for the GPT model
        messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        # insert a new message first in the messages array
        messages.insert(
            0,
            {
                "role": "user",
                "content": f"Answer given the following context {st.session_state.text_content}. Keep your answers concise.",
            },
        )

        # Generate a response using the GPT model
        with st.chat_message("assistant"):
            stream = open_ai_client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=messages,
                stream=True,
            )

            # Display assistant response in chat message container
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})

        # calculate price of gpt call
        input_string = ""
        for message in messages:
            input_string += message["content"] + "\n"
        calculate_price(input_string, response)
