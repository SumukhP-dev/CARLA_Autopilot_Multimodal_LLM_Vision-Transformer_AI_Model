"""
Comprehensive Evaluation Runner for CARLA Autopilot System

This script runs systematic evaluations across:
- Multiple maps (Town01, Town03, Town05, Town10)
- Multiple weather conditions (Clear, Rain, Fog, Night)
- Ablation studies (vision-only, audio-only, multimodal)
- Baseline comparisons (CARLA autopilot vs. our system)

Results are saved to evaluation_results.json for analysis.
"""

import os
import json
import time
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

# Evaluation configuration
MAPS = ["Town01", "Town03", "Town05", "Town10"]
WEATHER_PRESETS = {
    "Clear": {
        "cloudiness": 0.0,
        "precipitation": 0.0,
        "sun_altitude_angle": 90.0,
        "sun_azimuth_angle": 0.0,
        "precipitation_deposits": 0.0,
        "wind_intensity": 0.0,
        "fog_density": 0.0,
        "wetness": 0.0,
    },
    "Rain": {
        "cloudiness": 80.0,
        "precipitation": 50.0,
        "sun_altitude_angle": 30.0,
        "sun_azimuth_angle": 0.0,
        "precipitation_deposits": 50.0,
        "wind_intensity": 20.0,
        "fog_density": 0.0,
        "wetness": 50.0,
    },
    "Fog": {
        "cloudiness": 100.0,
        "precipitation": 0.0,
        "sun_altitude_angle": 10.0,
        "sun_azimuth_angle": 0.0,
        "precipitation_deposits": 0.0,
        "wind_intensity": 0.0,
        "fog_density": 50.0,
        "wetness": 0.0,
    },
    "Night": {
        "cloudiness": 0.0,
        "precipitation": 0.0,
        "sun_altitude_angle": -30.0,
        "sun_azimuth_angle": 0.0,
        "precipitation_deposits": 0.0,
        "wind_intensity": 0.0,
        "fog_density": 0.0,
        "wetness": 0.0,
    }
}

MODES = {
    "multimodal": {"VISION_ENABLED": "true", "AUDIO_ENABLED": "true"},
    "vision_only": {"VISION_ENABLED": "true", "AUDIO_ENABLED": "false"},
    "audio_only": {"VISION_ENABLED": "false", "AUDIO_ENABLED": "true"},
    "baseline": {"USE_CARLA_AUTOPILOT": "true"}  # CARLA's built-in autopilot
}

# Test configuration
FRAMES_PER_TEST = int(os.environ.get("EVAL_FRAMES", "1000"))  # Frames per test
MAX_FRAMES = int(os.environ.get("EVAL_MAX_FRAMES", "5000"))  # Max frames per run


def run_single_evaluation(map_name: str, weather_name: str, mode: str, 
                         weather_params: Dict, mode_params: Dict) -> Dict[str, Any]:
    """
    Run a single evaluation configuration.
    
    Returns:
        Dictionary with evaluation results
    """
    print(f"\n{'='*60}")
    print(f"Running: {map_name} | {weather_name} | {mode}")
    print(f"{'='*60}")
    
    # Set environment variables for this run
    env = os.environ.copy()
    env["CARLA_MAP"] = map_name
    env["FRAME_LIMIT"] = str(FRAMES_PER_TEST)
    env["EVAL_MODE"] = mode
    
    # Set weather parameters
    for key, value in weather_params.items():
        env[f"WEATHER_{key.upper()}"] = str(value)
    
    # Set mode parameters
    for key, value in mode_params.items():
        env[key] = value
    
    # Run simulator
    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, "simulator.py"],
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout per test
        )
        elapsed_time = time.time() - start_time
        
        # Parse results from output (you'll need to modify simulator to output JSON)
        # For now, we'll extract key metrics from stdout
        output = result.stdout + result.stderr
        
        # Extract metrics (this is a placeholder - you'll need to modify simulator.py
        # to output structured results)
        metrics = {
            "success": result.returncode == 0,
            "elapsed_time": elapsed_time,
            "frames_processed": FRAMES_PER_TEST,
            "map": map_name,
            "weather": weather_name,
            "mode": mode,
        }
        
        # Try to extract collision count, safety rate, etc. from output
        if "collision" in output.lower():
            # Parse collision count (you'll need to add structured output to simulator)
            pass
        
        return metrics
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Timeout",
            "map": map_name,
            "weather": weather_name,
            "mode": mode,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "map": map_name,
            "weather": weather_name,
            "mode": mode,
        }


def run_comprehensive_evaluation():
    """Run comprehensive evaluation across all configurations."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "frames_per_test": FRAMES_PER_TEST,
            "maps": MAPS,
            "weathers": list(WEATHER_PRESETS.keys()),
            "modes": list(MODES.keys()),
        },
        "results": []
    }
    
    total_tests = len(MAPS) * len(WEATHER_PRESETS) * len(MODES)
    current_test = 0
    
    for map_name in MAPS:
        for weather_name, weather_params in WEATHER_PRESETS.items():
            for mode, mode_params in MODES.items():
                current_test += 1
                print(f"\n[{current_test}/{total_tests}] Running evaluation...")
                
                result = run_single_evaluation(
                    map_name, weather_name, mode, weather_params, mode_params
                )
                results["results"].append(result)
                
                # Save intermediate results
                with open("evaluation_results.json", "w") as f:
                    json.dump(results, f, indent=2)
                
                # Brief pause between tests
                time.sleep(2)
    
    return results


def analyze_results(results: Dict) -> Dict[str, Any]:
    """Analyze evaluation results and generate summary statistics."""
    analysis = {
        "summary": {},
        "by_map": {},
        "by_weather": {},
        "by_mode": {},
        "comparisons": {}
    }
    
    # Group results
    for result in results["results"]:
        if not result.get("success"):
            continue
        
        map_name = result["map"]
        weather = result["weather"]
        mode = result["mode"]
        
        # By map
        if map_name not in analysis["by_map"]:
            analysis["by_map"][map_name] = []
        analysis["by_map"][map_name].append(result)
        
        # By weather
        if weather not in analysis["by_weather"]:
            analysis["by_weather"][weather] = []
        analysis["by_weather"][weather].append(result)
        
        # By mode
        if mode not in analysis["by_mode"]:
            analysis["by_mode"][mode] = []
        analysis["by_mode"][mode].append(result)
    
    # Calculate statistics
    # (Add your metric calculations here)
    
    return analysis


if __name__ == "__main__":
    print("="*60)
    print("CARLA Autopilot Comprehensive Evaluation")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  Maps: {len(MAPS)} ({', '.join(MAPS)})")
    print(f"  Weathers: {len(WEATHER_PRESETS)} ({', '.join(WEATHER_PRESETS.keys())})")
    print(f"  Modes: {len(MODES)} ({', '.join(MODES.keys())})")
    print(f"  Total tests: {len(MAPS) * len(WEATHER_PRESETS) * len(MODES)}")
    print(f"  Frames per test: {FRAMES_PER_TEST}")
    print("\nThis will take a while. Results will be saved to evaluation_results.json")
    
    input("\nPress Enter to start evaluation (make sure CARLA is running)...")
    
    results = run_comprehensive_evaluation()
    
    # Analyze results
    analysis = analyze_results(results)
    
    # Save full results
    with open("evaluation_results.json", "w") as f:
        json.dump({"raw_results": results, "analysis": analysis}, f, indent=2)
    
    print("\n" + "="*60)
    print("Evaluation Complete!")
    print("="*60)
    print(f"\nResults saved to: evaluation_results.json")
    print(f"Total tests run: {len(results['results'])}")

