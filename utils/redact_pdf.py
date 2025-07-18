import fitz  # PyMuPDF
from rapidfuzz import fuzz

def redact_pdf(pdf_path, phrase, similarity_threshold=70):
    doc = fitz.open(pdf_path)
    placeholder_data = []
    phrase_words = phrase.split()

    for page in doc:
        words = page.get_text("words")  # returns (x0, y0, x1, y1, "word", block_no, line_no, word_no)
        words_sorted = sorted(words, key=lambda w: (w[5], w[6], w[7]))  # sort by block, line, word index
        num_words = len(words_sorted)

        i = 0
        while i < num_words:
            for window_size in range(1, len(phrase_words) + 3):  # window sizes from 1 to phrase_len+2
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

                    # Redaction box
                    page.add_redact_annot(rect, fill=(1, 1, 1))  # white box
                    placeholder_data.append((page.number, rect, len(chunk_text)))

                    i += window_size - 1  # skip already matched words
                    break
            i += 1

    # Apply redactions
    for page in doc:
        page.apply_redactions()

    # Insert placeholder text (e.g., "xxxxx")
    for page_num, rect, text_len in placeholder_data:
        page = doc[page_num]
        placeholder_text = "x" * text_len
        font_size = rect.height * 0.6

        page.insert_textbox(
            rect,
            placeholder_text,
            fontsize=font_size,
            fontname="Times-Roman",
            align=1,  # center
            color=(0, 0, 0),  # black
        )

    # Save redacted PDF
    output_path = pdf_path.replace(".pdf", "_redacted.pdf")
    doc.save(output_path)
    doc.close()
    return output_path


