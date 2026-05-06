import pytesseract


def extract(image_path: str) -> str:
    return pytesseract.image_to_string(image_path)

