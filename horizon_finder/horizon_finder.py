"""Horizon detection logic.

This module contains the `HorizonFinder` which detects a single horizon-like line
from images or frames. The algorithm:
- Runs Canny edge detection (parameters configurable)
- For each image column, searches near the previous detected y-position to find
  the nearest edge, constrained by a maximum jump threshold

Coordinate convention for outputs:
- Returned line is a list of heights measured from the BOTTOM of the image
  (i.e., height in pixels, not y from the top). A value of -1 means unknown.
"""

import numpy as np
import cv2 as cv

class HorizonFinder:
    """Finds a horizon line in an image or numpy array.

    The detection is intentionally simple and fast for real-time use. It depends
    on edge detection and a per-column nearest-edge search with a configurable
    maximum jump constraint to maintain continuity and reject spurious edges.
    """

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
        """Run Canny edge detection on an image file path.

        Returns a single-channel binary edge map (uint8). Uses current
        `canny_edge_params`, including aperture size and L2 gradient.
        """
        img = cv.imread(file_path, cv.IMREAD_GRAYSCALE)
        assert img is not None, "file could not be read, check with os.path.exists()"
        edges = cv.Canny(
            img,
            self.canny_edge_params["threshold1"],
            self.canny_edge_params["threshold2"],
            apertureSize=int(self.canny_edge_params.get("apertureSize", 3)),
            L2gradient=bool(self.canny_edge_params.get("L2gradient", False)),
        )
        return edges
    
    def _get_canny_edges_from_array(self, img_array: np.ndarray) -> np.ndarray:
        """Get Canny edges directly from an RGB or grayscale numpy array.

        Accepts RGB arrays and converts to grayscale as needed. Optimized for
        real-time frame processing where avoiding I/O is important.
        """
        if len(img_array.shape) == 3:
            # Convert to grayscale if it's a color image
            img_gray = cv.cvtColor(img_array, cv.COLOR_RGB2GRAY)
        else:
            img_gray = img_array
        
        edges = cv.Canny(
            img_gray,
            self.canny_edge_params["threshold1"],
            self.canny_edge_params["threshold2"],
            apertureSize=int(self.canny_edge_params.get("apertureSize", 3)),
            L2gradient=bool(self.canny_edge_params.get("L2gradient", False)),
        )
        return edges

    def find_horizon_line(self, file_path: str) -> list[int]:
        """Detect a horizon line from an image file path.

        Returns a list of length equal to image width, where each entry is the
        detected horizon height measured from the bottom. -1 indicates unknown.
        """
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
        """Detect a horizon line from an in-memory RGB or grayscale array.

        Optimized for video frames. Output format is identical to
        `find_horizon_line`.
        """
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
        """Update detection parameters from a settings dictionary.

        Expected structure:
        {
            "canny_edge_params": {"threshold1", "threshold2", "apertureSize", "L2gradient"},
            "horizon_line_params": {"line_jump_threshold"}
        }
        """
        if "canny_edge_params" in settings:
            self.canny_edge_params.update(settings["canny_edge_params"])
        
        if "horizon_line_params" in settings:
            self.horizon_line_params.update(settings["horizon_line_params"])
    
    def get_current_parameters(self) -> dict:
        """Return a copy of current parameters for UI display or export."""
        return {
            "canny_edge_params": self.canny_edge_params.copy(),
            "horizon_line_params": self.horizon_line_params.copy()
        }
