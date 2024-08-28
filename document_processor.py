from pptx import Presentation
import fitz
import textract
import os

def extract_pdf_text(uploaded_file):
    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    full_text = ""
    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)
        page_text = page.get_text("text")
        full_text += page_text + "\n\n"
    pdf_document.close()
    return full_text


def extract_text_textract(uploaded_file):
    """extracts text for pdf, pptx, doc, docx, txt with textract python pacakge. A temp file has to be created to connect st.upload_file and the textract package"""
    bytes_data = uploaded_file.getvalue()
    suffix = uploaded_file.name.split(".")[-1]
    temp_file_path = f"temp_file.{suffix}"
    f = open(temp_file_path, 'wb')
    f.write(bytes_data)
    f.close()
    text = textract.process(temp_file_path).decode("utf-8").replace("\n", " ").replace("  ", " ")
    os.remove(temp_file_path)
    return text