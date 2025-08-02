"""
Export manager for handling horizon detection result exports
"""
import csv
import os
from pathlib import Path
from typing import List, Optional, Dict
import numpy as np
import cv2 as cv
from PyQt6.QtWidgets import QMessageBox


class ExportManager:
    """Manages export operations for horizon detection results"""
    
    @staticmethod
    def export_results(
        export_config: Dict[str, bool],
        save_path: str,
        base_name: str,
        file_path: Optional[str] = None,
        horizon_line: Optional[List[int]] = None,
        all_horizon_lines: Optional[List[List[int]]] = None
    ) -> bool:
        """
        Export horizon detection results based on configuration
        
        Args:
            export_config: Dictionary with export format flags
            save_path: Directory to save files
            base_name: Base name for files (suffixes will be added)
            file_path: Path to original file
            horizon_line: Single horizon line data (for images)
            all_horizon_lines: All horizon lines (for videos)
        
        Returns:
            bool: True if all exports successful, False otherwise
        """
        success = True
        
        try:
            # Export CSV data
            if export_config.get('csv', False):
                success &= ExportManager._export_csv(
                    save_path, base_name, horizon_line, all_horizon_lines
                )
            
            # Export graph visualization
            if export_config.get('graph', False) and (horizon_line or all_horizon_lines):
                success &= ExportManager._export_graph(
                    save_path, base_name, file_path, horizon_line, all_horizon_lines
                )
            
            # Export overlay on original
            if export_config.get('overlay', False) and file_path and (horizon_line or all_horizon_lines):
                success &= ExportManager._export_overlay(
                    save_path, base_name, file_path, horizon_line, all_horizon_lines
                )
            
        except Exception as e:
            print(f"Export error: {e}")
            return False
        
        return success
    
    @staticmethod
    def _export_csv(
        save_path: str,
        base_name: str,
        horizon_line: Optional[List[int]],
        all_horizon_lines: Optional[List[List[int]]]
    ) -> bool:
        """Export horizon line data to CSV"""
        try:
            csv_path = os.path.join(save_path, f"{base_name}_csv.csv")
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                if all_horizon_lines:
                    # Video: Export all frames
                    writer.writerow(['Frame', 'X', 'Y'])
                    for frame_idx, line in enumerate(all_horizon_lines):
                        if line:
                            for x, y in enumerate(line):
                                if y != -1:  # Skip invalid points
                                    writer.writerow([frame_idx, x, y])
                elif horizon_line:
                    # Image: Export single frame
                    writer.writerow(['X', 'Y'])
                    for x, y in enumerate(horizon_line):
                        if y != -1:  # Skip invalid points
                            writer.writerow([x, y])
                else:
                    # No data to export
                    writer.writerow(['X', 'Y'])
                    writer.writerow(['No horizon data available'])
            
            return True
            
        except Exception as e:
            print(f"CSV export error: {e}")
            return False
    
    @staticmethod
    def _export_graph(
        save_path: str,
        base_name: str,
        file_path: Optional[str],
        horizon_line: Optional[List[int]],
        all_horizon_lines: Optional[List[List[int]]]
    ) -> bool:
        """Export horizon line as graph visualization"""
        try:
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(12, 8))
            
            if all_horizon_lines:
                # Video: Plot multiple lines
                plt.title("Horizon Lines - Video Analysis")
                for frame_idx, line in enumerate(all_horizon_lines[:min(10, len(all_horizon_lines))]):  # Limit to first 10 frames for clarity
                    if line:
                        x_coords = [i for i, y in enumerate(line) if y != -1]
                        y_coords = [y for y in line if y != -1]
                        if x_coords and y_coords:
                            plt.plot(x_coords, y_coords, alpha=0.7, label=f'Frame {frame_idx}')
                
                plt.xlabel('Image Width (pixels)')
                plt.ylabel('Height from Bottom (pixels)')
                plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                plt.grid(True, alpha=0.3)
                
            elif horizon_line:
                # Image: Plot single line
                plt.title("Horizon Line - Image Analysis")
                x_coords = [i for i, y in enumerate(horizon_line) if y != -1]
                y_coords = [y for y in horizon_line if y != -1]
                
                if x_coords and y_coords:
                    plt.plot(x_coords, y_coords, 'b-', linewidth=2, label='Horizon Line')
                    plt.fill_between(x_coords, 0, y_coords, alpha=0.3)
                
                plt.xlabel('Image Width (pixels)')
                plt.ylabel('Height from Bottom (pixels)')
                plt.legend()
                plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save as PNG
            graph_path = os.path.join(save_path, f"{base_name}_graph.png")
            plt.savefig(graph_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return True
            
        except ImportError:
            print("Matplotlib not available for graph export")
            return False
        except Exception as e:
            print(f"Graph export error: {e}")
            return False
    
    @staticmethod
    def _export_overlay(
        save_path: str,
        base_name: str,
        file_path: str,
        horizon_line: Optional[List[int]],
        all_horizon_lines: Optional[List[List[int]]]
    ) -> bool:
        """Export original file with horizon line overlay"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                return ExportManager._export_image_overlay(
                    save_path, base_name, file_path, horizon_line
                )
            elif file_ext in ['.mp4', '.avi', '.mov', '.mkv']:
                return ExportManager._export_video_overlay(
                    save_path, base_name, file_path, all_horizon_lines
                )
            else:
                print(f"Unsupported file format for overlay: {file_ext}")
                return False
                
        except Exception as e:
            print(f"Overlay export error: {e}")
            return False
    
    @staticmethod
    def _export_image_overlay(
        save_path: str,
        base_name: str,
        file_path: str,
        horizon_line: Optional[List[int]]
    ) -> bool:
        """Export image with horizon line overlay"""
        try:
            # Load original image
            image = cv.imread(file_path)
            if image is None:
                return False
            
            height = image.shape[0]
            
            # Draw horizon line
            if horizon_line:
                # Calculate line thickness based on image size
                min_dimension = min(image.shape[:2])
                line_thickness = max(2, min_dimension // 300)
                
                for x, height_val in enumerate(horizon_line):
                    if height_val != -1 and x < image.shape[1]:
                        y = height - height_val
                        if 0 <= y < height:
                            cv.circle(image, (x, y), radius=line_thickness, 
                                    color=(255, 0, 255), thickness=-1)
            
            # Save overlay image
            overlay_path = os.path.join(save_path, f"{base_name}_overlay.png")
            cv.imwrite(overlay_path, image)
            
            return True
            
        except Exception as e:
            print(f"Image overlay export error: {e}")
            return False
    
    @staticmethod
    def _export_video_overlay(
        save_path: str,
        base_name: str,
        file_path: str,
        all_horizon_lines: Optional[List[List[int]]]
    ) -> bool:
        """Export video with horizon line overlay"""
        try:
            # Open original video
            cap = cv.VideoCapture(file_path)
            if not cap.isOpened():
                return False
            
            # Get video properties
            fps = cap.get(cv.CAP_PROP_FPS) or 30
            width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
            
            # Setup video writer
            fourcc = cv.VideoWriter_fourcc(*'mp4v')
            overlay_path = os.path.join(save_path, f"{base_name}_overlay.mp4")
            out = cv.VideoWriter(overlay_path, fourcc, fps, (width, height))
            
            frame_idx = 0
            line_thickness = max(2, min(width, height) // 300)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Draw horizon line if available for this frame
                if (all_horizon_lines and 
                    frame_idx < len(all_horizon_lines) and 
                    all_horizon_lines[frame_idx]):
                    
                    horizon_line = all_horizon_lines[frame_idx]
                    for x, height_val in enumerate(horizon_line):
                        if height_val != -1 and x < width:
                            y = height - height_val
                            if 0 <= y < height:
                                cv.circle(frame, (x, y), radius=line_thickness, 
                                        color=(255, 0, 255), thickness=-1)
                
                out.write(frame)
                frame_idx += 1
            
            cap.release()
            out.release()
            
            return True
            
        except Exception as e:
            print(f"Video overlay export error: {e}")
            return False