"""
Test SatelliteImageryPipeline with synthetic satellite images.
"""

import sys
from pathlib import Path

import numpy as np

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Data.SatelliteImageryPipeline import (
    SatelliteImageryPipeline,
    ColorBasedDetector,
    ThermalAnomalyDetector,
    VegetationAnomalyDetector
)


def create_synthetic_satellite_image(width: int = 512, height: int = 512,
                                    has_fire: bool = True) -> np.ndarray:
    """
    Create synthetic satellite imagery for testing.
    
    Simulates Sentinel-2-like multi-spectral image with channels:
    - 0-2: RGB
    - 3: NIR
    - 4: SWIR
    """
    # Create base image (vegetation-covered terrain)
    image = np.zeros((height, width, 5), dtype=np.uint8)
    
    # Green vegetation background
    image[:, :, 0] = np.random.randint(80, 120, (height, width))    # Red
    image[:, :, 1] = np.random.randint(150, 200, (height, width))   # Green
    image[:, :, 2] = np.random.randint(60, 100, (height, width))    # Blue
    image[:, :, 3] = np.random.randint(180, 220, (height, width))   # NIR
    image[:, :, 4] = np.random.randint(100, 150, (height, width))   # SWIR
    
    if has_fire:
        # Add fire hotspots (red/bright regions)
        for _ in range(3):  # 3 fire hotspots
            cx = np.random.randint(50, width - 50)
            cy = np.random.randint(50, height - 50)
            radius = np.random.randint(20, 50)
            
            y, x = np.ogrid[:height, :width]
            mask = (x - cx)**2 + (y - cy)**2 <= radius**2
            
            # Intense red/NIR in fire areas
            image[mask, 0] = np.clip(image[mask, 0] + 150, 0, 255)  # Very red
            image[mask, 1] = np.clip(image[mask, 1] - 100, 0, 255)  # Low green
            image[mask, 2] = np.clip(image[mask, 2] - 100, 0, 255)  # Low blue
            image[mask, 3] = np.clip(image[mask, 3] - 100, 0, 255)  # Low NIR (fire absorbs)
            image[mask, 4] = np.clip(image[mask, 4] + 100, 0, 255)  # High SWIR (thermal)
    
    return image


def test_color_detector():
    """Test color-based fire detection."""
    print("\n[TEST] Color-Based Fire Detector")
    print("=" * 60)
    
    detector = ColorBasedDetector(threshold=0.3)
    
    # Test with fire
    image_fire = create_synthetic_satellite_image(has_fire=True)
    mask_fire = detector.detect(image_fire)
    fire_pixels = np.sum(mask_fire)
    
    # Test without fire
    image_no_fire = create_synthetic_satellite_image(has_fire=False)
    mask_no_fire = detector.detect(image_no_fire)
    no_fire_pixels = np.sum(mask_no_fire)
    
    print(f"\n  Image with fire: {fire_pixels} fire pixels detected")
    print(f"  Image without fire: {no_fire_pixels} fire pixels detected")
    
    assert fire_pixels > no_fire_pixels, "Should detect more fire in image with fire"
    assert fire_pixels > 0, "Should detect some fire"
    
    print(f"[OK] Color detector working correctly")
    return True


def test_thermal_detector():
    """Test thermal anomaly detection."""
    print("\n[TEST] Thermal Anomaly Detector")
    print("=" * 60)
    
    detector = ThermalAnomalyDetector(percentile=85)
    
    # Test with fire
    image_fire = create_synthetic_satellite_image(has_fire=True)
    mask_fire = detector.detect(image_fire)
    fire_pixels = np.sum(mask_fire)
    
    # Test without fire
    image_no_fire = create_synthetic_satellite_image(has_fire=False)
    mask_no_fire = detector.detect(image_no_fire)
    no_fire_pixels = np.sum(mask_no_fire)
    
    print(f"\n  Image with fire: {fire_pixels} anomalous pixels detected")
    print(f"  Image without fire: {no_fire_pixels} anomalous pixels detected")
    
    assert fire_pixels > no_fire_pixels, "Should detect more anomalies in fire image"
    
    print(f"[OK] Thermal detector working correctly")
    return True


def test_vegetation_detector():
    """Test vegetation anomaly detection."""
    print("\n[TEST] Vegetation Anomaly Detector")
    print("=" * 60)
    
    detector = VegetationAnomalyDetector(ndvi_threshold=0.2)
    
    # Test with fire
    image_fire = create_synthetic_satellite_image(has_fire=True)
    mask_fire = detector.detect(image_fire)
    fire_pixels = np.sum(mask_fire)
    
    # Test without fire
    image_no_fire = create_synthetic_satellite_image(has_fire=False)
    mask_no_fire = detector.detect(image_no_fire)
    no_fire_pixels = np.sum(mask_no_fire)
    
    print(f"\n  Image with fire: {fire_pixels} anomalous pixels detected")
    print(f"  Image without fire: {no_fire_pixels} anomalous pixels detected")
    
    assert fire_pixels >= no_fire_pixels, "Should detect at least as many anomalies in fire image"
    
    print(f"[OK] Vegetation detector working correctly")
    return True


