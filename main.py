import streamlit as st
import fitz 
from dotenv import load_dotenv
import os

load_dotenv()

OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
assert OPEN_AI_API_KEY is not None and OPEN_AI_API_KEY.startswith("sk-p") and OPEN_AI_API_KEY.endswith("kUA"), "OpenAI API key is not set."

st.title("Summarizer")


col1, col2 = st.columns(2)

with col1: 
    st.write("Upload a PDF file to summarize and chat with the document.")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

with col2:
    st.write("Link to a podcast, video or article to summarize and chat with the content.")
    link = st.text_input("Paste a link", type="default")
    if st.button("Submit Link"):
        st.write(f"Link submitted: {link}")

# If a file is uploaded
if uploaded_file is not None:
    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    st.write(f"Number of pages: {pdf_document.page_count}")
    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)
        page_text = page.get_text("text")
        st.write(f"### Page {page_number + 1}")
        st.write(page_text)
    pdf_document.close()

else:
    st.write("Please upload a PDF file to continue.")
