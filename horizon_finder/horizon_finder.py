import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import csv

class HorizonFinder:
    def __init__(self):
        self.canny_edge_params = {
            "threshold1": 100,
            "threshold2": 200,
            "apertureSize": 3,
            "L2gradient": False,
        }
        self.horizon_line_params = {
            "line_jump_threshold": 15,
        }

    def _get_canny_edges(self, file_path: str) -> np.ndarray:
        img = cv.imread(file_path, cv.IMREAD_GRAYSCALE)
        assert img is not None, "file could not be read, check with os.path.exists()"
        edges = cv.Canny(   img,   
                            self.canny_edge_params["threshold1"],
                            self.canny_edge_params["threshold2"],
                        )
        return edges
    
    def _get_canny_edges_from_array(self, img_array: np.ndarray) -> np.ndarray:
        """Get Canny edges directly from numpy array (optimized for video processing)"""
        if len(img_array.shape) == 3:
            # Convert to grayscale if it's a color image
            img_gray = cv.cvtColor(img_array, cv.COLOR_RGB2GRAY)
        else:
            img_gray = img_array
        
        edges = cv.Canny(img_gray,   
                        self.canny_edge_params["threshold1"],
                        self.canny_edge_params["threshold2"]
                        )
        return edges

    def find_horizon_line(self, file_path: str) -> list[int]:
        # get the index of the highest non zero value in each column
        edges = self._get_canny_edges(file_path)
        height = len(edges)
        width = len(edges[0])
        horizon_line = [-1 for _ in range (0, width)]
        #horizon_line_deltas = [-1 for _ in range (0, width)]

        line_jump_thres = self.horizon_line_params["line_jump_threshold"]

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

            # compare deltas, pick closer line
            if (up_height == -1 and down_height == -1):
                # didn't find any edge
                # add the previous value
                horizon_line[col] = prev_hori_pixel
            # only found an edge below
            elif (up_height != -1 and down_height == -1):
                if (abs(prev_hori_pixel-up_height) <= line_jump_thres):
                    horizon_line[col] = up_height
                    prev_hori_pixel = up_height
                else:
                    # didn't find a close enough edge
                    # add the previous value
                    horizon_line[col] = prev_hori_pixel
            # only found an edge above
            elif (up_height == -1 and down_height != -1):
                if (abs(prev_hori_pixel-down_height) <= line_jump_thres):
                    horizon_line[col] = down_height
                    prev_hori_pixel = down_height
                else:
                    # didn't find a close enough edge
                    # add the previous value
                    horizon_line[col] = prev_hori_pixel
            # found an edges above and below
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

        return horizon_line
    
    def find_horizon_line_from_array(self, img_array: np.ndarray) -> list[int]:
        """Find horizon line directly from numpy array (optimized for video processing)"""
        # get the index of the highest non zero value in each column
        edges = self._get_canny_edges_from_array(img_array)
        height = len(edges)
        width = len(edges[0])
        horizon_line = [-1 for _ in range(0, width)]

        line_jump_thres = self.horizon_line_params["line_jump_threshold"]

        prev_hori_pixel = -1
        for col in range(0, width):
            # pick highest line if first col
            if prev_hori_pixel == -1:
                for i in range(0, height):
                    curr_height = height - i
                    pixel = edges[i][col]
                    if pixel != 0:  # there is an edge
                        horizon_line[col] = curr_height
                        prev_hori_pixel = curr_height
                        break

            up_height = -1
            # search up from previous line
            for i in range(0, height-prev_hori_pixel):
                curr_height = prev_hori_pixel + i
                pixel = edges[height-prev_hori_pixel-i][col]
                if pixel != 0:  # there is an edge
                    up_height = curr_height
                    break
            down_height = -1
            # search down from previous line
            for i in range(0, prev_hori_pixel):
                curr_height = prev_hori_pixel - i
                pixel = edges[height-prev_hori_pixel+i][col]
                if pixel != 0:  # there is an edge
                    down_height = curr_height
                    break

            # compare deltas, pick closer line
            if (up_height == -1 and down_height == -1):
                # didn't find any edge
                # add the previous value
                horizon_line[col] = prev_hori_pixel
            # only found an edge below
            elif (up_height != -1 and down_height == -1):
                if (abs(prev_hori_pixel-up_height) <= line_jump_thres):
                    horizon_line[col] = up_height
                    prev_hori_pixel = up_height
                else:
                    # didn't find a close enough edge
                    # add the previous value
                    horizon_line[col] = prev_hori_pixel
            # only found an edge above
            elif (up_height == -1 and down_height != -1):
                if (abs(prev_hori_pixel-down_height) <= line_jump_thres):
                    horizon_line[col] = down_height
                    prev_hori_pixel = down_height
                else:
                    # didn't find a close enough edge
                    # add the previous value
                    horizon_line[col] = prev_hori_pixel
            # found an edges above and below
            else:  #(up_height != -1 and down_height != -1):
                # up_height is closer
                if (abs(prev_hori_pixel-up_height) <= abs(prev_hori_pixel-down_height)):
                    if (abs(prev_hori_pixel-up_height) <= line_jump_thres):
                        horizon_line[col] = up_height
                        prev_hori_pixel = up_height
                    else:
                        # didn't find a close enough edge
                        # add the previous value
                        horizon_line[col] = prev_hori_pixel
                else:  # down_height is closer
                    if (abs(prev_hori_pixel-down_height) <= line_jump_thres):
                        horizon_line[col] = down_height
                        prev_hori_pixel = down_height
                    else:
                        # didn't find a close enough edge
                        # add the previous value
                        horizon_line[col] = prev_hori_pixel

        return horizon_line
    
    def update_parameters(self, settings: dict) -> None:
        """Update horizon finder parameters from settings dictionary"""
        if "canny_edge_params" in settings:
            self.canny_edge_params.update(settings["canny_edge_params"])
        
        if "horizon_line_params" in settings:
            self.horizon_line_params.update(settings["horizon_line_params"])
    
    def get_current_parameters(self) -> dict:
        """Get current parameters as dictionary"""
        return {
            "canny_edge_params": self.canny_edge_params.copy(),
            "horizon_line_params": self.horizon_line_params.copy()
        }
