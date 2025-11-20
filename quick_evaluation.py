"""
Quick Evaluation Script - Runs a subset of tests to generate results quickly.

This runs representative tests across:
- 2 maps (Town03, Town05)
- 2 weather conditions (Clear, Rain)
- 3 modes (multimodal, vision_only, baseline)
Total: 12 tests (much faster than full 64-test suite)
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

# Reduced test configuration for quick evaluation
MAPS = ["Town03", "Town05"]  # Representative maps
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
    }
}

MODES = {
    "multimodal": {"VISION_ENABLED": "true", "AUDIO_ENABLED": "true"},
    "vision_only": {"VISION_ENABLED": "true", "AUDIO_ENABLED": "false"},
    "baseline": {"USE_CARLA_AUTOPILOT": "true"}
}

# Reduced frame count for quick testing
# Can be overridden with EVAL_FRAMES environment variable
# For even faster testing, use fast_evaluation.py (100 frames) or set EVAL_FRAMES=100
FRAMES_PER_TEST = int(os.environ.get("EVAL_FRAMES", "500"))  # Reduced from 1000


def run_single_evaluation(map_name: str, weather_name: str, mode: str, 
                         weather_params: Dict, mode_params: Dict) -> Dict[str, Any]:
    """Run a single evaluation configuration."""
    print(f"\n{'='*60}")
    print(f"Running: {map_name} | {weather_name} | {mode}")
    print(f"{'='*60}")
    
    # Set environment variables for this run
    env = os.environ.copy()
    env["CARLA_MAP"] = map_name
    env["FRAME_LIMIT"] = str(FRAMES_PER_TEST)
    env["MAX_FRAMES"] = str(FRAMES_PER_TEST)
    env["EVAL_MODE"] = mode
    env["EVAL_OUTPUT_FILE"] = f"eval_result_{map_name}_{weather_name}_{mode}.json"
    
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
            encoding='utf-8',
            errors='replace',  # Replace encoding errors instead of failing
            timeout=300  # 5 minute timeout per test (can be reduced for faster failure detection)
        )
        elapsed_time = time.time() - start_time
        
        # Try to load results from output file
        result_file = env["EVAL_OUTPUT_FILE"]
        metrics = {
            "success": result.returncode == 0,
            "elapsed_time": elapsed_time,
            "frames_processed": FRAMES_PER_TEST,
            "map": map_name,
            "weather": weather_name,
            "mode": mode,
        }
        
        if os.path.exists(result_file):
            try:
                with open(result_file, "r") as f:
                    eval_data = json.load(f)
                    metrics.update(eval_data.get("metrics", {}))
                    print(f"[OK] Loaded results from {result_file}")
            except Exception as e:
                print(f"[WARN] Could not parse result file: {e}")
        
        # Parse collision info from output
        output = result.stdout + result.stderr
        
        # Log error output for debugging
        if result.returncode != 0:
            print(f"[ERROR] Test failed with return code {result.returncode}")
            # Print last 10 lines of output for debugging
            output_lines = output.split("\n")
            if len(output_lines) > 10:
                print("[ERROR] Last 10 lines of output:")
                for line in output_lines[-10:]:
                    if line.strip():
                        print(f"  {line}")
            else:
                print(f"[ERROR] Output: {output[:500]}")  # First 500 chars
        
        if "Collisions:" in output:
            for line in output.split("\n"):
                if "Collisions:" in line:
                    try:
                        collisions = int(line.split("Collisions:")[1].strip().split()[0])
                        metrics["collisions"] = collisions
                    except:
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


def run_quick_evaluation():
    """Run quick evaluation with subset of tests."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "frames_per_test": FRAMES_PER_TEST,
            "maps": MAPS,
            "weathers": list(WEATHER_PRESETS.keys()),
            "modes": list(MODES.keys()),
            "note": "Quick evaluation - subset of full test suite"
        },
        "results": []
    }
    
    total_tests = len(MAPS) * len(WEATHER_PRESETS) * len(MODES)
    current_test = 0
    
    print("="*60)
    print("QUICK EVALUATION - Representative Test Suite")
    print("="*60)
    print(f"Total tests: {total_tests}")
    print(f"Frames per test: {FRAMES_PER_TEST}")
    print(f"Estimated time: ~{total_tests * 3} minutes")
    print("\nMake sure CARLA is running!")
    print("="*60)
    
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
                time.sleep(3)
    
    return results


if __name__ == "__main__":
    print("Starting quick evaluation...")
    print("This will run 12 representative tests.")
    print("\nMake sure CARLA is running...")
    import time
    time.sleep(2)  # Brief pause to allow user to see the message
    
    results = run_quick_evaluation()
    
    print("\n" + "="*60)
    print("Quick Evaluation Complete!")
    print("="*60)
    print(f"\nResults saved to: evaluation_results.json")
    print(f"Total tests run: {len(results['results'])}")
    print("\nRun 'python analyze_evaluation_results.py' to analyze results.")


