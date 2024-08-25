import streamlit as st
import os
from openai import OpenAI
from utility import prompt_gpt, get_openai_client, calculate_price, display_credit_bar
import streamlit as st
import fitz
from utility import retrieve_content, get_prompt
import yaml
import auth_functions
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# load keys
open_ai_client = get_openai_client()



def toggle_sidebar():
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible


if st.button("Toggle authentication sidebar"):
    toggle_sidebar()
st.write("\n")

display_credit_bar(total_credits=10000, remaining_credits=100) #TODO add so you have remaining credits from firebase
st.write("\n")


# add a colored button with a link to my page
link = "https://buymeacoffee.com/kjosbakken"
button_text = "Buy me a coffee"

# Custom HTML for a button styled like a Streamlit button with a positive green color
button_html = f"""
    <style>
        .button {{
            display: inline-block;
            background-color: #4CAF50; /* Green color */
            color: white;
            padding: 0.25em 0.75em;
            font-size: 1rem;
            font-weight: 400;
            text-align: center;
            text-decoration: none;
            border-radius: 0.25rem;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }}
        .button:hover {{
            background-color: #45A049; /* Slightly darker green on hover */
        }}
    </style>
    <a href="{link}" target="_blank">
        <button class="button">{button_text}</button>
    </a>
"""
st.markdown(button_html, unsafe_allow_html=True)




## Not logged in -----------------------------------------------------------------------------------
with st.sidebar:
    if 'user_info' not in st.session_state:
        col1,col2,col3 = st.columns([1,2,1])

        # Authentication form layout
        do_you_have_an_account = col2.selectbox(label='Do you have an account?',options=('Yes','No','I forgot my password'))
        auth_form = col2.form(key='Authentication form',clear_on_submit=False)
        email = auth_form.text_input(label='Email')
        password = auth_form.text_input(label='Password',type='password') if do_you_have_an_account in {'Yes','No'} else auth_form.empty()
        auth_notification = col2.empty()

        # Sign In
        if do_you_have_an_account == 'Yes' and auth_form.form_submit_button(label='Sign In',use_container_width=True,type='primary'):
            with auth_notification, st.spinner('Signing in'):
                auth_functions.sign_in(email,password)

        # Create Account
        elif do_you_have_an_account == 'No' and auth_form.form_submit_button(label='Create Account',use_container_width=True,type='primary'):
            with auth_notification, st.spinner('Creating account'):
                auth_functions.create_account(email,password)

        # Password Reset
        elif do_you_have_an_account == 'I forgot my password' and auth_form.form_submit_button(label='Send Password Reset Email',use_container_width=True,type='primary'):
            with auth_notification, st.spinner('Sending password reset link'):
                auth_functions.reset_password(email)

        # Authentication success and warning messages
        if 'auth_success' in st.session_state:
            auth_notification.success(st.session_state.auth_success)
            del st.session_state.auth_success
        elif 'auth_warning' in st.session_state:
            auth_notification.warning(st.session_state.auth_warning)
            del st.session_state.auth_warning

    ## Logged in --------------------------------------------------------------------------------------
    else:
        # Sign out
        st.header('Sign out:')
        st.button(label='Sign Out',on_click=auth_functions.sign_out,type='primary')

        # Delete Account
        st.header('Delete account:')
        password = st.text_input(label='Confirm your password',type='password')
        st.button(label='Delete Account',on_click=auth_functions.delete_account,args=[password],type='primary')


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
st.title("Content Summarizer and Chat")


with st.container():
    st.write("---")
    col1, col2 = st.columns(2)

    # First column: PDF upload section
    with col1:
        # st.write("Upload a PDF file to summarize and chat with the document.")
        st.write("## Upload PDF")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        if st.button("Create summary of PDF"):
            if uploaded_file is None:
                st.write(":red[Please upload a PDF file first.]")
            if 'user_info' not in st.session_state: # not signed in
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
        st.write("## Link to content")

        link = st.text_input("Paste a link", type="default")
        if st.button("Create a summary from the content in the link"):
            logger.info("TRYKKA KNAPPEN")
            if 'user_info' not in st.session_state:
                st.write(":red[Please login to use this feature.]")
            else:

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

