import cv2
import numpy as np
import io

def detect_document(image):
    orig = image.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5,5), 0)

    edges = cv2.Canny(gray, 75, 200)
    edges = cv2.dilate(edges, np.ones((5,5), np.uint8), iterations=1)

    cnts, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    doc_cnt = None
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            doc_cnt = approx
            break

    if doc_cnt is None:
        return orig

    pts = doc_cnt.reshape(4, 2)
    rect = np.zeros((4,2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    (tl, tr, br, bl) = rect
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = int(max(heightA, heightB))

    dst = np.array([[0,0],[maxWidth-1,0],[maxWidth-1,maxHeight-1],[0,maxHeight-1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))

    return warped


def enhance_document(input_bytesio):
    """
    input_bytesio: BytesIO containing image data
    returns: BytesIO with enhanced image
    """
    # Convert BytesIO -> numpy array
    file_bytes = np.frombuffer(input_bytesio.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # Optional: detect document and crop
    # img = detect_document(img)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Remove shadows
    dilated = cv2.dilate(gray, np.ones((9,9), np.uint8))
    bg = cv2.medianBlur(dilated, 25)
    no_shadow = 255 - cv2.absdiff(gray, bg)

    # 2. CLAHE
    clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(8,8))
    clahe_img = clahe.apply(no_shadow)

    # 3. Smooth handwriting
    smooth = cv2.bilateralFilter(clahe_img, d=7, sigmaColor=50, sigmaSpace=50)

    # 4. Clean background
    _, cleaned = cv2.threshold(smooth, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Convert back to BytesIO
    is_success, buffer = cv2.imencode(".png", cleaned)
    if not is_success:
        raise Exception("Failed to encode image")

    output_bytesio = io.BytesIO(buffer.tobytes())
    output_bytesio.seek(0)
    return output_bytesio
