import cv2
import numpy as np
from HandTrackingModule import HandDetector


WINDOW_W, WINDOW_H = 1280, 720
HEADER_H = 125


# Color options
color_options = [
    {"name": "Purple", "bgr": (255, 0, 255)},
    {"name": "Green",  "bgr": (0, 255, 0)},
    {"name": "Red",    "bgr": (0, 0, 255)},
    {"name": "Yellow", "bgr": (0, 255, 255)},
    {"name": "Eraser", "bgr": (0, 0, 0)},
]


brushThickness = 15
eraserThickness = 50


def create_color_header(selected_idx=0):
    """Create header with color swatches programmatically"""
    header = np.ones((HEADER_H, WINDOW_W, 3), np.uint8) * 50  # Dark gray background
    
    num_colors = len(color_options)
    region_width = WINDOW_W // num_colors
    
    for i, option in enumerate(color_options):
        left = i * region_width
        right = (i + 1) * region_width
        
        # Draw color rectangle
        color = option["bgr"]
        if option["name"] == "Eraser":
            # Draw eraser as light gray with diagonal lines
            cv2.rectangle(header, (left + 10, 10), (right - 10, HEADER_H - 10), (200, 200, 200), -1)
            cv2.line(header, (left + 10, 10), (right - 10, HEADER_H - 10), (100, 100, 100), 3)
            cv2.line(header, (right - 10, 10), (left + 10, HEADER_H - 10), (100, 100, 100), 3)
        else:
            cv2.rectangle(header, (left + 10, 10), (right - 10, HEADER_H - 10), color, -1)
        
        # Add text label
        text_color = (255, 255, 255) if option["name"] != "Eraser" else (0, 0, 0)
        cv2.putText(header, option["name"], (left + 30, HEADER_H - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
        
        # Highlight selected color with a white border
        if i == selected_idx:
            cv2.rectangle(header, (left + 5, 5), (right - 5, HEADER_H - 5), (255, 255, 255), 5)
    
    return header



# Initialize camera and detector
cap = cv2.VideoCapture(0)
cap.set(3, WINDOW_W)
cap.set(4, WINDOW_H)
detector = HandDetector(detectionCon=0.85)

# Initialize drawing variables
xp, yp = 0, 0
current_color_idx = 0
drawColor = color_options[current_color_idx]["bgr"]
imgCanvas = np.zeros((WINDOW_H, WINDOW_W, 3), np.uint8)
header = create_color_header(current_color_idx)

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    img = detector.findHands(img)
    lmList = detector.findPosition(img)

    if lmList:
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]
        
        # Check which fingers are up
        fingers = []
        tip_ids = [4, 8, 12, 16, 20]
        # Thumb
        if lmList[tip_ids[0]][1] > lmList[tip_ids[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
        # 4 Fingers
        for id in range(1, 5):
            if lmList[tip_ids[id]][2] < lmList[tip_ids[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        
        # Clear canvas if all 5 fingers are up
        if sum(fingers) == 5:
            imgCanvas = np.zeros((WINDOW_H, WINDOW_W, 3), np.uint8)
            xp, yp = 0, 0
        
        # Selection Mode: Index and Middle fingers are up
        if fingers[1] and fingers[2] and not fingers[3]:
            xp, yp = 0, 0
            cv2.rectangle(img, (x1, y1-25), (x2, y2+25), drawColor, cv2.FILLED)
            if y1 < HEADER_H:
                region_width = WINDOW_W // len(color_options)
                for i, option in enumerate(color_options):
                    left = i * region_width
                    right = left + region_width
                    if left < x1 < right:
                        current_color_idx = i
                        drawColor = option["bgr"]
                        header = create_color_header(current_color_idx)
                        break
        
        # Drawing Mode: Only Index finger is up
        elif fingers[1] and not fingers[2]:
            cv2.circle(img, (x1, y1), 15, drawColor, cv2.FILLED)
            if xp == 0 and yp == 0:
                xp, yp = x1, y1
            thickness = eraserThickness if drawColor == (0,0,0) else brushThickness
            cv2.line(img, (xp, yp), (x1, y1), drawColor, thickness)
            cv2.line(imgCanvas, (xp, yp), (x1, y1), drawColor, thickness)
            xp, yp = x1, y1

    # Combine canvas with webcam feed
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
