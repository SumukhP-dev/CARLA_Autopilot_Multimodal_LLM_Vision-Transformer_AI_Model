#!/usr/bin/env python3

import sys
import os

# Add CARLA path
carla_path = "C:/Users/sumuk/Documents - Copy/CARLA_Latest/PythonAPI/carla/dist/carla-0.9.16-py3.12-win-amd64.egg"
if carla_path not in sys.path:
    sys.path.append(carla_path)

try:
    import carla
    print("SUCCESS: CARLA module imported successfully")
    
    # Try to connect to CARLA server
    client = carla.Client("localhost", 2000)
    client.set_timeout(5.0)
    
    print("SUCCESS: Connected to CARLA server")
    
    # Get world info
    world = client.get_world()
    print(f"SUCCESS: World loaded: {world}")
    
    # Get available maps
    available_maps = client.get_available_maps()
    print(f"SUCCESS: Available maps: {len(available_maps)}")
    
    # Load a world
    world = client.load_world("Town03")
    print(f"SUCCESS: Loaded world: {world}")
    
    # Get spawn points
    spawn_points = world.get_map().get_spawn_points()
    print(f"SUCCESS: Found {len(spawn_points)} spawn points")
    
    print("\nCARLA connection successful! You should see the CARLA window.")
    
except ImportError as e:
    print(f"CARLA import failed: {e}")
    print("This is likely due to missing DLL dependencies.")
except Exception as e:
    print(f"CARLA connection failed: {e}")
    print("Make sure CARLA server is running.")
