
import cv2
import numpy as np

def detect_document(image):
    orig = image.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5,5), 0)

    # Edge detection
    edges = cv2.Canny(gray, 75, 200)
    edges = cv2.dilate(edges, np.ones((5,5), np.uint8), iterations=1)

    # Contours
    cnts, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    doc_cnt = None
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4:    # quadrilateral detected
            doc_cnt = approx
            break

    if doc_cnt is None:
        return orig  # no document found → return unchanged

    # ---- Perspective transform ----
    pts = doc_cnt.reshape(4, 2)

    # Order points (top-left → clockwise)
    rect = np.zeros((4,2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # TL
    rect[2] = pts[np.argmax(s)]   # BR

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # TR
    rect[3] = pts[np.argmax(diff)]  # BL

    (tl, tr, br, bl) = rect

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = int(max(heightA, heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))

    return warped


def enhance_document(input_path, output_path):
    img = cv2.imread(input_path)

    # ✨ FIRST: crop document properly
    #img = detect_document(img)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Remove shadows
    dilated = cv2.dilate(gray, np.ones((9, 9), np.uint8))
    bg = cv2.medianBlur(dilated, 25)
    no_shadow = 255 - cv2.absdiff(gray, bg)

    # 2. CLAHE
    clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(8,8))
    clahe_img = clahe.apply(no_shadow)

    # 3. Smooth handwriting
    smooth = cv2.bilateralFilter(clahe_img, d=7, sigmaColor=50, sigmaSpace=50)

    # 4. Clean background
    _, cleaned = cv2.threshold(smooth, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    cv2.imwrite(output_path, cleaned)
    return output_path

'''
def enhance_document(input_path, output_path):
    img = cv2.imread(input_path)

    # Convert to gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # -------------------------------------------------
    # 1. REMOVE SHADOWS (CamScanner style)
    # -------------------------------------------------
    dilated = cv2.dilate(gray, np.ones((9, 9), np.uint8))
    bg = cv2.medianBlur(dilated, 25)
    no_shadow = 255 - cv2.absdiff(gray, bg)

    # -------------------------------------------------
    # 2. CLAHE FOR SMOOTH, CLEAN, READABLE TEXT
    # (Better than adaptive threshold for handwriting)
    # -------------------------------------------------
    clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(8,8))
    clahe_img = clahe.apply(no_shadow)

    # -------------------------------------------------
    # 3. Gentle smoothing (remove dots/noise)
    # -------------------------------------------------
    smooth = cv2.bilateralFilter(clahe_img, d=7, sigmaColor=50, sigmaSpace=50)

    # -------------------------------------------------
    # 4. Light threshold to make white background cleaner
    # -------------------------------------------------
    _, cleaned = cv2.threshold(smooth, 0, 255,
                               cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    cv2.imwrite(output_path, cleaned)
    return output_path

'''