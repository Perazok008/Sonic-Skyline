import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import csv
import torch
from PIL import Image
from scipy import ndimage
from sklearn.cluster import DBSCAN
import os

# Try to import SAM2 components
try:
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor
    SAM2_AVAILABLE = True
except ImportError:
    print("SAM2 not available, using fallback segmentation only")
    SAM2_AVAILABLE = False

output_file_name_prefix = "./test_results/SAM2_test4.1_"
test_landscape_image = "./test_images/road_asphalt_highway_mountain_tree-61355.jpg"

def load_sam2_model():
    """Load and initialize SAM2 model"""
    if not SAM2_AVAILABLE:
        print("SAM2 not installed, using fallback segmentation")
        return None
        
    try:
        # Check for model files in common locations
        possible_checkpoints = [
            "sam2_hiera_large.pt",
            "./models/sam2_hiera_large.pt", 
            "sam2_hiera_small.pt",
            "./models/sam2_hiera_small.pt"
        ]
        
        checkpoint_path = None
        for cp in possible_checkpoints:
            if os.path.exists(cp):
                checkpoint_path = cp
                break
        
        if checkpoint_path is None:
            print("SAM2 checkpoint not found. Please download SAM2 model weights.")
            print("Using fallback segmentation approach...")
            return None
            
        model_cfg = "sam2_hiera_l.yaml" if "large" in checkpoint_path else "sam2_hiera_s.yaml"
        
        sam2_model = build_sam2(model_cfg, checkpoint_path)
        predictor = SAM2ImagePredictor(sam2_model)
        print(f"SAM2 model loaded successfully from {checkpoint_path}")
        return predictor
    except Exception as e:
        print(f"Error loading SAM2 model: {e}")
        print("Using fallback segmentation approach...")
        return None

