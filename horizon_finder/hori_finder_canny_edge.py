import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt

output_file_name_prefix = "H_"

test_landscape_image = "mountains-fjord_G4EWW6PIHV.jpg"
#'road_asphalt_highway_mountain_tree-61355.jpg'

# Canny Edge: https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html

# Canny Edge Test
img = cv.imread(test_landscape_image, cv.IMREAD_GRAYSCALE)
assert img is not None, "file could not be read, check with os.path.exists()"
edges = cv.Canny(img,100,200)

# get the index of the highest non zero value in each column
height = len(edges)
width = len(edges[0])
horizon_line = [-1 for _ in range (0, width)]

line_jump_thres = 50

prev_hori_pixel = -1
for col in range(0, width):
    for i in range(0, height):
        curr_height = height - i
        pixel = edges[i][col]
        print(str(curr_height) + ", " + str(col) + " " + str(pixel))
        if pixel != 0: # there is an edge
            # determine if this point is close enough to prev edge
            if prev_hori_pixel > -1:
                diff = abs(prev_hori_pixel - curr_height)
                print(str(curr_height) + " " + str(diff))
                if (diff > line_jump_thres):
                    print(str(curr_height) + " " + str(diff))
                    continue
            horizon_line[col] = curr_height
            prev_hori_pixel = curr_height
            print(edges.shape)
            break # look at next column

x = [i for i in range (1, width+1)]
y = horizon_line

# just conney edge
plt.imshow(edges,cmap = 'gray')
#plt.xticks([]), plt.yticks([])
plt.title("Canny Edge")

plt.savefig(output_file_name_prefix + "canny_edge.jpg")


# overlay
plt.clf()
overlay_y = [-1*val + height for val in horizon_line]

plt.imshow(edges,cmap = 'gray')
#plt.xticks([]), plt.yticks([])
plt.plot(x, overlay_y, color='pink', linewidth=2)  # Plot points connected by line, markers on points
plt.title("Canny Edge Overlay")

plt.savefig(output_file_name_prefix + "canny_edge_overlay.jpg")

# graph
plt.clf()
plt.plot(x, y, color='blue', lw=2)  # Plot points connected by line, markers on points
plt.title("Canny Edge XY Plot")
plt.xlim(0, width)
plt.ylim(0, height)

plt.savefig(output_file_name_prefix + "canny_edge_xy_plot.jpg")

# Saving horizon data as csv file
import csv

with open (output_file_name_prefix + "canny_edge_horiz_data.csv", "w+") as file:
    writer = csv.writer(file)
    print(horizon_line)
    for val in horizon_line:
        writer.writerow([val])