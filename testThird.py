import cv2
import numpy as np

# 读取图像文件
img = cv2 .imread('./docs/examples/purple9.png')
# 将图像从 RGB 转换到 HSV 颜色空间
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
#设置颜色范围
lower_range = np.array([147, 111, 175])
upper_range = np.array([255, 212, 255])
# 应用颜色过滤器
mask = cv2.inRange(hsv, lower_range, upper_range)
# 执行形态学操作《可选)
kernel = np.ones((5, 5), np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
# 查找轮廓
contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
# 在原始图像上绘制轮廓
cv2.drawContours(img, contours, -1, (0, 255, 0), 3)
#显示结果
cv2.imshow('image', img)
cv2.waitKey(0)
cv2.destroyAllWindows()


