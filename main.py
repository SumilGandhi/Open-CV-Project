# main.py
import cv2
import numpy as np
import os
import time
from HandTrackingModule import HandDetector

# Load header images
folderPath = "header"
overlayList = []
for img in os.listdir(folderPath):
    if img.endswith(('.png', '.jpg', '.jpeg')):  # Only load image files
        loaded_img = cv2.imread(f'{folderPath}/{img}')
        if loaded_img is not None:
            # Resize to fit the header area (125 height, 1280 width)
            resized_img = cv2.resize(loaded_img, (1280, 125))
            overlayList.append(resized_img)

header = overlayList[0] if overlayList else np.zeros((125, 1280, 3), np.uint8)  # Default header

# Brush settings
drawColor = (255, 0, 255)  # Purple
brushThickness = 15
eraserThickness = 50

xp, yp = 0, 0  # Previous points
imgCanvas = np.zeros((720, 1280, 3), np.uint8)

cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

detector = HandDetector(detectionCon=0.85)

while True:
    # Capture frame
    success, img = cap.read()
    img = cv2.flip(img, 1)
    img = detector.findHands(img)
    lmList = detector.findPosition(img)

    if lmList:
        x1, y1 = lmList[8][1:]  # Index finger
        x2, y2 = lmList[12][1:]  # Middle finger

        # Check which fingers are up
        fingers = []
        for tip in [8, 12, 16, 20]:
            fingers.append(1 if lmList[tip][2] < lmList[tip - 2][2] else 0)
        
        # Clear canvas - All fingers up
        if all(fingers):
            imgCanvas = np.zeros((720, 1280, 3), np.uint8)
            xp, yp = 0, 0

        # Selection Mode – 2 fingers up
        if fingers[1] and fingers[2]:
            xp, yp = 0, 0
            cv2.rectangle(img, (x1, y1 - 25), (x2, y2 + 25), drawColor, cv2.FILLED)
            if y1 < 125:
                if 200 < x1 < 350:  # Purple
                    drawColor = (255, 0, 255)
                    header = overlayList[0] if len(overlayList) > 0 else header
                elif 400 < x1 < 550:  # Blue
                    drawColor = (255, 0, 0)
                    header = overlayList[1] if len(overlayList) > 1 else header
                elif 600 < x1 < 750:  # Green
                    drawColor = (0, 255, 0)
                    header = overlayList[2] if len(overlayList) > 2 else header
                elif 800 < x1 < 950:  # Red
                    drawColor = (0, 0, 255)
                    header = overlayList[3] if len(overlayList) > 3 else header
                elif 1000 < x1 < 1150:  # Yellow
                    drawColor = (0, 255, 255)
                    header = overlayList[4] if len(overlayList) > 4 else header
                elif 1200 < x1 < 1280:  # Eraser
                    drawColor = (0, 0, 0)
                    header = overlayList[5] if len(overlayList) > 5 else header

        # Drawing Mode – Index finger up
        if fingers[1] and not fingers[2]:
            cv2.circle(img, (x1, y1), 15, drawColor, cv2.FILLED)
            if xp == 0 and yp == 0:
                xp, yp = x1, y1

            if drawColor == (0, 0, 0):
                cv2.line(img, (xp, yp), (x1, y1), drawColor, eraserThickness)
                cv2.line(imgCanvas, (xp, yp), (x1, y1), drawColor, eraserThickness)
            else:
                cv2.line(img, (xp, yp), (x1, y1), drawColor, brushThickness)
                cv2.line(imgCanvas, (xp, yp), (x1, y1), drawColor, brushThickness)

            xp, yp = x1, y1

    # Combine canvas with webcam feed
    imgGray = cv2.cvtColor(imgCanvas, cv2.COLOR_BGR2GRAY)
    _, imgInv = cv2.threshold(imgGray, 20, 255, cv2.THRESH_BINARY_INV)
    imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
    img = cv2.bitwise_and(img, imgInv)
    img = cv2.bitwise_or(img, imgCanvas)

    # Display header
    img[0:125, 0:1280] = header

    cv2.imshow("Virtual Painter", img)
    if cv2.waitKey(1) == ord('q'):
        break

#rwah