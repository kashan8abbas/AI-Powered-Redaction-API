from PIL import Image, ImageDraw
import easyocr
from fuzzywuzzy import fuzz
import os

reader = easyocr.Reader(['ar'])  

def redact_image_ai(path, phrase, threshold=70):
    image = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(image)

    results = reader.readtext(path)

    for (bbox, text, prob) in results:
        similarity = fuzz.ratio(text.strip(), phrase.strip())
        print(f"Detected: {text} | Match: {similarity}%")
        if similarity >= threshold:
            
            polygon_points = [tuple(map(int, point)) for point in bbox]
            draw.polygon(polygon_points, fill="black")

    output_path = path.replace(".", "_redacted.")
    image.save(output_path)
    return output_path
