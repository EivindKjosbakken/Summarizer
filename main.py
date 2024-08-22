import streamlit as st
import fitz 
from dotenv import load_dotenv
import os
from openai import OpenAI
from utility import prompt_gpt, get_openai_client
import streamlit as st


# load keys
load_dotenv()
open_ai_client = get_openai_client()

# init states
if "greeting_sent" not in st.session_state:
    st.session_state.greeting_sent = False  # This flag will track if the greeting has been sent
# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "summary" not in st.session_state:
    st.session_state.summary = None

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
            if uploaded_file is None: st.write("Please upload a PDF file first.")
            else:
                pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                full_text = ""
                for page_number in range(pdf_document.page_count):
                    page = pdf_document.load_page(page_number)
                    page_text = page.get_text("text")
                    full_text += page_text + "\n\n"
                pdf_document.close()

                # TODO remove after testing
                full_text = full_text[:1000]

                st.session_state.summary = "This is a placeholder for the summary of the content."
                prompt = "Summarize this document: " + full_text

                response_text = prompt_gpt(open_ai_client=open_ai_client, prompt=prompt)
                st.session_state.summary = response_text


    # Second column: Link input section
    with col2:
        st.write("Link to a podcast, video, or article to summarize and chat with the content.")
        link = st.text_input("Paste a link", type="default")
        if st.button("Submit Link"):
            st.write(f"Link submitted: {link}")
            # Assuming prompt_gpt is a function that interacts with an AI model
            response_text = prompt_gpt(open_ai_client=open_ai_client, prompt=link)
            st.write("Response:")
            st.write(response_text)



st.write("\n\n")

with st.container():
    st.write("## Summary")
    st.write("This is a placeholder for the summary of the content.")
    if st.session_state.summary is not None: st.write(st.session_state.summary)

with st.container():
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
            st.session_state.messages.append({"role": "assistant", "content": "How can I help you today?"})
            st.session_state.greeting_sent = True  # Update the flag to prevent future greetings

        prompt = st.chat_input("Enter your question here")

        if prompt:
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Prepare the messages for the GPT model
            messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]

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



