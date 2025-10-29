#!/usr/bin/env python3
"""
CARLA Setup Script
This script helps set up CARLA with proper DLL dependencies on Windows.
"""

import os
import sys
import subprocess
import platform

def check_carla_installation():
    """Check if CARLA is properly installed and accessible."""
    carla_path = "C:/Users/sumuk/Documents - Copy/CARLA_Latest/PythonAPI/carla/dist/carla-0.9.16-py3.12-win-amd64.egg"
    
    if not os.path.exists(carla_path):
        print(f"CARLA not found at: {carla_path}")
        return False
    
    print(f"CARLA found at: {carla_path}")
    return True

def check_dll_dependencies():
    """Check for required DLL dependencies."""
    print("\nChecking DLL dependencies...")
    
    # Check for Visual C++ Redistributable
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                           r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64")
        print("Visual C++ 2015-2022 Redistributable found")
        return True
    except:
        print("Visual C++ 2015-2022 Redistributable not found")
        return False

def install_vcredist():
    """Provide instructions for installing Visual C++ Redistributable."""
    print("\nTo fix CARLA DLL issues, please install:")
    print("1. Microsoft Visual C++ 2015-2022 Redistributable (x64)")
    print("   Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe")
    print("2. Restart your computer after installation")
    print("3. Run this script again to verify")

def test_carla_import():
    """Test if CARLA can be imported successfully."""
    print("\nTesting CARLA import...")
    
    # Add CARLA to path
    carla_path = "C:/Users/sumuk/Documents - Copy/CARLA_Latest/PythonAPI/carla/dist/carla-0.9.16-py3.12-win-amd64.egg"
    if carla_path not in sys.path:
        sys.path.append(carla_path)
    
    try:
        import carla
        print("CARLA imported successfully!")
        
        # Test basic functionality
        client = carla.Client("localhost", 2000)
        client.set_timeout(2.0)
        print("CARLA client created successfully!")
        return True
        
    except ImportError as e:
        print(f"CARLA import failed: {e}")
        return False
    except Exception as e:
        print(f"CARLA imported but connection failed: {e}")
        print("   This is normal if CARLA server is not running")
        return True

def main():
    print("CARLA Setup and Diagnostics")
    print("=" * 40)
    
    # Check system
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    
    # Check CARLA installation
    if not check_carla_installation():
        print("\nPlease install CARLA first")
        return
    
    # Check DLL dependencies
    if not check_dll_dependencies():
        install_vcredist()
        return
    
    # Test CARLA import
    if test_carla_import():
        print("\nCARLA is ready to use!")
        print("\nTo run the simulator:")
        print("1. Start CARLA server: C:/Users/sumuk/Documents - Copy/CARLA_Latest/WindowsNoEditor/CarlaUE4.exe")
        print("2. Run: python simulator.py")
    else:
        print("\nCARLA setup incomplete. Please install Visual C++ Redistributable.")

if __name__ == "__main__":
    main()
