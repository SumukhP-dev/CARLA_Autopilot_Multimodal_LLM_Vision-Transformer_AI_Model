#!/usr/bin/env python3
"""
CARLA Compatibility Fix
This script attempts to fix CARLA compatibility issues on Windows.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version compatibility."""
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # CARLA 0.9.16 was built for Python 3.12, but we have 3.13
    if sys.version_info.major == 3 and sys.version_info.minor >= 13:
        print("WARNING: CARLA 0.9.16 was built for Python 3.12, but you're using Python 3.13")
        print("This may cause DLL loading issues.")
        return False
    return True

def try_dll_fix():
    """Try to fix DLL loading by copying required DLLs."""
    carla_root = Path("C:/Users/sumuk/Documents - Copy/CARLA_Latest")
    python_dir = Path(sys.executable).parent
    
    print(f"CARLA root: {carla_root}")
    print(f"Python directory: {python_dir}")
    
    # Look for required DLLs in CARLA
    dlls_to_copy = [
        "Engine/Binaries/ThirdParty/PhysX/VS2019/win64/PhysX3Common_x64.dll",
        "Engine/Binaries/ThirdParty/PhysX/VS2019/win64/PhysX3Cooking_x64.dll", 
        "Engine/Binaries/ThirdParty/PhysX/VS2019/win64/PhysX3Gpu_x64.dll",
        "Engine/Binaries/ThirdParty/PhysX/VS2019/win64/PhysX3_x64.dll"
    ]
    
    print("\nLooking for CARLA DLLs...")
    found_dlls = []
    for dll in dlls_to_copy:
        dll_path = carla_root / dll
        if dll_path.exists():
            print(f"  Found: {dll}")
            found_dlls.append(dll_path)
        else:
            print(f"  Missing: {dll}")
    
    if found_dlls:
        print(f"\nFound {len(found_dlls)} DLLs. Attempting to copy to Python directory...")
        try:
            for dll_path in found_dlls:
                dest_path = python_dir / dll_path.name
                shutil.copy2(dll_path, dest_path)
                print(f"  Copied: {dll_path.name}")
            return True
        except Exception as e:
            print(f"  Copy failed: {e}")
            return False
    else:
        print("No DLLs found to copy.")
        return False

def try_environment_fix():
    """Try setting environment variables to help with DLL loading."""
    print("\nSetting environment variables...")
    
    carla_root = "C:/Users/sumuk/Documents - Copy/CARLA_Latest"
    os.environ['CARLA_ROOT'] = carla_root
    os.environ['PATH'] = f"{carla_root}/Engine/Binaries/ThirdParty/PhysX/VS2019/win64;{os.environ['PATH']}"
    
    print(f"Set CARLA_ROOT: {carla_root}")
    print("Added CARLA DLL directory to PATH")

def test_carla_import():
    """Test CARLA import after fixes."""
    print("\nTesting CARLA import...")
    
    carla_path = "C:/Users/sumuk/Documents - Copy/CARLA_Latest/PythonAPI/carla/dist/carla-0.9.16-py3.12-win-amd64.egg"
    if carla_path not in sys.path:
        sys.path.append(carla_path)
    
    try:
        import carla
        print("SUCCESS: CARLA imported successfully!")
        
        # Test basic functionality
        try:
            client = carla.Client("localhost", 2000)
            client.set_timeout(2.0)
            print("SUCCESS: CARLA client created!")
            return True
        except Exception as e:
            print(f"CARLA client creation failed (this is normal if server isn't running): {e}")
            return True  # Import success is enough
            
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def main():
    print("CARLA Compatibility Fix")
    print("=" * 30)
    
    # Check Python version
    if not check_python_version():
        print("\nConsider using Python 3.12 for better CARLA compatibility")
    
    # Try environment fix
    try_environment_fix()
    
    # Try DLL fix
    if try_dll_fix():
        print("DLLs copied successfully")
    else:
        print("DLL copy failed or no DLLs found")
    
    # Test import
    if test_carla_import():
        print("\nCARLA is working! You can now run the simulator.")
        print("\nTo start the simulation:")
        print("1. Start CARLA server: C:/Users/sumuk/Documents - Copy/CARLA_Latest/CarlaUE4.exe")
        print("2. Run: python simulator.py")
    else:
        print("\nCARLA still not working. Possible solutions:")
        print("1. Install Python 3.12 and use that instead")
        print("2. Download a newer CARLA version (0.9.15 or 0.9.17)")
        print("3. Use CARLA with Docker")
        print("4. Run as Administrator")

if __name__ == "__main__":
    main()