def test_pipeline_detection():
    """Test full pipeline detection."""
    print("\n[TEST] Full Satellite Imagery Pipeline")
    print("=" * 60)
    
    pipeline = SatelliteImageryPipeline()
    
    # Test with fire
    image_fire = create_synthetic_satellite_image(has_fire=True)
    mask_fire = pipeline.detect_fires(image_fire)
    fire_pixels = np.sum(mask_fire)
    
    # Test without fire
    image_no_fire = create_synthetic_satellite_image(has_fire=False)
    mask_no_fire = pipeline.detect_fires(image_no_fire)
    no_fire_pixels = np.sum(mask_no_fire)
    
    print(f"\n  Image with fire: {fire_pixels} fire pixels detected")
    print(f"  Image without fire: {no_fire_pixels} fire pixels detected")
    
    assert fire_pixels > 0, "Should detect fire when present"
    assert fire_pixels > no_fire_pixels * 2, "Fire image should have significantly more detections"
    
    print(f"[OK] Pipeline detection working correctly")
    return True


def test_hotspot_extraction():
    """Test hotspot extraction from detection mask."""
    print("\n[TEST] Hotspot Extraction")
    print("=" * 60)
    
    pipeline = SatelliteImageryPipeline()
    
    # Create image with known fire
    image = create_synthetic_satellite_image(width=512, height=512, has_fire=True)
    mask = pipeline.detect_fires(image)
    
    # Extract hotspots
    hotspots = pipeline.extract_hotspots(mask, image, min_size=20)
    
    print(f"\n  Extracted {len(hotspots)} hotspots from fire mask")
    
    assert len(hotspots) > 0, "Should extract hotspots"
    assert len(hotspots) <= 5, "Should extract reasonable number of hotspots"
    
    # Check hotspot properties
    for i, hotspot in enumerate(hotspots):
        print(f"\n  Hotspot {i+1}:")
        print(f"    Center: {hotspot['center']}")
        print(f"    Size: {hotspot['size_pixels']} pixels")
        print(f"    Intensity: {hotspot['intensity']:.2f}")
        
        assert 0 <= hotspot['intensity'] <= 1, "Intensity should be 0-1"
        assert hotspot['size_pixels'] > 0, "Hotspot should have area"
    
    print(f"\n[OK] Hotspot extraction working correctly")
    return True


def test_boundary_generation():
    """Test boundary generation from hotspots."""
    print("\n[TEST] Boundary Generation")
    print("=" * 60)
    
    pipeline = SatelliteImageryPipeline()
    
    # Create image with fire
    image = create_synthetic_satellite_image(has_fire=True)
    mask = pipeline.detect_fires(image)
    hotspots = pipeline.extract_hotspots(mask, image)
    
    # Generate boundary
    boundary = pipeline.generate_boundary(hotspots)
    
    assert boundary is not None, "Should generate boundary"
    assert len(boundary) >= 3, "Boundary should have at least 3 points"
    
    print(f"\n  Generated boundary with {len(boundary)} vertices")
    
    for i, (x, y) in enumerate(boundary[:3]):  # Show first 3
        print(f"    Vertex {i+1}: ({x:.1f}, {y:.1f})")
    
    print(f"[OK] Boundary generation working correctly")
    return True


def test_detection_summary():
    """Test detection summary statistics."""
    print("\n[TEST] Detection Summary")
    print("=" * 60)
    
    pipeline = SatelliteImageryPipeline()
    
    # Create and process image
    image = create_synthetic_satellite_image(512, 512, has_fire=True)
    mask = pipeline.detect_fires(image)
    hotspots = pipeline.extract_hotspots(mask, image)
    
    # Get summary
    summary = pipeline.get_detection_summary()
    
    print(f"\n  Fire pixels: {summary['fire_pixels']}")
    print(f"  Total pixels: {summary['total_pixels']}")
    print(f"  Fire coverage: {summary['fire_percentage']:.2f}%")
    print(f"  Hotspot count: {summary['hotspot_count']}")
    
    assert summary['fire_pixels'] > 0, "Should have fire pixels"
    assert summary['fire_percentage'] > 0, "Should have fire percentage"
    assert summary['hotspot_count'] == len(hotspots), "Hotspot count should match"
    
    print(f"\n[OK] Detection summary correct")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Satellite Imagery Pipeline Testing")
    print("=" * 60)
    
    all_passed = True
    tests = [
        test_color_detector,
        test_thermal_detector,
        test_vegetation_detector,
        test_pipeline_detection,
        test_hotspot_extraction,
        test_boundary_generation,
        test_detection_summary,
    ]
    
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"\n[FAIL] {test.__name__}: {e}")
            all_passed = False
        except Exception as e:
            print(f"\n[FAIL] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] All satellite imagery tests passed!")
    else:
        print("[FAIL] Some tests failed")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
