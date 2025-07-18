from docx import Document
import os

def redact_docx(input_path, phrase):
    doc = Document(input_path)
    redacted = False

    for para in doc.paragraphs:
        if phrase in para.text:
            para.text = para.text.replace(phrase, "xxxxx")
            redacted = True

    output_path = input_path.replace(".", "_redacted.")
    doc.save(output_path)
    return output_path
