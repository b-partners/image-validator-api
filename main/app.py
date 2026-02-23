import base64
import io
import json
import pytesseract
import numpy as np
from PIL import Image


def lambda_handler(event, context):
    body = json.loads(event["body"])
    image_base64 = body["base64image"]
    is_corrupted = is_image_corrupted(image_base64)
    print("is image corrupted", is_corrupted)
    return {
        "statusCode": 200,
        "body": json.dumps({"isCorrupted": is_corrupted})
    }


def is_image_corrupted(base64_img):
    try:
        # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
        if ',' in base64_img:
            base64_img = base64_img.split(',')[1]

        # Decode base64 to bytes and convert bytes to image
        img_bytes = base64.b64decode(base64_img)
        img = Image.open(io.BytesIO(img_bytes))
        if image_contains_failed_text(img) or is_img_blank(img):
            return True
        return False

    except Exception as e:
        # If any exception occurs during decoding/processing, image is likely corrupted
        print(f"Image corruption detected: {str(e)}")
        return True


def image_contains_failed_text(img):
    failed_keywords = ("failed", "wmts")
    """
    Retourne True si le texte OCRisé de l'image contient l'un des mots-clés indiquant un échec.
    """
    gray = img.convert("L")
    bw = gray.point(lambda x: 0 if x < 200 else 255, mode="1")

    try_text = pytesseract.image_to_string(bw)
    txt_norm = try_text.lower()
    return any(k in txt_norm for k in failed_keywords)

def is_img_blank(img):
    if np.all(img == 0) or np.all(img == 255):
        return True
    return False