def segment_image_with_sam2(image_path, predictor=None):
    """Segment image using SAM2 or robust fallback method"""
    # Load image
    image = cv.imread(image_path)
    image_rgb = cv.cvtColor(image, cv.COLOR_BGR2RGB)
    
    if predictor is not None:
        try:
            predictor.set_image(image_rgb)
            height, width = image_rgb.shape[:2]
            
            # Conservative sky points from very top
            sky_points = np.array([
                [width//4, height//12], [width//2, height//15], [3*width//4, height//12]
            ])
            sky_labels = np.array([1, 1, 1])
            
            sky_masks, sky_scores, _ = predictor.predict(
                point_coords=sky_points,
                point_labels=sky_labels,
                multimask_output=True,
            )
            
            # Choose the best mask
            best_mask_idx = np.argmax(sky_scores)
            sky_mask = sky_masks[best_mask_idx]
            combined_mask = sky_mask.astype(np.uint8) * 255
            
            print("SAM2 segmentation successful")
            return combined_mask, image_rgb
            
        except Exception as e:
            print(f"SAM2 segmentation failed: {e}")
    
    # Robust fallback segmentation
    return robust_sky_segmentation(image_rgb)

def robust_sky_segmentation(image_rgb):
    """Robust sky segmentation that works reliably"""
    height, width = image_rgb.shape[:2]
    
    # Convert to different color spaces
    hsv = cv.cvtColor(image_rgb, cv.COLOR_RGB2HSV)
    gray = cv.cvtColor(image_rgb, cv.COLOR_RGB2GRAY)
    
    # Method 1: Color-based sky detection (more permissive)
    # Blue sky detection
    lower_blue = np.array([90, 20, 20])   # More permissive blue range
    upper_blue = np.array([140, 255, 255])
    blue_sky_mask = cv.inRange(hsv, lower_blue, upper_blue)
    
    # Bright areas (cloudy/overcast sky, fog)
    _, bright_mask = cv.threshold(gray, 140, 255, cv.THRESH_BINARY)  # Lower threshold
    
    # Light colored areas (could be sky)
    # Look for low saturation, high value areas
    low_sat_mask = cv.inRange(hsv, np.array([0, 0, 100]), np.array([180, 60, 255]))
    
    # Method 2: Gradient-based detection (simplified)
    # Sky typically has smoother gradients
    grad_x = cv.Sobel(gray, cv.CV_64F, 1, 0, ksize=3)
    grad_y = cv.Sobel(gray, cv.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
    
    # Areas with low gradient (smooth) are more likely sky
    _, smooth_mask = cv.threshold(gradient_magnitude, 40, 255, cv.THRESH_BINARY_INV)
    smooth_mask = smooth_mask.astype(np.uint8)
    
    # Combine methods - be more inclusive
    sky_mask = cv.bitwise_or(blue_sky_mask, bright_mask)
    sky_mask = cv.bitwise_or(sky_mask, low_sat_mask)
    
    # Only apply gradient constraint to refined areas
    sky_mask = cv.bitwise_and(sky_mask, smooth_mask)
    
    # Clean up with morphological operations
    kernel = np.ones((5,5), np.uint8)
    sky_mask = cv.morphologyEx(sky_mask, cv.MORPH_CLOSE, kernel)
    sky_mask = cv.morphologyEx(sky_mask, cv.MORPH_OPEN, kernel)
    
    # Apply a gentle geometric bias toward upper regions
    # But don't be too restrictive
    for i in range(height):
        weight = max(0.3, 1.0 - (i / height) * 0.8)  # Much gentler weighting
        sky_mask[i, :] = (sky_mask[i, :].astype(np.float32) * weight).astype(np.uint8)
    
    # Ensure we have some sky detection
    sky_pixels = np.sum(sky_mask > 0)
    total_pixels = height * width
    sky_percentage = (sky_pixels / total_pixels) * 100
    
    print(f"Sky detection: {sky_percentage:.1f}% of image")
    
    # If we detected too little sky, be more permissive
    if sky_percentage < 5:
        print("Very little sky detected, using more permissive detection...")
        # Just use bright areas and upper portion bias
        sky_mask = bright_mask.copy()
        for i in range(height//2, height):
            sky_mask[i, :] = 0  # Remove lower half
    
    return sky_mask, image_rgb

def find_horizon_from_segmentation(mask):
    """Simplified but robust horizon extraction"""
    height, width = mask.shape
    horizon_points = []
    
    # Extract potential horizon points
    for col in range(width):
        sky_column = mask[:, col]
        sky_pixels = np.where(sky_column > 0)[0]
        
        if len(sky_pixels) > 0:
            # Find the lowest sky pixel
            horizon_y = sky_pixels[-1]
            horizon_points.append((col, height - horizon_y))
        else:
            horizon_points.append((col, -1))  # Invalid
    
    # Clean and smooth the horizon line
    horizon_line = clean_horizon_line(horizon_points, height, width)
    
    return horizon_line

def clean_horizon_line(horizon_points, height, width):
    """Clean horizon line with simpler, more robust approach"""
    # Get valid points
    valid_points = [(x, y) for x, y in horizon_points if y != -1]
    
    if len(valid_points) < 3:
        # Not enough points, return a reasonable default
        default_height = height * 0.4  # 40% from bottom
        print(f"Insufficient horizon points, using default height: {default_height}")
        return [default_height] * width
    
    valid_points = np.array(valid_points)
    x_coords = valid_points[:, 0]
    y_coords = valid_points[:, 1]
    
    # Simple outlier removal using percentiles
    q1, q3 = np.percentile(y_coords, [25, 75])
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Keep points within reasonable range
    mask = (y_coords >= lower_bound) & (y_coords <= upper_bound)
    if np.sum(mask) > 2:
        x_coords = x_coords[mask]
        y_coords = y_coords[mask]
    
    # Fit a simple polynomial (linear or quadratic)
    try:
        degree = min(2, len(x_coords) - 1)
        poly_coeffs = np.polyfit(x_coords, y_coords, degree)
        poly_func = np.poly1d(poly_coeffs)
        
        # Generate smooth horizon
        x_full = np.arange(width)
        horizon_smooth = poly_func(x_full)
        
        # Apply reasonable constraints
        median_y = np.median(y_coords)
        max_deviation = height * 0.15  # 15% deviation allowed
        
        horizon_smooth = np.clip(horizon_smooth, 
                               max(0, median_y - max_deviation),
                               min(height * 0.7, median_y + max_deviation))
        
        print(f"Horizon line fitted with {len(x_coords)} points")
        return horizon_smooth.tolist()
        
    except:
        # Fallback to median value
        median_y = np.median(y_coords)
        print(f"Using median horizon height: {median_y}")
        return [median_y] * width

def save_segmentation_results(mask, image_rgb, horizon_line):
    """Save results with debug information"""
    height, width = mask.shape
    
    plt.clf()
    plt.figure(figsize=(15, 10))
    
    # Original image
    plt.subplot(2, 3, 1)
    plt.imshow(image_rgb)
    plt.title("Original Image")
    plt.axis('off')
    
    # Segmentation mask
    plt.subplot(2, 3, 2)
    plt.imshow(mask, cmap='gray')
    plt.title("Sky Segmentation Mask")
    plt.axis('off')
    
    # Horizon on original
    plt.subplot(2, 3, 3)
    plt.imshow(image_rgb)
    x = range(len(horizon_line))
    overlay_y = [height - val for val in horizon_line]
    plt.plot(x, overlay_y, color='red', linewidth=3, label='Detected Horizon')
    plt.title("Horizon Detection")
    plt.legend()
    plt.axis('off')
    
    # Edge detection for reference
    plt.subplot(2, 3, 4)
    gray = cv.cvtColor(image_rgb, cv.COLOR_RGB2GRAY)
    edges = cv.Canny(gray, 50, 150)
    plt.imshow(edges, cmap='gray')
    plt.title("Canny Edges (Reference)")
    plt.axis('off')
    
    # Horizon profile
    plt.subplot(2, 3, 5)
    plt.plot(x, horizon_line, color='blue', linewidth=2)
    plt.title(f"Horizon Profile")
    plt.xlabel("X Position")
    plt.ylabel("Height from Bottom")
    plt.grid(True, alpha=0.3)
    
    # Statistics
    plt.subplot(2, 3, 6)
    smoothness = np.std(np.diff(horizon_line))
    coverage = np.sum(mask > 0) / (height * width) * 100
    
    stats_text = f"""Results:
    
Sky Coverage: {coverage:.1f}%
Line Smoothness: {smoothness:.2f}
Height Range: {np.min(horizon_line):.0f}-{np.max(horizon_line):.0f}
Average Height: {np.mean(horizon_line):.1f}

Status: {"Good" if 5 < coverage < 50 and smoothness < 20 else "Needs Review"}"""
    
    plt.text(0.1, 0.5, stats_text, fontsize=11, verticalalignment='center',
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen" if coverage > 5 else "lightyellow", alpha=0.7))
    plt.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_file_name_prefix + "analysis.jpg", dpi=150, bbox_inches='tight')
    plt.close()

def save_horizon_line_as_csv(horizon_line):
    """Save horizon line data as CSV"""
    with open(output_file_name_prefix + "data.csv", "w+", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["x", "horizon_height"])
        for i, val in enumerate(horizon_line):
            writer.writerow([i, val])

def process_image(image_path):
    """Main function to process an image and extract horizon line"""
    print(f"Processing image: {image_path}")
    
    # Load SAM2 model (optional)
    predictor = load_sam2_model()
    
    # Segment the image
    mask, image_rgb = segment_image_with_sam2(image_path, predictor)
    
    # Extract horizon line from segmentation
    horizon_line = find_horizon_from_segmentation(mask)
    
    # Save results
    save_segmentation_results(mask, image_rgb, horizon_line)
    save_horizon_line_as_csv(horizon_line)
    
    print(f"Results saved with prefix: {output_file_name_prefix}")
    print(f"Horizon line: avg={np.mean(horizon_line):.1f}, std={np.std(horizon_line):.1f}")
    
    return horizon_line, mask

if __name__ == "__main__":
    # Process the test image
    horizon_line, mask = process_image(test_landscape_image)
    print("Horizon detection completed!") 