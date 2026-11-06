"""Non-regression du validateur sur images-dataset.

Lancement : python tests/test_failed_tile_pattern.py  (ou pytest tests/)

Les noms de fichiers du dataset sont trompeurs : les failed_*_FLUX_IGN_* sont
des images valides. La verite terrain est donc listee explicitement ici.
"""
import base64
import io
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "main"))

from app import image_contains_failed_tile_pattern, is_image_corrupted  # noqa: E402

DATASET = os.path.join(ROOT, "images-dataset")

FAILED_IMAGES = {
    "HAUTE-SAVOIE_2025_5CM.jpg",
    "PCRS_1024_failed.jpg",
    "PCRS_probe_nimes_failed.jpg",
    "corrupted.jpeg",
    "failed_MARNE_2026.jpg",
}


def _dataset_images():
    return sorted(
        name for name in os.listdir(DATASET)
        if name.lower().endswith((".jpg", ".jpeg", ".png"))
    )


def _as_geodata_sends_it(path):
    # geodata re-encode l'image en JPEG (ImageIO) avant de l'envoyer au validateur
    buffer = io.BytesIO()
    Image.open(path).convert("RGB").save(buffer, "JPEG", quality=75)
    buffer.seek(0)
    return buffer


def test_failed_tile_pattern_matches_ground_truth():
    errors = []
    for name in _dataset_images():
        image = Image.open(_as_geodata_sends_it(os.path.join(DATASET, name)))
        expected = name in FAILED_IMAGES
        if image_contains_failed_tile_pattern(image) != expected:
            errors.append(f"{name}: expected failed={expected}")
    assert not errors, errors


def test_valid_images_are_not_corrupted():
    errors = []
    for name in _dataset_images():
        if name in FAILED_IMAGES:
            continue
        payload = base64.b64encode(_as_geodata_sends_it(os.path.join(DATASET, name)).read())
        if is_image_corrupted(payload.decode()):
            errors.append(name)
    assert not errors, f"valid images flagged as corrupted: {errors}"


if __name__ == "__main__":
    test_failed_tile_pattern_matches_ground_truth()
    test_valid_images_are_not_corrupted()
    print("OK")
