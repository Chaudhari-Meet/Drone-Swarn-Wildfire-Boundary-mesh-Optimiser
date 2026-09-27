"""
Test WeatherDataProvider with simulated weather data.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Data.WeatherDataProvider import WeatherDataProvider, WeatherData


def test_weather_simulated_data():
    """Test simulated weather generation."""
    print("\n[TEST] Simulated Weather Generation")
    print("=" * 60)
    
    provider = WeatherDataProvider(mode="simulated")
    
    # Test at different locations
    locations = [
        (35.0, -120.0, "Southern California"),
        (40.0, -105.0, "Colorado"),
        (45.0, -122.0, "Oregon"),
    ]
    
    for lat, lon, name in locations:
        weather = provider.get_weather(lat, lon)
        
        assert weather is not None
        assert -40 < weather.temperature_c < 50
        assert 0 <= weather.humidity_percent <= 100
        assert 0 <= weather.wind_speed_ms < 30
        assert 0 <= weather.wind_direction_deg < 360
        assert weather.pressure_hpa > 900  # Above sea level
        
        print(f"\n  {name} ({lat}, {lon}):")
        print(f"    Temperature: {weather.temperature_c:.1f} C")
        print(f"    Humidity: {weather.humidity_percent:.0f}%")
        print(f"    Wind: {weather.wind_speed_ms:.1f} m/s from {weather.wind_direction_deg:.0f}°")
        print(f"    Pressure: {weather.pressure_hpa:.1f} hPa")
        print(f"    Fire Danger Index: {weather.fire_danger_index:.1f}/100")
    
    print(f"\n[OK] Generated realistic weather for {len(locations)} locations")
    return True


def test_weather_fire_danger_index():
    """Test fire danger index calculation."""
    print("\n[TEST] Fire Danger Index Calculation")
    print("=" * 60)
    
    provider = WeatherDataProvider(mode="simulated")
    
    # Test 1: High danger conditions
    high_danger = WeatherData(
        timestamp=datetime.now(),
        latitude=35.0,
        longitude=-120.0,
        wind_speed_ms=15,  # Strong wind
        wind_direction_deg=270,
        temperature_c=35,  # Hot
        humidity_percent=20,  # Dry
        pressure_hpa=1013,
        precipitation_mm=0
    )
    
    danger_high = high_danger.fire_danger_index
    assert danger_high > 60, f"High danger should be >60, got {danger_high:.1f}"
    print(f"\n  High danger conditions: {danger_high:.1f}/100")
    print(f"    (35C, 20% humidity, 15 m/s wind)")
    
    # Test 2: Low danger conditions
    low_danger = WeatherData(
        timestamp=datetime.now(),
        latitude=35.0,
        longitude=-120.0,
        wind_speed_ms=2,  # Light wind
        wind_direction_deg=270,
        temperature_c=15,  # Cool
        humidity_percent=80,  # Wet
        pressure_hpa=1013,
        precipitation_mm=5  # Recent rain
    )
    
    danger_low = low_danger.fire_danger_index
    assert danger_low < 30, f"Low danger should be <30, got {danger_low:.1f}"
    print(f"\n  Low danger conditions: {danger_low:.1f}/100")
    print(f"    (15C, 80% humidity, 2 m/s wind)")
    
    # Test 3: Favorable for spread
    favorable = high_danger.is_favorable_for_spread
    unfavorable = low_danger.is_favorable_for_spread
    
    assert favorable == True, "High danger should be favorable for spread"
    assert unfavorable == False, "Low danger should not be favorable for spread"
    print(f"\n[OK] Fire danger index correctly calculated")
    
    return True


def test_weather_forecast():
    """Test weather forecasting."""
    print("\n[TEST] Weather Forecasting")
    print("=" * 60)
    
    provider = WeatherDataProvider(mode="simulated")
    
    # Generate 24-hour forecast
    forecast = provider.get_weather_forecast(35.0, -120.0, hours=24)
    
    assert len(forecast) > 0, "Forecast should have data points"
    assert len(forecast) >= 8, f"24-hour forecast should have ~8 data points (3h intervals), got {len(forecast)}"
    
    print(f"\n  24-hour forecast: {len(forecast)} data points")
    
    # Analyze variations
    temps = [w.temperature_c for w in forecast]
    winds = [w.wind_speed_ms for w in forecast]
    
    temp_range = max(temps) - min(temps)
    wind_range = max(winds) - min(winds)
    
    print(f"  Temperature range: {min(temps):.1f}C to {max(temps):.1f}C ({temp_range:.1f}C variation)")
    print(f"  Wind range: {min(winds):.1f} to {max(winds):.1f} m/s ({wind_range:.1f} m/s variation)")
    
    assert temp_range > 5, "Should have temperature variation over day"
    print(f"\n[OK] Generated realistic 24-hour forecast")
    
    return True


def test_weather_diurnal_cycle():
    """Test that weather follows diurnal (daily) cycle."""
    print("\n[TEST] Diurnal Weather Cycle")
    print("=" * 60)
    
    provider = WeatherDataProvider(mode="simulated")
    
    # Generate weather for different times of day
    base_date = datetime(2026, 9, 25)
    hours_in_day = [0, 6, 12, 18, 23]  # Midnight, dawn, noon, dusk, late night
    
    temperatures = []
    humidities = []
    
    print("\n  Time   | Temp | Humidity | Fire Danger")
    print("  -------|------|----------|------------")
    
    for hour in hours_in_day:
        timestamp = base_date + timedelta(hours=hour)
        weather = provider.get_weather(35.0, -120.0, timestamp)
        
        temperatures.append(weather.temperature_c)
        humidities.append(weather.humidity_percent)
        
        time_str = timestamp.strftime("%H:%M")
        print(f"  {time_str}  | {weather.temperature_c:5.1f} | {weather.humidity_percent:7.0f}% | {weather.fire_danger_index:6.1f}")
    
    # Temperature should peak around noon (hour 12)
    noon_idx = hours_in_day.index(12)
    midnight_idx = hours_in_day.index(0)
    
    assert temperatures[noon_idx] > temperatures[midnight_idx], "Should be hotter at noon than midnight"
    print(f"\n[OK] Temperature peaks at noon (diurnal cycle verified)")
    
    return True


def test_weather_summary():
    """Test weather summary statistics."""
    print("\n[TEST] Weather Summary Statistics")
    print("=" * 60)
    
    provider = WeatherDataProvider(mode="simulated")
    
    summary = provider.get_weather_summary(35.0, -120.0, hours=24)
    
    assert "temperature" in summary
    assert "wind_speed" in summary
    assert "humidity" in summary
    assert "fire_danger" in summary
    
    print(f"\n  Period: {summary['period_hours']} hours ({summary['samples']} samples)")
    print(f"\n  Temperature:")
    print(f"    Min: {summary['temperature']['min']:.1f}C")
    print(f"    Avg: {summary['temperature']['avg']:.1f}C")
    print(f"    Max: {summary['temperature']['max']:.1f}C")
    
    print(f"\n  Wind Speed:")
    print(f"    Min: {summary['wind_speed']['min']:.1f} m/s")
    print(f"    Avg: {summary['wind_speed']['avg']:.1f} m/s")
    print(f"    Max: {summary['wind_speed']['max']:.1f} m/s")
    
    print(f"\n  Fire Danger Index:")
    print(f"    Min: {summary['fire_danger']['min']:.1f}/100")
    print(f"    Avg: {summary['fire_danger']['avg']:.1f}/100")
    print(f"    Max: {summary['fire_danger']['max']:.1f}/100")
    
    print(f"\n  Favorable periods: {summary['favorable_periods']}/{summary['samples']}")
    
    print(f"\n[OK] Weather summary generated successfully")
    
    return True


def test_weather_caching():
    """Test weather data caching."""
    print("\n[TEST] Weather Data Caching")
    print("=" * 60)
    
    provider = WeatherDataProvider(mode="cached")
    
    # First call should generate and cache
    weather1 = provider.get_weather(35.0, -120.0)
    assert weather1 is not None
    
    # Second call should use cache
    weather2 = provider.get_weather(35.0, -120.0)
    assert weather2 is not None
    
    # Cached data should be identical
    assert weather1.temperature_c == weather2.temperature_c
    assert weather1.wind_speed_ms == weather2.wind_speed_ms
    
    print(f"\n  First weather fetch: {weather1.temperature_c:.1f}C")
    print(f"  Cached second fetch: {weather2.temperature_c:.1f}C (identical)")
    
    # Different location should have different data
    weather3 = provider.get_weather(40.0, -105.0)
    assert weather3.temperature_c != weather1.temperature_c or weather3.wind_speed_ms != weather1.wind_speed_ms
    
    print(f"  Different location: {weather3.temperature_c:.1f}C (different)")
    print(f"\n[OK] Weather caching works correctly")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Weather Data Provider Testing")
    print("=" * 60)
    
    all_passed = True
    tests = [
        test_weather_simulated_data,
        test_weather_fire_danger_index,
        test_weather_forecast,
        test_weather_diurnal_cycle,
        test_weather_summary,
        test_weather_caching,
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
        print("[SUCCESS] All weather tests passed!")
    else:
        print("[FAIL] Some tests failed")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
