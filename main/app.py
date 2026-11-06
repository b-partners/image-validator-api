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

        # Test d'image vide en premier : quelques ms, evite les deux passes OCR
        if is_img_blank(img_blank):
            print("Image is blank")
            return True
        # Detection par pixels (quelques ms) avant l'OCR : la lecture Tesseract du
        # filigrane "Failed: wmts_..." depend de la taille du texte et la rate parfois
        if image_contains_failed_tile_pattern(img_text):
            print("Image contains failed tile pattern")
            return True
        if image_contains_failed_text(img_text):
            print("Image contains failed text")
            return True
        return False

    except Exception as e:
        # If any exception occurs during decoding/processing, image is likely corrupted.jpeg
        print(f"Image corruption detected: {str(e)}")
        return True

FAILED_PATTERN_GRID = 8
FAILED_PATTERN_MIN_CELLS = 6


def image_contains_failed_tile_pattern(img):
    """Retourne True si l'image contient le motif d'echec GeoServer : traits rouges
    satures (croix + texte "Failed: wmts_...") sur fond blanc.

    On ne garde que les pixels rouges entoures de blanc, puis on exige que le motif
    s'etale sur plusieurs cellules quasi blanches de l'image : un logo ou un objet
    rouge sur un toit blanc ou de la neige reste localise, le motif d'echec non.
    """
    rgb = np.asarray(img.convert("RGB"), dtype=np.int16)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    height, width = r.shape

    white = (np.minimum(np.minimum(r, g), b) >= 215).astype(np.float32)
    window = max(15, (min(height, width) // 32) | 1)
    white_background = cv2.blur(white, (window, window)) >= 0.80
    saturated_red = (r >= 140) & (r - g >= 45) & (r - b >= 45)
    red_on_white = saturated_red & white_background

    rows = np.linspace(0, height, FAILED_PATTERN_GRID + 1).astype(int)
    cols = np.linspace(0, width, FAILED_PATTERN_GRID + 1).astype(int)
    failed_cells = 0
    for i in range(FAILED_PATTERN_GRID):
        for j in range(FAILED_PATTERN_GRID):
            cell = (slice(rows[i], rows[i + 1]), slice(cols[j], cols[j + 1]))
            if white[cell].mean() >= 0.85 and red_on_white[cell].mean() >= 0.0005:
                failed_cells += 1

    return failed_cells >= FAILED_PATTERN_MIN_CELLS


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
    with open("../images-dataset/saint-denis.jpeg", "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    event = {
        "body": json.dumps({
            "base64image": img_base64
        })
    }

    result = lambda_handler(event, None)
    print(result)