# import fitz  # PyMuPDF
# from rapidfuzz import fuzz

# def redact_pdf(pdf_path, phrase, similarity_threshold=70):
#     doc = fitz.open(pdf_path)
#     placeholder_data = []
#     phrase_words = phrase.split()

#     for page in doc:
#         words = page.get_text("words")  # returns (x0, y0, x1, y1, "word", block_no, line_no, word_no)
#         words_sorted = sorted(words, key=lambda w: (w[5], w[6], w[7]))  # sort by block, line, word index
#         num_words = len(words_sorted)

#         i = 0
#         while i < num_words:
#             for window_size in range(1, len(phrase_words) + 3):  # window sizes from 1 to phrase_len+2
#                 if i + window_size > num_words:
#                     break

#                 chunk = words_sorted[i:i + window_size]
#                 chunk_text = " ".join(w[4] for w in chunk)
#                 similarity = fuzz.ratio(chunk_text.lower(), phrase.lower())

#                 if similarity >= similarity_threshold:
#                     x0 = min(w[0] for w in chunk)
#                     y0 = min(w[1] for w in chunk)
#                     x1 = max(w[2] for w in chunk)
#                     y1 = max(w[3] for w in chunk)
#                     rect = fitz.Rect(x0, y0, x1, y1)

#                     # Redaction box
#                     page.add_redact_annot(rect, fill=(1, 1, 1))  # white box
#                     placeholder_data.append((page.number, rect, len(chunk_text)))

#                     i += window_size - 1  # skip already matched words
#                     break
#             i += 1

#     # Apply redactions
#     for page in doc:
#         page.apply_redactions()

#     # Insert placeholder text (e.g., "xxxxx")
#     for page_num, rect, text_len in placeholder_data:
#         page = doc[page_num]
#         placeholder_text = "x" * text_len
#         font_size = rect.height * 0.6

#         page.insert_textbox(
#             rect,
#             placeholder_text,
#             fontsize=font_size,
#             fontname="Times-Roman",
#             align=1,  # center
#             color=(0, 0, 0),  # black
#         )

#     # Save redacted PDF
#     output_path = pdf_path.replace(".pdf", "_redacted.pdf")
#     doc.save(output_path)
#     doc.close()
#     return output_path



import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import easyocr
import io
import numpy as np
from rapidfuzz import fuzz

# EasyOCR reader (Arabic + English)
reader = easyocr.Reader(['en', 'ar'])

def redact_text_on_image(image: Image.Image, phrase: str, threshold=70) -> Image.Image:
    draw = ImageDraw.Draw(image)
    results = reader.readtext(np.array(image))

    for (bbox, text, prob) in results:
        similarity = fuzz.ratio(text.strip().lower(), phrase.strip().lower())

        if similarity >= threshold:
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            top_left = (min(x_coords), min(y_coords))
            bottom_right = (max(x_coords), max(y_coords))

            width = bottom_right[0] - top_left[0]
            height = bottom_right[1] - top_left[1]

            if width > 5 and height > 5 and width < image.width and height < image.height:
                print(f"[Image] Redacting: '{text}' → box: {top_left} to {bottom_right}")
                draw.rectangle([top_left, bottom_right], fill="black")

    return image

def redact_pdf(pdf_path, phrase, similarity_threshold=70):
    doc = fitz.open(pdf_path)
    placeholder_data = []
    phrase_words = phrase.split()

    for page_index, page in enumerate(doc):
        print(f"\n--- Page {page_index + 1} ---")

        # ========== REDACT TEXT ==========
        words = page.get_text("words")
        words_sorted = sorted(words, key=lambda w: (w[5], w[6], w[7]))
        num_words = len(words_sorted)
        i = 0

        while i < num_words:
            for window_size in range(1, len(phrase_words) + 3):
                if i + window_size > num_words:
                    break

                chunk = words_sorted[i:i + window_size]
                chunk_text = " ".join(w[4] for w in chunk)
                similarity = fuzz.ratio(chunk_text.lower(), phrase.lower())

                if similarity >= similarity_threshold:
                    x0 = min(w[0] for w in chunk)
                    y0 = min(w[1] for w in chunk)
                    x1 = max(w[2] for w in chunk)
                    y1 = max(w[3] for w in chunk)
                    rect = fitz.Rect(x0, y0, x1, y1)

                    page.add_redact_annot(rect, fill=(1, 1, 1)) 
                    placeholder_data.append((page.number, rect, len(chunk_text)))

                    print(f"[Text] Redacting: '{chunk_text}' → box: {rect}")
                    i += window_size - 1
                    break
            i += 1

        # ========== REDACT IMAGE ==========
        image_list = page.get_images(full=True)

        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            original_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            redacted_image = redact_text_on_image(original_image, phrase, threshold=similarity_threshold)


            img_io = io.BytesIO()
            redacted_image.save(img_io, format='PNG')
            img_io.seek(0)

            image_info = page.get_image_info(xref)
            if not image_info:
                continue
            bbox = image_info[0]["bbox"]

            page.add_redact_annot(bbox, fill=(1, 1, 1)) 
            page.apply_redactions()
            page.insert_image(bbox, stream=img_io.read())
            print(f"[Image] Redacted and replaced image {img_index+1}")


    for page in doc:
        page.apply_redactions()


    for page_num, rect, text_len in placeholder_data:
        page = doc[page_num]
        placeholder_text = "x" * text_len
        font_size = rect.height * 0.6
        page.insert_textbox(
            rect,
            placeholder_text,
            fontsize=font_size,
            fontname="Times-Roman",
            align=1,
            color=(0, 0, 0),
        )

    output_path = pdf_path.replace(".pdf", "_redacted.pdf")
    doc.save(output_path)
    doc.close()
    print(f"\n✅ Final redacted PDF saved as: {output_path}")
    return output_path


