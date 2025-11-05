"""
CARLA Autopilot Simulator - Main Entry Point

This module orchestrates the complete autonomous driving system by:
1. Connecting to CARLA simulator
2. Initializing vehicle and sensors
3. Processing multimodal inputs (vision + audio)
4. Generating driving commands via LLM
5. Applying vehicle control
6. Monitoring simulation metrics

The system integrates Vision Transformer models, speech recognition, and
Large Language Models (LLMs) to enable intelligent autonomous driving.
"""

import glob
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import pygame  # We will be using this for manual control
import requests  # For sending data to dashboard backend
import time  # For timing requests

from audio_conversion import convert
from camera_text_processing import CameraTextProcessing
from player import Player
from text_to_instructions_converter import TextToInstructionsConverter
from video_recorder import VideoRecorder

def main():
    """
    Main simulation loop.
    
    Initializes CARLA connection, spawns vehicle, sets up sensors,
    and runs the autonomous driving simulation loop with multimodal
    AI decision-making.
    """
    print("=" * 60)
    print("CARLA Autopilot Simulator - Starting...")
    print("=" * 60)
    
    # Add CARLA Python API to path
    # Try to get CARLA path from environment variable, otherwise use default
    carla_path = os.environ.get("CARLA_PATH")
    
    # If not set, try to auto-detect CARLA path
    if not carla_path:
        # Try common installation locations
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Try default Windows paths
            possible_paths = [
                os.path.join(os.environ.get("USERPROFILE", ""), "Documents", "CARLA_Latest", "PythonAPI", "carla", "dist", "carla-0.9.16-py3.12-win-amd64.egg"),
                os.path.join(os.environ.get("USERPROFILE", ""), "Documents", "CARLA", "PythonAPI", "carla", "dist", "carla-0.9.16-py3.12-win-amd64.egg"),
            ]
        else:  # Linux/Mac
            # Try default Linux/Mac paths
            possible_paths = [
                os.path.expanduser("~/CARLA_0.9.16/PythonAPI/carla/dist/carla-0.9.16-py3.12-linux-x86_64.egg"),
                os.path.expanduser("~/CARLA/PythonAPI/carla/dist/carla-0.9.16-py3.12-linux-x86_64.egg"),
            ]
        
        # Try to find CARLA in common locations
        for path in possible_paths:
            if os.path.exists(path):
                carla_path = path
                break
    
    # If still not found, try using glob pattern (CARLA's default approach)
    if not carla_path or not os.path.exists(carla_path):
        try:
            import glob
            import platform
            system = platform.system()
            if system == "Windows":
                egg_pattern = "carla-*%d.%d-%s.egg" % (sys.version_info.major, sys.version_info.minor, 'win-amd64')
            else:
                egg_pattern = "carla-*%d.%d-%s.egg" % (sys.version_info.major, sys.version_info.minor, 'linux-x86_64')
            
            # Try common CARLA installation directories
            search_dirs = [
                os.path.join(os.environ.get("USERPROFILE", ""), "Documents", "CARLA_Latest", "PythonAPI", "carla", "dist"),
                os.path.join(os.environ.get("USERPROFILE", ""), "Documents", "CARLA", "PythonAPI", "carla", "dist"),
                os.path.expanduser("~/CARLA_0.9.16/PythonAPI/carla/dist"),
                os.path.expanduser("~/CARLA/PythonAPI/carla/dist"),
            ]
            
            for search_dir in search_dirs:
                if os.path.exists(search_dir):
                    matches = glob.glob(os.path.join(search_dir, egg_pattern))
                    if matches:
                        carla_path = matches[0]
                        break
        except Exception:
            pass
    
    if carla_path and os.path.exists(carla_path):
        sys.path.append(carla_path)
        print(f"[OK] Found CARLA at: {carla_path}")
    else:
        print(f"[ERROR] CARLA not found. Please set CARLA_PATH in .env file")
        print("Example: CARLA_PATH=C:\\path\\to\\carla\\dist\\carla-0.9.16-py3.12-win-amd64.egg")
        print("Or install CARLA and update .env file with the correct path")
        sys.exit(1)
    
    # Import CARLA after adding to path
    try:
        import carla
        print("[OK] CARLA module imported successfully")
    except Exception as e:
        print(f"[ERROR] Failed to import CARLA: {e}")
        sys.exit(1)

    # server running on our system with configurable host and port
    carla_host = os.environ.get("CARLA_HOST", "localhost")
    carla_port = int(os.environ.get("CARLA_PORT", "2000"))
    carla_timeout = float(os.environ.get("CARLA_TIMEOUT", "10.0"))  # Increased timeout
    
    print(f"Connecting to CARLA server at {carla_host}:{carla_port}...")
    client = carla.Client(carla_host, carla_port)
    client.set_timeout(carla_timeout)
    
    # Get map name from environment variable, default to Town03
    map_name = os.environ.get("CARLA_MAP", "Town03")
    print(f"[Map] Using map: {map_name}")
    
    # Get world - try to load specified map
    try:
        world = client.get_world()
        current_map = world.get_map().name
        print(f"[Map] Current map: {current_map}")
        
        # Load specified map if different from current
        if current_map != map_name:
            print(f"[Map] Loading new map: {map_name}...")
            world = client.load_world(map_name)
            print(f"[Map] Successfully loaded map: {world.get_map().name}")
        else:
            print(f"[Map] Already on map: {map_name}")
    except RuntimeError:
        print(f"[Map] No existing world found, loading {map_name}...")
        try:
            world = client.load_world(map_name)
            print(f"[Map] Successfully loaded map: {world.get_map().name}")
        except RuntimeError as e:
            print(f"ERROR: Could not load map {map_name}: {e}")
            print("\nPlease make sure:")
            print("1. CARLA server is running (CarlaUE4.exe)")
            print(f"2. CARLA server is accessible at {carla_host}:{carla_port}")
            print("3. CARLA server has finished loading")
            print(f"4. Map '{map_name}' is available in CARLA")
            print("\nAvailable maps can be checked with: client.get_available_maps()")
            sys.exit(1)
    
    # Get the actual map name for dashboard
    actual_map_name = world.get_map().name
    print(f"[Map] Active map: {actual_map_name}")
    spectator = world.get_spectator()

    # I have changed the weather to a clear noon.
    weather = carla.WeatherParameters(
        cloudiness=0.0,
        precipitation=0.0,
        sun_altitude_angle=10.0,
        sun_azimuth_angle=90.0,
        precipitation_deposits=0.0,
        wind_intensity=0.0,
        fog_density=0.0,
        wetness=0.0,
    )
    world.set_weather(weather)

    # First let's get the blueprint library and the spawn points for our world.
    # Depending on your Carla version and the map chosen, you get different actors
    # and spawn points respectively
    bp_lib = world.get_blueprint_library()
    spawn_points = world.get_map().get_spawn_points()


    # I am spawning an Audi etron here. You can check out the blueprint library
    # to spawn your vehicle of choice. Also we spawn in a random safe point 79
    vehicle_bp = bp_lib.find("vehicle.audi.etron")
    if vehicle_bp is None:
        print("ERROR: vehicle.audi.etron blueprint not found, trying any vehicle...")
        vehicle_bp = bp_lib.filter("vehicle.*")[0]  # Get first available vehicle
    
    ego_vehicle = world.try_spawn_actor(vehicle_bp, spawn_points[79])
    if ego_vehicle is None:
        print("ERROR: Failed to spawn vehicle at spawn point 79, trying another point...")
        # Try a different spawn point
        for i, spawn_point in enumerate(spawn_points[:10]):  # Try first 10 spawn points
            ego_vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)
            if ego_vehicle is not None:
                print(f"Successfully spawned vehicle at spawn point {i}")
                break
    
    if ego_vehicle is None:
        print("ERROR: Could not spawn vehicle at any spawn point")
        sys.exit(1)

    # Let's position the spectator just behind the vehicle
    # Carla.Transform has two parameters - Location and Rotation. We use this to
    # to position the spectator by going 4 metres behind and 2.5 metres above the
    # ego_vehicle

    transform = carla.Transform(
        ego_vehicle.get_transform().transform(carla.Location(x=-4, z=2.5)),
        ego_vehicle.get_transform().rotation,
    )
    spectator.set_transform(transform)

    # If you want to position the your_actor with just the coordinates,
    # you can use the below codes.
    # location = carla.Location(x=0, y=0, z=30)
    # rotation = carla.Rotation(roll=0, pitch=-30, yaw=180)
    # transform = carla.Transform(location, rotation)
    # your_actor.set_transform(transform)

    # Let's add the bus.
    vehicle_bp_bus = bp_lib.find("vehicle.mitsubishi.fusorosa")

    vehicle_bus = world.try_spawn_actor(vehicle_bp_bus, spawn_points[80])
    location = ego_vehicle.get_location()
    location.x -= 50
    vehicle_bus.set_location(location)

    # print("ego_vehicle", ego_vehicle.get_location())
    # print("vehicle_bus", vehicle_bus.get_location())
    # print("location", location)

    # Allows you to drive the ego_vehicle manually
    ego_vehicle.set_autopilot(False)

    ## Vehicle PHYSICS property

    # Create Wheels Physics Control
    front_left_wheel = carla.WheelPhysicsControl(
        tire_friction=2.0, damping_rate=1.5, max_steer_angle=70.0, long_stiff_value=1000
    )
    front_right_wheel = carla.WheelPhysicsControl(
        tire_friction=2.0, damping_rate=1.5, max_steer_angle=70.0, long_stiff_value=1000
    )
    rear_left_wheel = carla.WheelPhysicsControl(
        tire_friction=3.0, damping_rate=1.5, max_steer_angle=0.0, long_stiff_value=1000
    )
    rear_right_wheel = carla.WheelPhysicsControl(
        tire_friction=3.0, damping_rate=1.5, max_steer_angle=0.0, long_stiff_value=1000
    )  # Reducing friction increases idle throttle

    wheels = [front_left_wheel, front_right_wheel, rear_left_wheel, rear_right_wheel]

    # Change Vehicle Physics Control parameters of the vehicle
    physics_control = ego_vehicle.get_physics_control()
    physics_control.torque_curve = [
        carla.Vector2D(x=0, y=400),
        carla.Vector2D(x=1300, y=600),
    ]
    physics_control.max_rpm = 10000
    physics_control.moi = 1.0
    physics_control.damping_rate_full_throttle = 0.0
    physics_control.use_gear_autobox = True
    physics_control.gear_switch_time = 0.5
    physics_control.clutch_strength = 10
    physics_control.mass = 10000
    physics_control.drag_coefficient = 0.25
    physics_control.steering_curve = [
        carla.Vector2D(x=0, y=1),
        carla.Vector2D(x=100, y=1),
        carla.Vector2D(x=300, y=1),
    ]
    physics_control.use_sweep_wheel_collision = True
    physics_control.wheels = wheels

    # Apply Vehicle Physics Control for the vehicle
    ego_vehicle.apply_physics_control(physics_control)
    # Start with lower initial speed for safety
    ego_vehicle.apply_ackermann_control(carla.VehicleAckermannControl(speed=3.0, steer=0.0))

    pygame.init()  # initialising

    # Set up the Pygame display
    size = (640, 480)
    pygame.display.set_caption("CARLA Manual Control")
    screen = pygame.display.set_mode(size)

    # Set up the control object and loop until the user exits the script
    clock = pygame.time.Clock()
    done = False
    
    # Get target speed from environment
    target_speed = float(os.environ.get("TARGET_SPEED", "5.0"))
    
    # Track previous steering for rate limiting (safety feature to prevent abrupt turns)
    previous_steer = 0.0
    max_steer_change = 0.15  # Maximum steering change per frame to prevent crashes

    # Find a camera blueprint
    camera_bp = bp_lib.find('sensor.camera.rgb')

    player = Player(world, ego_vehicle)
    
    # Initialize camera processing once
    camera_text_processing = CameraTextProcessing(camera_bp, ego_vehicle, bp_lib, world)
    camera_text_processing.initial_camera()
    
    # Initialize text converter once
    text_to_instructions_converter = TextToInstructionsConverter()
    
    # Dashboard backend URL
    dashboard_url = os.environ.get("DASHBOARD_URL", "http://localhost:4000/api/simulations")
    
    # Track simulation statistics for dashboard
    collision_count = 0
    safe_frames = 0
    collision_detected = False
    
    def send_to_dashboard(map_name, collisions, safe_runs):
        """Send simulation data to dashboard backend"""
        try:
            data = {
                "name": map_name,
                "collisions": collisions,
                "safeRuns": safe_runs
            }
            response = requests.post(dashboard_url, json=data, timeout=2.0)
            if response.status_code == 200:
                print(f"[Dashboard] Data sent successfully: {data}")
                return True
            else:
                print(f"[Dashboard] Failed to send data: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"[Dashboard] Connection error (backend may not be running): {e}")
            return False
    
    print("Starting autopilot simulation...")
    
    # Check if test mode is enabled (random controls for fast testing)
    test_mode = os.environ.get("TEST_MODE", "false").lower() == "true"
    
    # Initialize video recorder for 2 minutes of recording
    # Note: Actual simulation may run slower due to LLM/ML processing, so we calculate
    # duration based on expected frame rate, not wall-clock time
    record_duration = 120  # Target duration: 2 minutes in seconds
    video_fps = 20  # Frames per second for video output
    record_frames = record_duration * video_fps  # Total frames for 2 minutes (2400 frames)
    
    # Since each frame takes longer (LLM calls, etc.), increase time limit
    # In test mode, frames are much faster (no LLM), so use shorter time limit
    if test_mode:
        actual_duration = record_duration * 2  # 4 minutes for test mode (faster frames)
        print(f"[TEST MODE] Enabled - Using random steering and speeds for fast testing")
        print(f"[TEST MODE] Time limit: {actual_duration} seconds (no LLM calls)")
    else:
        actual_duration = record_duration * 5  # 10 minutes = 600 seconds for normal mode
    
    # Check if dashboard recording is enabled via environment variable
    include_dashboard = os.environ.get("RECORD_DASHBOARD", "false").lower() == "true"
    dashboard_url = os.environ.get("DASHBOARD_URL", "http://localhost:4200")
    
    # Optional bounding box for dashboard window (left, top, right, bottom)
    # Format: "100,100,900,700" (example: captures window at position 100,100 with size 800x600)
    dashboard_bbox = None
    dashboard_bbox_str = os.environ.get("DASHBOARD_BBOX")
    if dashboard_bbox_str:
        try:
            dashboard_bbox = tuple(map(int, dashboard_bbox_str.split(',')))
            if len(dashboard_bbox) != 4:
                print(f"[Video] Warning: Invalid DASHBOARD_BBOX format, using full screen")
                dashboard_bbox = None
        except ValueError:
            print(f"[Video] Warning: Invalid DASHBOARD_BBOX format, using full screen")
            dashboard_bbox = None
    
    video_recorder = VideoRecorder(
        output_path="recordings", 
        fps=video_fps, 
        width=800, 
        height=600,
        include_dashboard=include_dashboard,
        dashboard_url=dashboard_url,
        dashboard_bbox=dashboard_bbox
    )
    video_recorder.start_recording()
    print(f"[Video] Recording started - will record for {record_duration} seconds ({record_frames} frames at {video_fps} FPS)")
    
    frame_count = 0
    # Use record_frames for 2 minutes, but allow override via environment
    # Default to 2400 frames (2 minutes at 20 FPS) if not specified
    max_frames_env = os.environ.get("MAX_FRAMES")
    if max_frames_env:
        max_frames = int(max_frames_env)
        if max_frames < record_frames:
            print(f"[INFO] MAX_FRAMES={max_frames} is less than 2 minutes ({record_frames} frames). Recording will be limited.")
    else:
        # Use full recording duration if MAX_FRAMES not set
        max_frames = record_frames
        print(f"[INFO] Using default MAX_FRAMES={max_frames} for full 2-minute recording")
    start_time = time.time()
    end_time = start_time + actual_duration  # Allow 10 minutes wall-clock for 2 minutes of simulation
    print(f"[Video] Time limit: {actual_duration} seconds (allowing for slow LLM/ML processing)")
    
    # Calculate frame interval: capture every Nth simulation frame to match video FPS
    # Simulation runs at 60 FPS (from clock.tick), video needs 20 FPS
    # So we capture every 3rd frame (60/20 = 3)
    simulation_fps = 60  # Pygame clock tick rate
    frame_skip = max(1, simulation_fps // video_fps)  # Capture every Nth frame
    print(f"[Video] Frame capture: Every {frame_skip} simulation frames (simulation: {simulation_fps} FPS, video: {video_fps} FPS)")

    while not done and frame_count < max_frames and time.time() < end_time:
        try:
            frame_count += 1
            print(f"\n=== Frame {frame_count}/{max_frames} ===")

            # Tick the simulation first
            world.tick()
            
            # Check for collisions
            collision_detected_this_frame = False
            try:
                collision_impulse = ego_vehicle.get_angular_velocity()
                angular_velocity_magnitude = (collision_impulse.x**2 + collision_impulse.y**2 + collision_impulse.z**2)**0.5
                
                # Also check linear velocity for sudden stops
                velocity = ego_vehicle.get_velocity()
                speed = (velocity.x**2 + velocity.y**2 + velocity.z**2)**0.5
                
                # Detect collisions based on sudden angular velocity or speed changes
                if angular_velocity_magnitude > 8.0:
                    collision_detected_this_frame = True
                    if not collision_detected:  # Only count once per collision event
                        collision_count += 1
                        collision_detected = True
                        print(f"WARNING: Collision #{collision_count} detected! Angular velocity: {angular_velocity_magnitude:.2f}")
                elif angular_velocity_magnitude < 3.0 and collision_detected:
                    # Reset collision flag when vehicle stabilizes
                    collision_detected = False
            except Exception as e:
                print(f"Warning: Error checking collision: {e}")
            
            # Track safe frames
            if not collision_detected_this_frame:
                safe_frames += 1

            # Check if test mode is enabled (random controls for fast testing)
            test_mode = os.environ.get("TEST_MODE", "false").lower() == "true"
            
            if test_mode:
                # Use random values for fast testing without LLM calls
                import random
                speed = random.uniform(3.0, 8.0)  # Random speed between 3-8 m/s
                steer = random.uniform(-0.8, 0.8)  # Random steering between -0.8 to 0.8
                print(f"[TEST MODE] Random controls: speed={speed:.2f} m/s, steer={steer:.2f}")
                text_of_audio = "Test mode: Random controls"
                text_of_scene = "Test mode: Random controls enabled"
            else:
                # Normal mode: use LLM and vision model
                # Choose a random audio command from audio_files directory if available
                try:
                    audio_dir = os.path.join(os.getcwd(), "audio_files")
                    # Supported audio extensions
                    patterns = ["*.mp3", "*.wav", "*.ogg", "*.flac", "*.m4a"]
                    candidates = []
                    if os.path.isdir(audio_dir):
                        for pattern in patterns:
                            candidates.extend(glob.glob(os.path.join(audio_dir, pattern)))

                    selected_audio_path = None
                    if candidates:
                        import random
                        selected_audio_path = random.choice(candidates)
                    else:
                        # Fallback to root audio.mp3 if directory is empty or missing
                        fallback = os.path.join(os.getcwd(), "audio.mp3")
                        if os.path.exists(fallback):
                            selected_audio_path = fallback

                    if selected_audio_path is None:
                        print("[Audio] No audio files found; converter will return mock text")
                        text_of_audio = convert("audio.mp3")
                    else:
                        print(f"[Audio] Using command file: {selected_audio_path}")
                        text_of_audio = convert(selected_audio_path)
                except Exception as e:
                    print(f"[Audio] Error selecting audio file: {e}. Falling back to default path")
                    text_of_audio = convert("audio.mp3")

                print(f"Audio text: {text_of_audio}")

                text_of_scene = camera_text_processing.get_scenario_from_image()
                print(f"Scene analysis: {text_of_scene}")

            # Capture frame for video recording (every Nth frame to match video FPS)
            # Note: frame_count starts at 1, so we check (frame_count - 1) % frame_skip == 0
            # This ensures we capture frames 1, 4, 7, 10... (every 3rd frame)
            if video_recorder.is_recording() and (frame_count - 1) % frame_skip == 0:
                try:
                    # Get the latest camera image
                    if hasattr(camera_text_processing, 'sensor_data') and 'rgb_image' in camera_text_processing.sensor_data:
                        image_data = camera_text_processing.sensor_data['rgb_image']
                        if image_data is not None and image_data.size > 0:
                            # Remove alpha channel if present
                            if len(image_data.shape) == 3 and image_data.shape[2] == 4:
                                image_rgb = image_data[:, :, :3]
                            else:
                                image_rgb = image_data
                            
                            # Debug: Check image properties
                            if frame_count == 1 or frame_count % 30 == 0:  # Log first frame and every 30 frames
                                print(f"[Video] Frame {frame_count}: Image shape={image_rgb.shape}, dtype={image_rgb.dtype}, min={image_rgb.min()}, max={image_rgb.max()}")
                            
                            video_recorder.add_frame(image_rgb)
                            if video_recorder.frame_count % 10 == 0:  # Log every 10 successfully written frames
                                print(f"[Video] Successfully captured {video_recorder.frame_count} frames for video")
                except Exception as e:
                    print(f"[Video] Warning: Could not capture frame: {e}")
                    import traceback
                    traceback.print_exc()

            # Get vehicle velocity and convert to m/s
            velocity = ego_vehicle.get_velocity()
            speed_mps = (velocity.x**2 + velocity.y**2 + velocity.z**2)**0.5
            
            # Get current steering angle
            current_control = ego_vehicle.get_control()
            steer_angle = current_control.steer

            # Make movements for ego vehicle
            if not test_mode:
                # Normal mode: use LLM for decision making
                speed, steer = text_to_instructions_converter.convert(text_of_audio, text_of_scene, speed_mps, steer_angle)
            # else: speed and steer are already set from random values above
            
            # Validate and clamp speed and steer values
            if not isinstance(speed, (int, float)) or speed < 0:
                print(f"Warning: Invalid speed value {speed}, using default 5.0")
                speed = 5.0
            if not isinstance(steer, (int, float)):
                print(f"Warning: Invalid steer value {steer}, using 0.0")
                steer = 0.0
            
            # Clamp steer to valid range [-1.0, 1.0]
            steer = max(-1.0, min(1.0, float(steer)))
            
            # Apply steering rate limiting to prevent abrupt changes
            steer_diff = steer - previous_steer
            if abs(steer_diff) > max_steer_change:
                steer = previous_steer + (max_steer_change if steer_diff > 0 else -max_steer_change)
                print(f"Steering rate limited: change from {previous_steer:.3f} to {steer:.3f}")
            
            # Reduce speed when steering is high (for safety)
            abs_steer = abs(steer)
            if abs_steer > 0.5:
                # Reduce speed proportionally for high steering
                speed_reduction = abs_steer * 2.0  # Reduce up to 2 m/s for full steering
                speed = max(3.0, speed - speed_reduction)  # Minimum speed of 3 m/s
                print(f"Speed reduced due to high steering: {speed:.2f} m/s")
            
            # Clamp speed to safe range
            speed = max(3.0, min(15.0, float(speed)))  # Between 3-15 m/s for urban driving
            
            previous_steer = steer
            
            print(f"Autopilot decision: speed={speed:.2f} m/s, steer={steer:.3f}")

            # Apply control with validated values - using ONLY ackermann_control (not apply_control)
            ego_vehicle.apply_ackermann_control(carla.VehicleAckermannControl(speed=float(speed), steer=float(steer)))
            
            # Send periodic updates to dashboard (every 5 frames)
            if frame_count % 5 == 0:
                # Calculate safe runs: total frames minus collisions
                # Each "run" represents 5 frames, so safe_runs = total safe frames / 5
                safe_runs = max(0, safe_frames // 5)  # Ensure non-negative
                send_to_dashboard(actual_map_name, collision_count, safe_runs)
                print(f"[Dashboard] Sent update: {collision_count} collisions, {safe_runs} safe runs (from {safe_frames} safe frames)")

            # Keep moving the spectator to keep up with ego vehicle
            try:
                spectator = world.get_spectator()
                transform = carla.Transform(
                    ego_vehicle.get_transform().transform(carla.Location(x=-4, z=2.5)),
                    ego_vehicle.get_transform().rotation,
                )
                spectator.set_transform(transform)
            except Exception as e:
                print(f"Warning: Failed to update spectator: {e}")

        except KeyboardInterrupt:
            print("\nSimulation interrupted by user")
            done = True
        except Exception as e:
            print(f"ERROR in simulation loop: {e}")
            import traceback
            traceback.print_exc()
            print("Continuing to next frame...")
            # Continue instead of breaking to see if it's recoverable

        # Update the display and check for the quit event
        try:
            pygame.display.flip()
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("[Simulation] Pygame window closed, stopping simulation")
                    done = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print("[Simulation] ESC key pressed, stopping simulation")
                        done = True
        except Exception as e:
            print(f"Warning: Pygame display error: {e}")
            # Don't stop simulation on pygame errors, just continue

        # Sleep to ensure consistent loop timing
        # Simulation runs at 60 FPS, we capture frames at video FPS (20 FPS) via frame_skip
        clock.tick(simulation_fps)  # Keep simulation at 60 FPS for smooth gameplay
    
    # Stop video recording
    if video_recorder.is_recording():
        video_file = video_recorder.stop_recording()
        if video_file:
            elapsed_time = time.time() - start_time
            print(f"[Video] Recording completed: {elapsed_time:.1f} seconds, {frame_count} frames")
            print(f"[Video] Video saved to: {video_file}")
    
    # Send final summary to dashboard
    print("\n" + "=" * 60)
    print("Simulation Summary:")
    print(f"Total Frames: {frame_count}")
    print(f"Collisions: {collision_count}")
    print(f"Safe Frames: {safe_frames}")
    elapsed_time = time.time() - start_time
    print(f"Duration: {elapsed_time:.1f} seconds")
    # Calculate final safe runs: total safe frames / 5 (each run = 5 frames)
    safe_runs = max(0, safe_frames // 5)  # Ensure non-negative
    print(f"Safe Runs: {safe_runs} (calculated from {safe_frames} safe frames)")
    print("=" * 60)
    
    # Send final data to dashboard
    send_to_dashboard(actual_map_name, collision_count, safe_runs)
    print(f"[Dashboard] Final update sent: {collision_count} collisions, {safe_runs} safe runs")
    
    # Cleanup: destroy camera sensor before exiting
    print("\nCleaning up resources...")
    try:
        if 'camera_text_processing' in locals() and hasattr(camera_text_processing, 'camera'):
            print("Destroying camera sensor...")
            camera_text_processing.camera.destroy()
    except Exception as e:
        print(f"Warning: Failed to destroy camera: {e}")
    
    # Cleanup: destroy actors
    try:
        if 'ego_vehicle' in locals() and ego_vehicle is not None:
            print("Destroying ego vehicle...")
            ego_vehicle.destroy()
    except Exception as e:
        print(f"Warning: Failed to destroy ego vehicle: {e}")
    
    try:
        if 'vehicle_bus' in locals() and vehicle_bus is not None:
            print("Destroying bus vehicle...")
            vehicle_bus.destroy()
    except Exception as e:
        print(f"Warning: Failed to destroy bus vehicle: {e}")
    
    print("Simulation completed successfully!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
