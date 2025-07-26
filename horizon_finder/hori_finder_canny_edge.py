import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt

output_file_name_prefix = "M2_"

test_landscape_image = "landscape_with_clouds.jpg"

# Canny Edge: https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html

# Canny Edge Test
img = cv.imread(test_landscape_image, cv.IMREAD_GRAYSCALE)
assert img is not None, "file could not be read, check with os.path.exists()"
edges = cv.Canny(img,100,200)

# get the index of the highest non zero value in each column
height = len(edges)
width = len(edges[0])
horizon_line = [-1 for _ in range (0, width)]
#horizon_line_deltas = [-1 for _ in range (0, width)]

line_jump_thres = 15

prev_hori_pixel = -1
for col in range(0, width):
    # pick highest line if first col
    if prev_hori_pixel == -1:
        for i in range(0, height):
            curr_height = height - i
            pixel = edges[i][col]
            if pixel != 0: # there is an edge
                horizon_line[col] = curr_height
                prev_hori_pixel = curr_height
                break

    up_height = -1
    # search up from previous line
    for i in range(0, height-prev_hori_pixel):
        curr_height = prev_hori_pixel + i
        pixel = edges[height-prev_hori_pixel-i][col]
        if pixel != 0: # there is an edge
            up_height = curr_height
            break
    down_height = -1
    # search down from previous line
    for i in range(0, prev_hori_pixel):
        curr_height = prev_hori_pixel - i
        pixel = edges[height-prev_hori_pixel+i][col]
        if pixel != 0: # there is an edge
            down_height = curr_height
            break

    print("prev_hori_pixel: " + str(prev_hori_pixel) + ", up_height: " + str(up_height) + ", down_height: " + str(down_height))
    # compare deltas, pick closer line
    if (up_height == -1 and down_height == -1):
        # didn't find any edge
        # add the previous value
        horizon_line[col] = prev_hori_pixel
    elif (up_height != -1 and down_height == -1):
        if (abs(prev_hori_pixel-up_height) <= line_jump_thres):
            horizon_line[col] = up_height
            prev_hori_pixel = up_height
        else:
            # didn't find a close enough edge
            # add the previous value
            horizon_line[col] = prev_hori_pixel
    elif (up_height == -1 and down_height != -1):
        if (abs(prev_hori_pixel-down_height) <= line_jump_thres):
            horizon_line[col] = down_height
            prev_hori_pixel = down_height
        else:
            # didn't find a close enough edge
            # add the previous value
            horizon_line[col] = prev_hori_pixel
    else: #(up_height != -1 and down_height != -1):
        # up_height is closer
        if (abs(prev_hori_pixel-up_height) <= abs(prev_hori_pixel-down_height)):
            if (abs(prev_hori_pixel-up_height) <= line_jump_thres):
                horizon_line[col] = up_height
                prev_hori_pixel = up_height
            else:
                # didn't find a close enough edge
                # add the previous value
                horizon_line[col] = prev_hori_pixel
        else: # down_height is closer
            if (abs(prev_hori_pixel-down_height) <= line_jump_thres):
                horizon_line[col] = down_height
                prev_hori_pixel = down_height
            else:
                # didn't find a close enough edge
                # add the previous value
                horizon_line[col] = prev_hori_pixel
    

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