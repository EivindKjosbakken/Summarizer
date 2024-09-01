import streamlit as st
import os
import streamlit as st
import fitz
import auth_functions

from llm_agent import LlmAgent
from utility import display_credit_bar
from stripe_payments import create_checkout_session, get_payment_amount, check_payment_status
from document_processor import DocumentProcessor
from firebase_utility import get_user, db, add_user_tokens
from url_processor import URLProcessor

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


llm_agent = LlmAgent()
document_processor = DocumentProcessor()
url_processor = URLProcessor()

STANDARD_START_TOKENS = int(os.getenv('STANDARD_START_TOKENS'))

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
    st.session_state.summary = ""

if "text_content" not in st.session_state:
    st.session_state.text_content = ""

is_signed_in = "user_info" in st.session_state

if "remaining_credits" not in st.session_state:
    st.session_state.remaining_credits = 0 

if 'credits_loaded' not in st.session_state:
    st.session_state.credits_loaded = False

if 'tutorial_step' not in st.session_state:
    st.session_state.tutorial_step = 0

login_warning_text = ":red[Please login to use this feature.]"

# start of the app

# tutorial
with st.sidebar:
    if st.button("Start tutorial for using website", key="start_tutorial"):
        st.session_state.tutorial_step = 1

def next_step():
    st.session_state.tutorial_step += 1
    # reload
    st.rerun()


# Define the custom style for the box using percentage for width
def get_info_box_style(text):
    # Replace \n with <br> for line breaks in HTML
    text = text.replace('\n', '<br>')
    
    custom_box_style = f"""
        <div style="
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ddd;
            width: 25%;         /* Set the width as a percentage of the parent container */
            min-width: 300px;   /* Set a minimum width to prevent the box from getting too small on small screens */
            margin: auto;       /* Center the box horizontally */
        ">
            <p>{text}</p>
        </div>
        """
    return custom_box_style

if "tutorial_step" in st.session_state:
    with st.sidebar:
        if st.session_state.tutorial_step == 1:
            st.markdown(get_info_box_style("<strong>Step 1:</strong>\n Register"), unsafe_allow_html=True)
            if st.button("Next Step", key="next_step_1"):
                next_step()

        if st.session_state.tutorial_step == 2:
            st.markdown(get_info_box_style("<strong>Step 2:</strong>\n Log in"), unsafe_allow_html=True)
            if st.button("Next Step", key="next_step_2"):
                next_step()

        if st.session_state.tutorial_step == 3:
            st.markdown(get_info_box_style("<strong>Step 3:</strong>\n Upload a PDF or link to a YouTube video"), unsafe_allow_html=True)
            if st.button("Next Step", key="next_step_3"):
                next_step()

        if st.session_state.tutorial_step == 4:
            st.markdown(get_info_box_style("<strong>Step 4:</strong>\n Press create summary"), unsafe_allow_html=True)
            if st.button("Next Step", key="next_step_4"):
                next_step()

        if st.session_state.tutorial_step == 5:
            st.markdown(get_info_box_style("<strong>Step 5:</strong>\n Chat with your content"), unsafe_allow_html=True)
            if st.button("Finish", key="finish"):
                st.write("Tutorial finished!")
                st.session_state.tutorial_step = 0


display_credit_bar(total_credits=2000, remaining_credits=st.session_state.remaining_credits) #TODO add so you have remaining credits from firebase
st.write("\n")


def load_button_html(checkout_url, button_text="Top up credits"):
    """load nicely styled button html for redirects"""
    hover_css = """
    <style>
    .stripe-button {
        display: inline-block;
        padding: 15px 32px;
        font-size: 16px;
        color: white !important; /* Ensure text color is white */
        background-color: #008CBA;
        text-align: center;
        text-decoration: none;
        border-radius: 12px;
        cursor: pointer;
        margin: 4px 2px;
        border: none;
        transition: background-color 0.3s ease;
    }
    .stripe-button:hover {
        background-color: #005f73;
        color: white !important; /* Ensure text color remains white on hover */
    }
    </style>
    """
    button_html = f'''
    {hover_css}
    <a href="{checkout_url}" target="_blank" class="stripe-button">{button_text}</a>
    '''
    return button_html

st.title("Content Summarizer and Chat")

