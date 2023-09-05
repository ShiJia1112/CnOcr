
import cv2
import numpy as np

# 定义颜色范围（以HSV颜色空间为例）
color_lower = np.array([255, 208, 255])
color_upper = np.array([138, 106, 169])

# 读取图像
image = cv2.imread("./docs/examples/purple9.png")

# 转换颜色空间为HSV
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# 根据颜色范围创建掩膜
mask = cv2.inRange(hsv, color_lower, color_upper)

# 进行形态学操作，如开运算和闭运算
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)


# 查找轮廓
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 遍历轮廓并绘制边界框
for contour in contours:
    area = cv2.contourArea(contour)
    if area > 100:  # 可根据实际情况调整阈值
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

# 显示结果
cv2.imshow("Result", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
