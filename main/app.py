import base64
import io
import json

import cv2
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
        if ',' in base64_img:
            base64_img = base64_img.split(',')[1]

        img_bytes = base64.b64decode(base64_img)
        img_text = Image.open(io.BytesIO(img_bytes))
        img_blank = np.array(img_text)

        if image_contains_failed_text(img_text):
            print("Image contains failed text")
            return True
        if is_img_blank(img_blank):
            print("Image is blank")
            return True
        return False

    except Exception as e:
        # If any exception occurs during decoding/processing, image is likely corrupted.jpeg
        print(f"Image corruption detected: {str(e)}")
        return True

def image_contains_failed_text(img):
    """Retourne True si l'image contient un mot-cle d'echec."""
    failed_keywords = ("failed", "wmts")

    gray = np.array(img.convert("L"))

    # Upscale : Tesseract est nettement plus fiable si le texte est grand.
    # INTER_LINEAR est plus rapide que INTER_CUBIC pour un resultat quasi identique ici.
    scale = 1.5
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

    # Otsu au lieu d'un seuil fixe : s'adapte au contraste de chaque image
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    thresh_inv = cv2.bitwise_not(thresh)

    # Un seul PSM (6), mais les deux polarites (texte sombre/clair) car c'est
    # ce qui fait le plus varier la lecture selon les images
    candidates = [
        (thresh, r'--oem 3 --psm 6'),
        (thresh_inv, r'--oem 3 --psm 6'),
    ]

    for image_variant, config in candidates:
        try_text = pytesseract.image_to_string(image_variant, config=config)
        txt_norm = try_text.lower().strip()

        if any(k in txt_norm for k in failed_keywords):
            return True

    return False

def is_img_blank(img):
    if np.all(img == 0) or np.all(img == 255):
        return True
    return False

if __name__ == "__main__":
    with open("saint-denis.jpeg", "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    event = {
        "body": json.dumps({
            "base64image": img_base64
        })
    }

    result = lambda_handler(event, None)
    print(result)