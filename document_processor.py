from pptx import Presentation
import fitz



def extract_pdf_text(uploaded_file):
    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    full_text = ""
    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)
        page_text = page.get_text("text")
        full_text += page_text + "\n\n"
    pdf_document.close()
    return full_text

def extract_pptx_text(uploaded_file):
    ppt = Presentation(uploaded_file)
    full_text = ""
    for slide in ppt.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                full_text += shape.text + " "
    return full_text
    
