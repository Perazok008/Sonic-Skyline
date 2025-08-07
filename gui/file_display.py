"""Display utilities for images and videos.

This module centralizes rendering of images and videos into a Qt `QLabel`.
It also integrates real-time horizon detection for videos with lightweight
performance optimizations:
- Processes only every Nth frame and caches the last computed horizon line
- Caps render FPS to reduce CPU/GPU usage

Coordinate convention:
- The horizon line values are heights from the bottom of the frame. This
  function converts to OpenCV's y-from-top coordinate when drawing.
"""
import os
import numpy as np
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage
from core.constants import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, CONTENT_FONT
import cv2 as cv

class FileDisplayManager:
    """Manages rendering of images/videos and overlaying the horizon line.

    Static methods are used to keep integration simple from the main window.
    Video playback state is stored as class-level attributes and is torn down
    when a new file is displayed or the window closes.
    """
    
    # Class variables for video playback
    _video_capture = None
    _video_timer = None
    _current_content_area = None
    _current_horizon_finder = None
    _show_horizon = True
    _show_image = True
    _show_axis = False
    
    # Performance optimization variables
    _frame_count = 0
    _cached_horizon_line = None
    _process_every_n_frames = 10  # Process horizon detection every 10th frame (adjustable for performance)
    _max_fps = 25  # Cap at 25 FPS for smooth performance (adjustable for performance)
    
    @classmethod
    def set_performance_settings(cls, process_every_n_frames: int = 5, max_fps: int = 20) -> None:
        """Adjust performance settings for video processing"""
        cls._process_every_n_frames = max(1, process_every_n_frames)  # Minimum 1
        cls._max_fps = max(5, min(60, max_fps))  # Between 5 and 60 FPS

    @staticmethod
    def display_file(content_area: QLabel, file_path: str, horizon_line: list[int] | None, 
                    show_image: bool = True, show_horizon: bool = True, show_axis: bool = False, 
                    horizon_finder=None) -> None:
        """Display an image or play a video with optional overlays.

        For images, draws the provided `horizon_line` immediately. For videos,
        starts a timer to read frames and compute/draw the horizon periodically.
        """
        
        # Stop any existing video playback
        FileDisplayManager._stop_video()

        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension in IMAGE_EXTENSIONS:
            frame = FileDisplayManager._render_frame(file_path, horizon_line, show_image, show_horizon, show_axis)
            pixmap = FileDisplayManager._np_to_qpixmap(frame)
            scaled_pixmap = pixmap.scaled(
                content_area.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            content_area.setPixmap(scaled_pixmap)
        elif file_extension in VIDEO_EXTENSIONS:
            FileDisplayManager._start_video_playback(content_area, file_path, horizon_finder, show_image, show_horizon, show_axis)
        else:
            content_area.setText(f"Unsupported file type:\n{file_extension}")
            content_area.setFont(CONTENT_FONT)

    @staticmethod
    def _render_frame(file_path: str, horizon_line: list[int] | None, 
                     show_image: bool = True, show_horizon: bool = True, show_axis: bool = False) -> np.ndarray:
        """Render a single image file to an RGB numpy array with overlays."""

        image = cv.imread(file_path)
        if image is None:
            raise FileNotFoundError(f"Could not load image: {file_path}")
        
        image_rgb = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        height, width = image_rgb.shape[:2]

        # Calculate scale factor for line thickness based on image dimensions
        # Use the smaller dimension to ensure lines are visible on both wide and tall images
        min_dimension = min(width, height)
        scale_factor = max(1, min_dimension // 500)  # Scale factor: 1 pixel per 500 pixels of image size
        
        # Calculate line thickness and radius based on scale factor
        line_thickness = max(1, scale_factor)
        circle_radius = max(1, scale_factor * 2)  # Make circles slightly larger for better visibility

        if not show_image:
            image_rgb[:] = 0  # Make black

        if show_horizon and horizon_line is not None:
            for x, height_val in enumerate(horizon_line):
                if height_val != -1:  # Skip holes/undetected areas
                    # Convert from height-based coordinates to OpenCV image coordinates
                    # The algorithm outputs height from bottom, OpenCV expects y from top
                    y = height - height_val
                    if 0 <= y < height:  # Ensure y is within image bounds
                        cv.circle(image_rgb, (x, y), radius=circle_radius, color=(255, 0, 255), thickness=-1)

        if show_axis and horizon_line is not None:
            cv.line(image_rgb, (0, height // 2), (width, height // 2), color=(255, 255, 255), thickness=line_thickness)

        return image_rgb

    @staticmethod
    def _np_to_qpixmap(np_img: np.ndarray) -> QPixmap:
        h, w, ch = np_img.shape
        bytes_per_line = ch * w
        qimg = QImage(np_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimg)
    
    @staticmethod
    def _start_video_playback(content_area: QLabel, file_path: str, horizon_finder, 
                             show_image: bool = True, show_horizon: bool = True, show_axis: bool = False) -> None:
        """Begin reading frames and scheduling horizon detection for a video."""
        
        # Initialize video capture
        FileDisplayManager._video_capture = cv.VideoCapture(file_path)
        if not FileDisplayManager._video_capture.isOpened():
            content_area.setText(f"Could not open video:\n{file_path}")
            content_area.setFont(CONTENT_FONT)
            return
        
        # Store current settings
        FileDisplayManager._current_content_area = content_area
        FileDisplayManager._current_horizon_finder = horizon_finder
        FileDisplayManager._show_horizon = show_horizon
        FileDisplayManager._show_image = show_image
        FileDisplayManager._show_axis = show_axis
        
        # Reset performance variables
        FileDisplayManager._frame_count = 0
        FileDisplayManager._cached_horizon_line = None
        
        # Use optimized FPS (capped at max_fps for performance)
        fps = min(FileDisplayManager._max_fps, 
                 FileDisplayManager._video_capture.get(cv.CAP_PROP_FPS) or 20)
        
        # Create and start timer for frame updates
        FileDisplayManager._video_timer = QTimer()
        FileDisplayManager._video_timer.timeout.connect(FileDisplayManager._update_video_frame)
        FileDisplayManager._video_timer.start(int(1000 / fps))  # Convert FPS to milliseconds
    
    @staticmethod
    def _update_video_frame() -> None:
        """Read next frame, optionally update horizon, render, and display."""
        if FileDisplayManager._video_capture is None:
            return
        
        ret, frame = FileDisplayManager._video_capture.read()
        if not ret:
            # End of video, restart from beginning
            FileDisplayManager._video_capture.set(cv.CAP_PROP_POS_FRAMES, 0)
            FileDisplayManager._frame_count = 0
            FileDisplayManager._cached_horizon_line = None
            return
        
        # Convert frame to RGB
        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        
        # Optimized horizon detection with frame skipping
        horizon_line = None
        if (FileDisplayManager._current_horizon_finder is not None and 
            FileDisplayManager._show_horizon):
            
            # Only process horizon detection every N frames for performance
            if FileDisplayManager._frame_count % FileDisplayManager._process_every_n_frames == 0:
                try:
                    # Use optimized direct array processing (no file I/O!)
                    horizon_line = FileDisplayManager._current_horizon_finder.find_horizon_line_from_array(frame_rgb)
                    FileDisplayManager._cached_horizon_line = horizon_line
                except Exception:
                    # If horizon detection fails, use cached result or None
                    horizon_line = FileDisplayManager._cached_horizon_line
            else:
                # Use cached horizon line for intermediate frames
                horizon_line = FileDisplayManager._cached_horizon_line
        
        # Increment frame counter
        FileDisplayManager._frame_count += 1
        
        # Render frame with horizon line using existing logic
        processed_frame = FileDisplayManager._render_frame_from_array(
            frame_rgb, horizon_line, 
            FileDisplayManager._show_image, 
            FileDisplayManager._show_horizon, 
            FileDisplayManager._show_axis
        )
        
        # Display frame
        pixmap = FileDisplayManager._np_to_qpixmap(processed_frame)
        scaled_pixmap = pixmap.scaled(
            FileDisplayManager._current_content_area.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        FileDisplayManager._current_content_area.setPixmap(scaled_pixmap)
    
    @staticmethod
    def _render_frame_from_array(image_rgb: np.ndarray, horizon_line: list[int] | None, 
                                show_image: bool = True, show_horizon: bool = True, show_axis: bool = False) -> np.ndarray:
        """Render a numpy array frame with optional horizon/axis overlays."""
        
        height, width = image_rgb.shape[:2]

        # Calculate scale factor for line thickness based on image dimensions
        min_dimension = min(width, height)
        scale_factor = max(1, min_dimension // 500)
        
        # Calculate line thickness and radius based on scale factor
        line_thickness = max(1, scale_factor)
        circle_radius = max(1, scale_factor * 2)

        if not show_image:
            image_rgb[:] = 0  # Make black

        if show_horizon and horizon_line is not None:
            for x, height_val in enumerate(horizon_line):
                if height_val != -1 and x < width:  # Skip holes/undetected areas and bounds check
                    # Convert from height-based coordinates to OpenCV image coordinates
                    y = height - height_val
                    if 0 <= y < height:  # Ensure y is within image bounds
                        cv.circle(image_rgb, (x, y), radius=circle_radius, color=(255, 0, 255), thickness=-1)

        if show_axis and horizon_line is not None:
            cv.line(image_rgb, (0, height // 2), (width, height // 2), color=(255, 255, 255), thickness=line_thickness)

        return image_rgb
    
    @staticmethod
    def _stop_video() -> None:
        """Stop video playback and release timers and capture handles."""
        if FileDisplayManager._video_timer is not None:
            FileDisplayManager._video_timer.stop()
            FileDisplayManager._video_timer = None
        
        if FileDisplayManager._video_capture is not None:
            FileDisplayManager._video_capture.release()
            FileDisplayManager._video_capture = None
        
        # Reset all variables
        FileDisplayManager._current_content_area = None
        FileDisplayManager._current_horizon_finder = None
        FileDisplayManager._frame_count = 0
        FileDisplayManager._cached_horizon_line = None
    
    @staticmethod
    def update_video_display_settings(show_image: bool = True, show_horizon: bool = True, show_axis: bool = False) -> None:
        """Update visibility toggles during video playback without restarting."""
        if FileDisplayManager._video_capture is not None:
            FileDisplayManager._show_image = show_image
            FileDisplayManager._show_horizon = show_horizon
            FileDisplayManager._show_axis = show_axis
