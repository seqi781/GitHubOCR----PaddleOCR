import easyocr


reader = easyocr.Reader(['en'])


def extract(image_path: str):
    return reader.readtext(image_path, detail=0)

