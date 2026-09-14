import base64
import io
import json

import cv2
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

        if image_contains_failed_pattern(img_text):
            print("Image contains failed pattern (red cross)")
            return True
        if is_img_blank(img_blank):
            print("Image is blank")
            return True
        return False

    except Exception as e:
        # If any exception occurs during decoding/processing, image is likely corrupted.jpeg
        print(f"Image corruption detected: {str(e)}")
        return True

def image_contains_failed_pattern(img):
    """Retourne True si l'image contient le motif de croix rouges diagonales
    caracteristique des tuiles WMTS/PCRS manquantes (fiable meme quand l'OCR
    du texte "Failed" echoue)."""
    arr = np.array(img.convert("RGB"))
    r, g, b = arr[:, :, 0].astype(int), arr[:, :, 1].astype(int), arr[:, :, 2].astype(int)
    red_mask = ((r > 150) & (r - g > 40) & (r - b > 40)).astype(np.uint8) * 255

    h, w = red_mask.shape
    diagonal = (h ** 2 + w ** 2) ** 0.5
    min_line_length = int(diagonal * 0.25)

    lines = cv2.HoughLinesP(red_mask, 1, np.pi / 180, threshold=60,
                             minLineLength=min_line_length, maxLineGap=15)
    return lines is not None

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