# Stripe payment
if st.button("Top up credits"):
    if not is_signed_in:
        st.write(login_warning_text)
    else:
        checkout_url_5_usd = create_checkout_session("5usd")
        checkout_url_10_usd = create_checkout_session("10usd")
        
        st.write("Choose a payment amount...")
        if checkout_url_5_usd and checkout_url_10_usd: 
            with st.container():
                st.markdown(load_button_html(checkout_url_5_usd, "Top up 5 USD"), unsafe_allow_html=True)
                st.markdown(load_button_html(checkout_url_10_usd, "Top up 10 USD"), unsafe_allow_html=True)

            
session_id_param = st.query_params.get('session_id', None)
email_param = st.query_params.get('email', None)
if session_id_param and email_param:
    # Check payment status
    if check_payment_status(session_id_param):

        amount_paid, currency = get_payment_amount(session_id_param)
        assert currency == "usd", "Currency is not USD"
        st.success(f"Payment was successful! Added {amount_paid * 100} to your account! Please log in again to use it")
        st.balloons()
        add_user_tokens(db, email_param, amount_paid * 100)
        logger.info(f"Added {amount_paid * 100} credits to user {email_param}")


    else:
        st.error("Payment failed or was canceled.")
    st.query_params.pop('session_id', None)  # Remove the session_id from the query parameters
     

## Not logged in -----------------------------------------------------------------------------------
with st.sidebar:
    if not is_signed_in:
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
        
        email = st.session_state.user_info['email']
        user_info = get_user(db, email)
        remaining_tokens = user_info.get("remaining_tokens", 0)
        st.session_state.remaining_credits = remaining_tokens

        if not st.session_state.credits_loaded:
            st.session_state.credits_loaded = True
            st.rerun()



with st.container():
    st.write("---")
    col1, col2 = st.columns(2)

    # First column: PDF upload section
    with col1:
        # st.write("Upload a PDF file to summarize and chat with the document.")
        st.write("## Upload PDF")
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf", "pptx", "doc", "docx", "txt"])
        if (uploaded_file):
            full_text = document_processor.extract_text(uploaded_file)
            st.session_state.text_content = full_text
            
        if st.button("Create summary"):
            if not is_signed_in:
                st.write(login_warning_text)
            elif uploaded_file is None:
                st.write(":red[Please upload a PDF file first.]")
            else:
                with st.spinner("Generating summary..."):
                    prompt = "Summarize this: " + full_text
                    response_text = llm_agent.prompt_gpt(prompt=prompt)
                    st.session_state.summary = response_text

    # Second column: Link input section
    with col2:
        st.write("## Link to content")

        link = st.text_input("Paste a link to Spotify episode or YouTube", type="default")
        if st.button("Create a summary from the content in the link"):
            if not is_signed_in:
                st.write(login_warning_text)
            else:
                with st.spinner("Retrieving content and generating summary. This can take up to 180 seconds, but likely less."):

                    content = url_processor.retrieve_content(link)
                    if not content:
                        st.write(":red[Could not retrieve content from the link.]")
                    else:
                        st.session_state.text_content = content
                        prompt = llm_agent.get_prompt(content)
                        response_text = llm_agent.prompt_gpt(prompt=prompt)
                        st.session_state.summary = response_text

st.write("\n\n")

# summary section
with st.container():
    st.write("## Summary")
    # st.write(st.session_state.summary)

    # with st.expander("## Summary", expanded=True):
    #     st.write(st.session_state.summary)
    if (st.session_state.summary != ""):
        st.markdown(f"""
            <div style="border: 1px solid black; padding: 10px; border-radius: 10px; background-color: #f9f9f9;">
                {st.session_state.summary}
            </div>
            """, unsafe_allow_html=True)

# chat section
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
        if not is_signed_in:
            st.warning("Please sign in to use the chat function.")
        else:
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
                stream = llm_agent.prompt_gpt_stream(messages=messages)

                # Display assistant response in chat message container
                response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})

            # calculate price of gpt call
            input_string = ""
            for message in messages:
                input_string += message["content"] + "\n"
            llm_agent.calculate_price(input_string, response)

with st.sidebar: 
    st.write("## Contact")
    st.write("Reach me at summarymate@gmail.com")



