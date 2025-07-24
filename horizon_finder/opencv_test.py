import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt

test_landscape_image = 'road_asphalt_highway_mountain_tree-61355.jpg'

# Lots of image processing tools that may apply:
# https://docs.opencv.org/4.x/d2/d96/tutorial_py_table_of_contents_imgproc.html

#   Canny Edge: https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html
#   Image Segmentation: https://docs.opencv.org/4.x/d3/db4/tutorial_py_watershed.html
#   Hough Line: https://docs.opencv.org/4.x/d6/d10/tutorial_py_houghlines.html

# Depth Map: https://docs.opencv.org/4.x/dd/d53/tutorial_py_depthmap.html

# Video tools: https://docs.opencv.org/4.x/d3/dd5/tutorial_table_of_content_other.html


# Canny Edge Test
img = cv.imread(test_landscape_image, cv.IMREAD_GRAYSCALE)
assert img is not None, "file could not be read, check with os.path.exists()"
edges = cv.Canny(img,100,200)
plt.imshow(edges,cmap = 'gray')
#plt.xticks([]), plt.yticks([])
plt.savefig("canny_edge_test.jpg")

# Image Segmentation test:
img = cv.imread(test_landscape_image)
assert img is not None, "file could not be read, check with os.path.exists()"
gray = cv.cvtColor(img,cv.COLOR_BGR2GRAY)
ret, thresh = cv.threshold(gray,0,255,cv.THRESH_BINARY_INV+cv.THRESH_OTSU)
plt.imshow(thresh,cmap = 'gray')
#plt.xticks([]), plt.yticks([])
plt.savefig("image_seg_test.jpg")

# Hough Line Test
img = cv.imread(test_landscape_image)
gray = cv.cvtColor(img,cv.COLOR_BGR2GRAY)
edges = cv.Canny(gray,50,150,apertureSize = 3)
lines = cv.HoughLinesP(edges,1,np.pi/180,100,minLineLength=100,maxLineGap=10)
for line in lines:
    x1,y1,x2,y2 = line[0]
    cv.line(img,(x1,y1),(x2,y2),(0,255,0),2)
cv.imwrite('hough_lines_test.jpg',img)

# Depth Map Test (doesn't work, supposed to have stereo images)
imgL = cv.imread(test_landscape_image, cv.IMREAD_GRAYSCALE)
imgR = cv.imread(test_landscape_image, cv.IMREAD_GRAYSCALE)

stereo = cv.StereoBM.create(numDisparities=16, blockSize=15)
disparity = stereo.compute(imgL,imgR)
plt.imshow(disparity,'gray')
plt.savefig("depth_map_test.jpg")