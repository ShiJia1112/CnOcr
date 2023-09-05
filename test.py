import cv2
import numpy as np

cap = cv2.VideoCapture(0)
red_min = np.array([0, 128, 46])
red_max = np.array([5, 255, 255])
red2_min = np.array([156, 128, 46])
red2_max = np.array([180, 255, 255])
yellow_min = np.array([15, 128, 46])
yellow_max = np.array([50, 255, 255])

while True:
    ret, frame = cap.read()
    x, y = frame.shape[0:2]
    small_frame = cv2.resize(frame, (int(y / 2), int(x / 2)))
    cv2.imshow('small', small_frame)

    src = small_frame.copy()
    res = src.copy()
    hsv = cv2.cvtColor(src, cv2.COLOR_BGR2HSV)
    mask_red1 = cv2.inRange(hsv, red_min, red_max)
    mask_red2 = cv2.inRange(hsv, red2_min, red2_max)
    mask_yellow = cv2.inRange(hsv, yellow_min, yellow_max)
    mask = cv2.bitwise_or(mask_red1, mask_red2)
    mask = cv2.bitwise_or(mask, mask_yellow)
    res = cv2.bitwise_and(src, src, mask=mask)
    h, w = res.shape[:2]
    blured = cv2.blur(res, (5, 5))
    ret, bright = cv2.threshold(blured, 10, 255, cv2.THRESH_BINARY)
    gray = cv2.cvtColor(bright, cv2.COLOR_BGR2GRAY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    opened = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
    contours, hierarchy = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(src, contours, -1, (255, 0, 0), 2)
    cv2.imsow("result", src)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
