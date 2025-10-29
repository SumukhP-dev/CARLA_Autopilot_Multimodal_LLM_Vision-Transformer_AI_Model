#!/usr/bin/env python3
"""
CARLA DLL Fix Script
This script attempts to fix CARLA DLL loading issues on Windows.
"""

import os
import sys
import shutil
from pathlib import Path

def add_carla_to_path():
    """Add CARLA to Python path and set environment variables."""
    carla_path = "C:/Users/sumuk/Documents - Copy/CARLA_Latest/PythonAPI/carla/dist/carla-0.9.16-py3.12-win-amd64.egg"
    carla_root = "C:/Users/sumuk/Documents - Copy/CARLA_Latest/WindowsNoEditor"
    
    if carla_path not in sys.path:
        sys.path.append(carla_path)
    
    # Set CARLA environment variables
    os.environ['CARLA_ROOT'] = carla_root
    os.environ['CARLA_SERVER'] = os.path.join(carla_root, "CarlaUE4.exe")
    
    print(f"Added CARLA to Python path: {carla_path}")
    print(f"Set CARLA_ROOT: {carla_root}")

def check_carla_dlls():
    """Check if CARLA DLLs exist and are accessible."""
    carla_root = "C:/Users/sumuk/Documents - Copy/CARLA_Latest/WindowsNoEditor"
    
    # Check for key DLLs
    dlls_to_check = [
        "CarlaUE4.exe",
        "Engine/Binaries/ThirdParty/PhysX/VS2019/win64/PhysX3Common_x64.dll",
        "Engine/Binaries/ThirdParty/PhysX/VS2019/win64/PhysX3Cooking_x64.dll",
        "Engine/Binaries/ThirdParty/PhysX/VS2019/win64/PhysX3Gpu_x64.dll"
    ]
    
    print("Checking CARLA DLLs...")
    for dll in dlls_to_check:
        dll_path = os.path.join(carla_root, dll)
        if os.path.exists(dll_path):
            print(f"  Found: {dll}")
        else:
            print(f"  Missing: {dll}")

def try_import_carla():
    """Try to import CARLA with various fixes."""
    print("\nAttempting to import CARLA...")
    
    # Method 1: Direct import
    try:
        import carla
        print("SUCCESS: CARLA imported directly!")
        return True
    except Exception as e:
        print(f"Direct import failed: {e}")
    
    # Method 2: Add to sys.path and try again
    try:
        carla_path = "C:/Users/sumuk/Documents - Copy/CARLA_Latest/PythonAPI/carla/dist/carla-0.9.16-py3.12-win-amd64.egg"
        if carla_path not in sys.path:
            sys.path.insert(0, carla_path)
        
        # Clear any cached imports
        if 'carla' in sys.modules:
            del sys.modules['carla']
        
        import carla
        print("SUCCESS: CARLA imported after path fix!")
        return True
    except Exception as e:
        print(f"Path fix import failed: {e}")
    
    # Method 3: Try with different Python version compatibility
    try:
        # Force Python 3.12 compatibility
        import importlib.util
        carla_path = "C:/Users/sumuk/Documents - Copy/CARLA_Latest/PythonAPI/carla/dist/carla-0.9.16-py3.12-win-amd64.egg"
        
        spec = importlib.util.spec_from_file_location("carla", carla_path)
        carla_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(carla_module)
        
        print("SUCCESS: CARLA imported with compatibility fix!")
        return True
    except Exception as e:
        print(f"Compatibility fix failed: {e}")
    
    return False

def main():
    print("CARLA DLL Fix Script")
    print("=" * 30)
    
    add_carla_to_path()
    check_carla_dlls()
    
    if try_import_carla():
        print("\nCARLA is working! You can now run the simulator.")
    else:
        print("\nCARLA DLL issues persist. Possible solutions:")
        print("1. Install Visual C++ 2015-2022 Redistributable (x64)")
        print("2. Install Visual C++ 2019 Redistributable (x64)")
        print("3. Try running as Administrator")
        print("4. Check Windows Defender/Antivirus isn't blocking DLLs")
        print("5. Reinstall CARLA with a fresh download")

if __name__ == "__main__":
    main()
