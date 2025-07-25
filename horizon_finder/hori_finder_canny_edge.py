import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt

test_landscape_image = 'road_asphalt_highway_mountain_tree-61355.jpg'

# Canny Edge: https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html

# Canny Edge Test
img = cv.imread(test_landscape_image, cv.IMREAD_GRAYSCALE)
assert img is not None, "file could not be read, check with os.path.exists()"
edges = cv.Canny(img,100,200)

# get the index of the highest non zero value in each column
height = len(edges)
width = len(edges[0])
horizon_line = [-1 for _ in range (0, width)]

for i, row in enumerate(edges):
    curr_height = height - i # count down from top
    for j, pixel in enumerate(row):
        if horizon_line[j] == -1 and pixel != 0:
            horizon_line[j] = curr_height

x = [i for i in range (1, width+1)]
y = horizon_line


# overlay
overlay_y = [-1*val + height for val in horizon_line]

plt.imshow(edges,cmap = 'gray')
#plt.xticks([]), plt.yticks([])
plt.plot(x, overlay_y, color='pink', linewidth=2)  # Plot points connected by line, markers on points
plt.title("Canny Edge Overlay")

plt.savefig("canny_edge_overlay.jpg")

# graph
plt.clf()

plt.plot(x, y, color='blue', lw=2)  # Plot points connected by line, markers on points
plt.title("Canny Edge XY Plot")
plt.xlim(0, width)
plt.ylim(0, height)

plt.savefig("canny_edge_xy_plot.jpg")

# Saving horizon data as csv file
import csv

with open ("canny_edge_horiz_data.csv", "w+") as file:
    writer = csv.writer(file)
    print(horizon_line)
    for val in horizon_line:
        writer.writerow([val])