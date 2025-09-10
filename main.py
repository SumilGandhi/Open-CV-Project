import cv2
import numpy as np
import os
import time
from HandTrackingModule import HandDetector
from skimage.metrics import structural_similarity as ssim  # pip install scikit-image


WINDOW_W, WINDOW_H = 1280, 720
HEADER_H = 125
REF_IMG_H = 300


# Color and header images
color_options = [
    {"name": "Purple", "bgr": (255, 0, 255)},
    {"name": "Blue",   "bgr": (255, 0, 0)},
    {"name": "Green",  "bgr": (0, 255, 0)},
    {"name": "Red",    "bgr": (0, 0, 255)},
    {"name": "Yellow", "bgr": (0, 255, 255)},
    {"name": "Eraser", "bgr": (0, 0, 0)},
]


brushThickness = 15
eraserThickness = 50


folderPath = "header"
overlayList = []
header_files = ["purple.png", "blue.png", "green.png", "red.png", "yellow.png", "eraser.png"]
for fname in header_files:
    img_path = os.path.join(folderPath, fname)
    if os.path.exists(img_path):
        loaded_img = cv2.imread(img_path)
        resized_img = cv2.resize(loaded_img, (WINDOW_W, HEADER_H))
        overlayList.append(resized_img)
    else:
        overlayList.append(np.zeros((HEADER_H, WINDOW_W, 3), np.uint8))


header = overlayList[0] if overlayList else np.zeros((HEADER_H, WINDOW_W, 3), np.uint8)


# Reference images
ref_folder = "reference_folder"
ref_img_files = sorted([f for f in os.listdir(ref_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
reference_images = []
for f in ref_img_files:
    full_path = os.path.join(ref_folder, f)
    img = cv2.imread(full_path, cv2.IMREAD_UNCHANGED)
    if img is not None:
        scale = REF_IMG_H / img.shape[0]
        w_new = int(img.shape[1] * scale)
        img = cv2.resize(img, (w_new, REF_IMG_H))
        reference_images.append(img)
ref_img_idx = 0


def overlay_reference(frame, ref_img):
    if ref_img is None:
        return frame, {'x':0,'y':0,'w':0,'h':0}
    h_frame, w_frame = frame.shape[:2]
    h_ref, w_ref = ref_img.shape[:2]
    x_offset = w_frame - w_ref - 20
    y_offset = (h_frame // 2) - (h_ref // 2)
    if ref_img.shape[2] == 3:
        frame[y_offset:y_offset+h_ref, x_offset:x_offset+w_ref] = ref_img
    else:
        rgb = ref_img[..., :3]
        alpha = ref_img[..., 3:] / 255.0
        alpha = np.repeat(alpha, 3, axis=2)
        roi = frame[y_offset:y_offset+h_ref, x_offset:x_offset+w_ref]
        roi[:] = (roi * (1 - alpha) + rgb * alpha).astype(np.uint8)
    ref_area = {'x': x_offset, 'y': y_offset, 'w': w_ref, 'h': h_ref}
    return frame, ref_area


def check_similarity(imgCanvas, ref_img, ref_area):
    if ref_img is None or ref_area['w'] == 0 or ref_area['h'] == 0:
        return False
    x, y, w, h = ref_area['x'], ref_area['y'], ref_area['w'], ref_area['h']
    drawn_crop = imgCanvas[y:y+h, x:x+w]
    if drawn_crop.shape[0] == 0 or drawn_crop.shape[1] == 0:
        return False
    ref_gray = cv2.cvtColor(ref_img[..., :3], cv2.COLOR_BGR2GRAY)
    drawn_gray = cv2.cvtColor(drawn_crop, cv2.COLOR_BGR2GRAY)
    if drawn_gray.shape != ref_gray.shape:
        drawn_gray = cv2.resize(drawn_gray, ref_gray.shape[::-1])
    score = ssim(ref_gray, drawn_gray)
    return score > 0.4  # Adjust threshold as per similarity needs


cap = cv2.VideoCapture(0)
cap.set(3, WINDOW_W)
cap.set(4, WINDOW_H)
detector = HandDetector(detectionCon=0.85)


xp, yp = 0, 0
drawColor = color_options[0]["bgr"]
imgCanvas = np.zeros((WINDOW_H, WINDOW_W, 3), np.uint8)


while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    img = detector.findHands(img)
    lmList = detector.findPosition(img)


    current_reference_img = reference_images[ref_img_idx] if reference_images else None
    img, ref_area = overlay_reference(img, current_reference_img)


    # Show tick or cross based on similarity
    is_similar = check_similarity(imgCanvas, current_reference_img, ref_area)
    feedback_pos = (ref_area['x'] + ref_area['w']//2 - 40, ref_area['y'] + 40)
    if is_similar:
        cv2.putText(img, "O", feedback_pos, cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 6)
    else:
        cv2.putText(img, "X", feedback_pos, cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 6)


    if lmList:
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]
        fingers = []
        for tip in [8, 12, 16, 20]:
            fingers.append(1 if lmList[tip][2] < lmList[tip - 2][2] else 0)
        if all(fingers):
            imgCanvas = np.zeros((WINDOW_H, WINDOW_W, 3), np.uint8)
            xp, yp = 0, 0
        if fingers[1] and fingers[2]:
            xp, yp = 0, 0
            cv2.rectangle(img, (x1, y1-25), (x2, y2+25), drawColor, cv2.FILLED)
            if y1 < HEADER_H:
                region_width = WINDOW_W // len(color_options)
                for i, option in enumerate(color_options):
                    left = i * region_width
                    right = left + region_width
                    if left < x1 < right:
                        drawColor = option["bgr"]
                        header = overlayList[i]
                        break
            if (
                ref_area['x'] < x1 < ref_area['x'] + ref_area['w'] and
                ref_area['y'] < y1 < ref_area['y'] + ref_area['h']
            ):
                if x1 < ref_area['x'] + ref_area['w'] // 2:
                    ref_img_idx = (ref_img_idx - 1) % len(reference_images)
                else:
                    ref_img_idx = (ref_img_idx + 1) % len(reference_images)
                time.sleep(0.3)
        if fingers[1] and not fingers[2]:
            cv2.circle(img, (x1, y1), 15, drawColor, cv2.FILLED)
            if xp == 0 and yp == 0:
                xp, yp = x1, y1
            thickness = eraserThickness if drawColor == (0,0,0) else brushThickness
            cv2.line(img, (xp, yp), (x1, y1), drawColor, thickness)
            cv2.line(imgCanvas, (xp, yp), (x1, y1), drawColor, thickness)
            xp, yp = x1, y1


    imgGray = cv2.cvtColor(imgCanvas, cv2.COLOR_BGR2GRAY)
    _, imgInv = cv2.threshold(imgGray, 20, 255, cv2.THRESH_BINARY_INV)
    imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
    img = cv2.bitwise_and(img, imgInv)
    img = cv2.bitwise_or(img, imgCanvas)
    img[0:HEADER_H, 0:WINDOW_W] = header


    cv2.imshow("Virtual Painter", img)
    if cv2.waitKey(1) == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()
