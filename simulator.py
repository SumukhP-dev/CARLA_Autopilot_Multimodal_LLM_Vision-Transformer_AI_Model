import glob
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import pygame  # We will be using this for manual control

from audio_conversion import convert
from camera_text_processing import CameraTextProcessing
from player import Player
from text_to_instructions_converter import TextToInstructionsConverter

def main():
    print("=" * 60)
    print("CARLA Autopilot Simulator - Starting...")
    print("=" * 60)
    
    # Add CARLA Python API to path
    carla_path = r"C:\Users\sumuk\Documents - Copy\CARLA_Latest\PythonAPI\carla\dist\carla-0.9.16-py3.12-win-amd64.egg"
    if os.path.exists(carla_path):
        sys.path.append(carla_path)
        print(f"[OK] Found CARLA at: {carla_path}")
    else:
        print(f"[ERROR] CARLA not found at: {carla_path}")
        print("Please ensure CARLA is properly installed")
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
    
    # Get world - try existing first, then load if needed
    try:
        world = client.get_world()
        print(f"Connected to existing world: {world}")
    except RuntimeError:
        print("No existing world found, loading Town03...")
        try:
            world = client.load_world("Town03")
            print(f"Successfully loaded world: {world}")
        except RuntimeError as e:
            print(f"ERROR: Could not connect to CARLA server: {e}")
            print("\nPlease make sure:")
            print("1. CARLA server is running (CarlaUE4.exe)")
            print(f"2. CARLA server is accessible at {carla_host}:{carla_port}")
            print("3. CARLA server has finished loading the map")
            sys.exit(1)
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
    ego_vehicle.apply_ackermann_control(carla.VehicleAckermannControl(speed=5, steer=0.0))

    pygame.init()  # initialising

    # Set up the Pygame display
    size = (640, 480)
    pygame.display.set_caption("CARLA Manual Control")
    screen = pygame.display.set_mode(size)

    # Set up the control object and loop until the user exits the script
    control = ego_vehicle.get_control()
    clock = pygame.time.Clock()
    done = False
    
    # Get target speed from environment
    target_speed = float(os.environ.get("TARGET_SPEED", "5.0"))

    # Find a camera blueprint
    camera_bp = bp_lib.find('sensor.camera.rgb')

    player = Player(world, ego_vehicle)
    
    # Initialize camera processing once
    camera_text_processing = CameraTextProcessing(camera_bp, ego_vehicle, bp_lib, world)
    camera_text_processing.initial_camera()
    
    # Initialize text converter once
    text_to_instructions_converter = TextToInstructionsConverter()
    
    print("Starting autopilot simulation...")
    print("Note: Using mock CARLA - all AI logic is working, just no visual window")
    frame_count = 0
    max_frames = int(os.environ.get("MAX_FRAMES", "20"))  # Configurable frame limit

    while not done and frame_count < max_frames:
        try:
            frame_count += 1
            print(f"\n=== Frame {frame_count}/{max_frames} ===")

            # Apply the control to the ego vehicle and tick the simulation
            ego_vehicle.apply_control(control)
            world.tick()

            text_of_audio = convert("audio.mp3")
            print(f"Audio text: {text_of_audio}")

            text_of_scene = camera_text_processing.get_scenario_from_image()
            print(f"Scene analysis: {text_of_scene}")

            # Get vehicle velocity and convert to m/s
            velocity = ego_vehicle.get_velocity()
            speed_mps = (velocity.x**2 + velocity.y**2 + velocity.z**2)**0.5
            
            # Get current steering angle
            steer_angle = ego_vehicle.get_control().steer

            # Make movements for ego vehicle
            speed, steer = text_to_instructions_converter.convert(text_of_audio, text_of_scene, speed_mps, steer_angle)
            
            # Validate and clamp speed and steer values
            if not isinstance(speed, (int, float)) or speed < 0:
                print(f"Warning: Invalid speed value {speed}, using default 5.0")
                speed = 5.0
            if not isinstance(steer, (int, float)):
                print(f"Warning: Invalid steer value {steer}, using 0.0")
                steer = 0.0
            # Clamp steer to valid range [-1.0, 1.0]
            steer = max(-1.0, min(1.0, float(steer)))
            
            print(f"Autopilot decision: speed={speed:.2f} m/s, steer={steer:.3f}")

            # Apply control with validated values
            ego_vehicle.apply_ackermann_control(carla.VehicleAckermannControl(speed=float(speed), steer=float(steer)))

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
                    done = True
        except Exception as e:
            print(f"Warning: Pygame display error: {e}")

        # Sleep to ensure consistent loop timing
        clock.tick(60)
    
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
