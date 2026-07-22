import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image

from modules.documents.ocr import _preprocess


def test_preprocess_converts_to_grayscale():
    image = Image.new("RGB", (2000, 2000), color=(120, 40, 200))

    result = _preprocess(image)

    assert result.mode == "L"


def test_preprocess_upscales_small_images():
    image = Image.new("RGB", (300, 200), color=(255, 255, 255))

    result = _preprocess(image)

    assert min(result.size) >= 1500


def test_preprocess_leaves_large_images_at_original_size():
    image = Image.new("RGB", (2000, 3000), color=(255, 255, 255))

    result = _preprocess(image)

    assert result.size == (2000, 3000)
