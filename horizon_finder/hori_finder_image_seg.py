import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt

output_file_name_prefix = "imgseg_C_"

test_landscape_image = "./test_images/pexels-bri-schneiter-28802-346529.jpg"

# Image Segmentation: https://docs.opencv.org/4.x/d3/db4/tutorial_py_watershed.html

# Image Segmentation test:
img = cv.imread(test_landscape_image)
assert img is not None, "file could not be read, check with os.path.exists()"
gray = cv.cvtColor(img,cv.COLOR_BGR2GRAY)
ret, thresh = cv.threshold(gray,0,255,cv.THRESH_BINARY_INV+cv.THRESH_OTSU)
plt.imshow(thresh,cmap = 'gray')
#plt.xticks([]), plt.yticks([])
plt.savefig(output_file_name_prefix + "image_seg_test.jpg")