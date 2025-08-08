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
import time
import numpy as np
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QTimer, QObject, QEvent
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
    _last_image_pixmap: QPixmap | None = None
    _resize_filter: QObject | None = None
    _native_fps: float = 0.0
    _timer_fps: float = 0.0
    _playback_fps: float = 0.0
    _desired_processing_fps: float | None = 30.0
    _auto_processing_fps: bool = True
    _total_frames: int = 0
    _current_frame_index: int = 0
    _is_paused: bool = False
    _processed_frames_counter: int = 0
    _processed_fps: float = 0.0
    _processed_fps_window_start: float = 0.0
    _last_frame_rgb: np.ndarray | None = None
    _last_display_time: float | None = None
    
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
        # Track the current area for scaling
        FileDisplayManager._current_content_area = content_area

        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension in IMAGE_EXTENSIONS:
            frame = FileDisplayManager._render_frame(file_path, horizon_line, show_image, show_horizon, show_axis)
            pixmap = FileDisplayManager._np_to_qpixmap(frame)
            # Remember original pixmap to re-scale on future resizes
            FileDisplayManager._last_image_pixmap = pixmap
            FileDisplayManager._install_image_resize_handler(content_area)
            # Scale to fit while preserving aspect ratio; allow shrinking and expanding
            if content_area.width() > 0 and content_area.height() > 0:
                scaled_pixmap = pixmap.scaled(
                    content_area.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                content_area.setPixmap(scaled_pixmap)
            else:
                content_area.setPixmap(pixmap)
        elif file_extension in VIDEO_EXTENSIONS:
            # For video, remove any image resize handler; video frames handle scaling each tick
            FileDisplayManager._remove_image_resize_handler(content_area)
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
        FileDisplayManager._last_image_pixmap = None
        FileDisplayManager._is_paused = False
        FileDisplayManager._last_frame_rgb = None
        FileDisplayManager._last_display_time = None
        
        # Reset performance variables
        FileDisplayManager._frame_count = 0
        FileDisplayManager._cached_horizon_line = None
        FileDisplayManager._processed_frames_counter = 0
        FileDisplayManager._processed_fps = 0.0
        FileDisplayManager._processed_fps_window_start = time.time()
        
        # Gather video properties
        native_fps = FileDisplayManager._video_capture.get(cv.CAP_PROP_FPS) or 20
        total_frames = int(FileDisplayManager._video_capture.get(cv.CAP_PROP_FRAME_COUNT) or 0)
        FileDisplayManager._native_fps = float(native_fps)
        FileDisplayManager._total_frames = total_frames
        FileDisplayManager._current_frame_index = int(FileDisplayManager._video_capture.get(cv.CAP_PROP_POS_FRAMES) or 0)
        
        # Determine desired processing fps (auto default to min(native, 30))
        if FileDisplayManager._auto_processing_fps or FileDisplayManager._desired_processing_fps is None:
            FileDisplayManager._desired_processing_fps = float(native_fps)
        
        # Timer FPS is capped by both native and configured display max
        timer_fps = min(float(FileDisplayManager._max_fps), float(native_fps) if native_fps > 0 else 20.0)
        FileDisplayManager._timer_fps = timer_fps
        # Compute process-every-N such that processed fps ~= desired
        desired = max(1.0, float(FileDisplayManager._desired_processing_fps or 1.0))
        # Ensure at least one processed frame per N frames; round to keep near desired fps
        FileDisplayManager._process_every_n_frames = max(1, int(round(timer_fps / desired)))
        
        # Use optimized FPS (capped at max_fps for performance)
        fps = timer_fps
        
        # Create and start timer for frame updates (strictly honor timer fps cap)
        FileDisplayManager._video_timer = QTimer()
        FileDisplayManager._video_timer.timeout.connect(FileDisplayManager._update_video_frame)
        interval_ms = max(1, int(round(1000.0 / fps)))
        FileDisplayManager._video_timer.start(interval_ms)
    
    @staticmethod
    def _update_video_frame() -> None:
        """Read next frame, optionally update horizon, render, and display."""
        if FileDisplayManager._video_capture is None:
            return
        
        t0 = time.time()
        ret, frame = FileDisplayManager._video_capture.read()
        if not ret:
            # End of video, restart from beginning
            FileDisplayManager._video_capture.set(cv.CAP_PROP_POS_FRAMES, 0)
            FileDisplayManager._frame_count = 0
            FileDisplayManager._cached_horizon_line = None
            FileDisplayManager._current_frame_index = 0
            return
        
        # Update current frame index
        FileDisplayManager._current_frame_index = int(FileDisplayManager._video_capture.get(cv.CAP_PROP_POS_FRAMES) or 0)
        
        # Convert frame to RGB
        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        FileDisplayManager._last_frame_rgb = frame_rgb
        
        # Optimized horizon detection with frame skipping
        horizon_line = FileDisplayManager._cached_horizon_line
        if FileDisplayManager._current_horizon_finder is not None:
            
            # Only process horizon detection every N frames for performance
            if FileDisplayManager._is_paused:
                # When paused, recompute horizon for current frame only if layer is on
                if FileDisplayManager._show_horizon:
                    try:
                        horizon_line = FileDisplayManager._current_horizon_finder.find_horizon_line_from_array(frame_rgb)
                        FileDisplayManager._cached_horizon_line = horizon_line
                    except Exception:
                        horizon_line = FileDisplayManager._cached_horizon_line
            elif FileDisplayManager._show_horizon and FileDisplayManager._frame_count % FileDisplayManager._process_every_n_frames == 0:
                try:
                    # Use optimized direct array processing (no file I/O!)
                    horizon_line = FileDisplayManager._current_horizon_finder.find_horizon_line_from_array(frame_rgb)
                    FileDisplayManager._cached_horizon_line = horizon_line
                    # Count processed frames to compute effective processing FPS
                    FileDisplayManager._processed_frames_counter += 1
                    now = time.time()
                    elapsed = now - FileDisplayManager._processed_fps_window_start
                    if elapsed >= 1.0:
                        FileDisplayManager._processed_fps = FileDisplayManager._processed_frames_counter / elapsed
                        FileDisplayManager._processed_frames_counter = 0
                        FileDisplayManager._processed_fps_window_start = now
                except Exception:
                    # If horizon detection fails, use cached result or None
                    horizon_line = FileDisplayManager._cached_horizon_line
            else:
                # Use cached horizon line for intermediate frames
                horizon_line = FileDisplayManager._cached_horizon_line
        
        # Increment frame counter
        FileDisplayManager._frame_count += 1
        
        # Render frame with horizon line using existing logic (no baking of line into image rendering path)
        processed_frame = FileDisplayManager._render_frame_from_array(
            frame_rgb, horizon_line if FileDisplayManager._show_horizon else None, 
            FileDisplayManager._show_image, 
            FileDisplayManager._show_horizon, 
            FileDisplayManager._show_axis
        )
        
        # Display frame (scale to current content area size with aspect preserved)
        pixmap = FileDisplayManager._np_to_qpixmap(processed_frame)
        if (FileDisplayManager._current_content_area is not None and
            FileDisplayManager._current_content_area.width() > 0 and
            FileDisplayManager._current_content_area.height() > 0):
            scaled_pixmap = pixmap.scaled(
                FileDisplayManager._current_content_area.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            FileDisplayManager._current_content_area.setPixmap(scaled_pixmap)
        else:
            FileDisplayManager._current_content_area.setPixmap(pixmap)
        # Update playback FPS estimate based on actual frame display cadence
        now = time.time()
        if FileDisplayManager._last_display_time is not None:
            dt_disp = max(1e-6, now - FileDisplayManager._last_display_time)
            inst = 1.0 / dt_disp
            if FileDisplayManager._playback_fps <= 0:
                FileDisplayManager._playback_fps = inst
            else:
                FileDisplayManager._playback_fps = 0.8 * FileDisplayManager._playback_fps + 0.2 * inst
        FileDisplayManager._last_display_time = now
    
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
        FileDisplayManager._last_image_pixmap = None
        FileDisplayManager._native_fps = 0.0
        FileDisplayManager._timer_fps = 0.0
        FileDisplayManager._total_frames = 0
        FileDisplayManager._current_frame_index = 0
        FileDisplayManager._is_paused = False
        FileDisplayManager._processed_frames_counter = 0
        FileDisplayManager._processed_fps = 0.0
    
    @staticmethod
    def update_video_display_settings(show_image: bool = True, show_horizon: bool = True, show_axis: bool = False) -> None:
        """Update visibility toggles during video playback without restarting."""
        if FileDisplayManager._video_capture is not None:
            FileDisplayManager._show_image = show_image
            FileDisplayManager._show_horizon = show_horizon
            FileDisplayManager._show_axis = show_axis
            # If paused, re-render the current frame immediately
            if FileDisplayManager._is_paused:
                FileDisplayManager.refresh_paused_frame(force_recompute=show_horizon)

    @staticmethod
    def _install_image_resize_handler(content_area: QLabel) -> None:
        """Install a resize event filter to rescale the last image pixmap on resize."""
        # Remove existing filter to avoid duplicates
        FileDisplayManager._remove_image_resize_handler(content_area)

        class _ResizeFilter(QObject):
            def eventFilter(self, obj, event):
                if obj is content_area and event.type() == QEvent.Type.Resize:
                    if FileDisplayManager._last_image_pixmap is not None:
                        scaled = FileDisplayManager._last_image_pixmap.scaled(
                            content_area.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                        content_area.setPixmap(scaled)
                return False

        filt = _ResizeFilter(content_area)
        FileDisplayManager._resize_filter = filt
        content_area.installEventFilter(filt)

    @staticmethod
    def _remove_image_resize_handler(content_area: QLabel) -> None:
        """Remove the resize event filter if present."""
        if FileDisplayManager._resize_filter is not None:
            try:
                content_area.removeEventFilter(FileDisplayManager._resize_filter)
            except Exception:
                pass
            FileDisplayManager._resize_filter = None

    # -------- Playback controls integration --------
    @staticmethod
    def pause() -> None:
        if FileDisplayManager._video_timer is not None and not FileDisplayManager._is_paused:
            FileDisplayManager._video_timer.stop()
            FileDisplayManager._is_paused = True

    @staticmethod
    def resume() -> None:
        if FileDisplayManager._video_timer is not None and FileDisplayManager._is_paused:
            interval_ms = int(1000 / FileDisplayManager._timer_fps) if FileDisplayManager._timer_fps > 0 else 50
            FileDisplayManager._video_timer.start(interval_ms)
            FileDisplayManager._is_paused = False

    @staticmethod
    def is_paused() -> bool:
        return FileDisplayManager._is_paused

    @staticmethod
    def seek_to_frame(frame_index: int) -> None:
        if FileDisplayManager._video_capture is None:
            return
        frame_index = max(0, min(frame_index, FileDisplayManager._total_frames - 1))
        FileDisplayManager._video_capture.set(cv.CAP_PROP_POS_FRAMES, frame_index)
        FileDisplayManager._current_frame_index = frame_index
        # Render the frame immediately if paused
        if FileDisplayManager._is_paused:
            ret, frame = FileDisplayManager._video_capture.read()
            if ret:
                FileDisplayManager._video_capture.set(cv.CAP_PROP_POS_FRAMES, frame_index + 1)
                frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                FileDisplayManager._last_frame_rgb = frame_rgb
                processed_frame = FileDisplayManager._render_frame_from_array(
                    frame_rgb,
                    FileDisplayManager._cached_horizon_line,
                    FileDisplayManager._show_image,
                    FileDisplayManager._show_horizon,
                    FileDisplayManager._show_axis,
                )
                pixmap = FileDisplayManager._np_to_qpixmap(processed_frame)
                if (FileDisplayManager._current_content_area is not None and
                    FileDisplayManager._current_content_area.width() > 0 and
                    FileDisplayManager._current_content_area.height() > 0):
                    scaled_pixmap = pixmap.scaled(
                        FileDisplayManager._current_content_area.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    FileDisplayManager._current_content_area.setPixmap(scaled_pixmap)
                else:
                    FileDisplayManager._current_content_area.setPixmap(pixmap)

    @staticmethod
    def set_processing_fps(fps: float) -> None:
        if fps is not None and fps > 0:
            FileDisplayManager._desired_processing_fps = float(fps)
            FileDisplayManager._auto_processing_fps = False
            FileDisplayManager._recompute_timing()

    @staticmethod
    def set_display_max_fps(fps: float) -> None:
        if fps is not None and fps > 0:
            FileDisplayManager._max_fps = int(max(5, min(120, fps)))
            FileDisplayManager._recompute_timing()

    @staticmethod
    def _recompute_timing() -> None:
        """Recompute timer interval and processing stride based on desired FPS and native FPS."""
        if FileDisplayManager._video_capture is None or FileDisplayManager._native_fps <= 0:
            return
        timer_fps = min(FileDisplayManager._max_fps, FileDisplayManager._native_fps)
        FileDisplayManager._timer_fps = timer_fps
        desired = max(1.0, float(FileDisplayManager._desired_processing_fps or 1.0))
        FileDisplayManager._process_every_n_frames = max(1, int(round(timer_fps / desired)))
        if FileDisplayManager._video_timer is not None and not FileDisplayManager._is_paused:
            FileDisplayManager._video_timer.stop()
            FileDisplayManager._video_timer.start(int(1000 / timer_fps))

    @staticmethod
    def get_video_state() -> dict:
        """Return current playback state for UI (frames, fps)."""
        return {
            "current_frame": FileDisplayManager._current_frame_index,
            "total_frames": FileDisplayManager._total_frames,
            "native_fps": FileDisplayManager._native_fps,
            "timer_fps": FileDisplayManager._timer_fps,
            "processing_fps": FileDisplayManager._processed_fps,
            "playback_fps": FileDisplayManager._playback_fps,
            "is_paused": FileDisplayManager._is_paused,
        }

    @staticmethod
    def refresh_paused_frame(force_recompute: bool = True) -> None:
        """Re-render the current paused frame, optionally recomputing horizon."""
        if not FileDisplayManager._is_paused or FileDisplayManager._last_frame_rgb is None:
            return
        frame_rgb = FileDisplayManager._last_frame_rgb.copy()
        horizon_line = FileDisplayManager._cached_horizon_line
        if force_recompute and FileDisplayManager._current_horizon_finder is not None:
            try:
                horizon_line = FileDisplayManager._current_horizon_finder.find_horizon_line_from_array(frame_rgb)
                FileDisplayManager._cached_horizon_line = horizon_line
            except Exception:
                pass
        processed_frame = FileDisplayManager._render_frame_from_array(
            frame_rgb,
            horizon_line if FileDisplayManager._show_horizon else None,
            FileDisplayManager._show_image,
            FileDisplayManager._show_horizon,
            FileDisplayManager._show_axis,
        )
        pixmap = FileDisplayManager._np_to_qpixmap(processed_frame)
        if (FileDisplayManager._current_content_area is not None and
            FileDisplayManager._current_content_area.width() > 0 and
            FileDisplayManager._current_content_area.height() > 0):
            scaled_pixmap = pixmap.scaled(
                FileDisplayManager._current_content_area.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            FileDisplayManager._current_content_area.setPixmap(scaled_pixmap)
        else:
            FileDisplayManager._current_content_area.setPixmap(pixmap)
