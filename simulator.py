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
    # Add CARLA Python API to path
    carla_path = r"C:\Users\sumuk\Documents - Copy\CARLA_Latest\PythonAPI\carla\dist\carla-0.9.16-py3.12-win-amd64.egg"
    if os.path.exists(carla_path):
        sys.path.append(carla_path)
        print(f"Found CARLA at: {carla_path}")
    else:
        print(f"CARLA not found at: {carla_path}")
        print("Please ensure CARLA is properly installed")
        sys.exit(1)
    
    # Import CARLA after adding to path
    import carla
    print("Using real CARLA module")

    # server running on our system with configurable host and port
    carla_host = os.environ.get("CARLA_HOST", "localhost")
    carla_port = int(os.environ.get("CARLA_PORT", "2000"))
    carla_timeout = float(os.environ.get("CARLA_TIMEOUT", "5.0"))
    
    client = carla.Client(carla_host, carla_port)
    client.set_timeout(carla_timeout)

    world = client.load_world("Town03")
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
    ego_vehicle = world.try_spawn_actor(vehicle_bp, spawn_points[79])

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
        frame_count += 1
        print(f"Frame {frame_count}: Processing autopilot...")

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
        print(f"Autopilot decision: speed={speed}, steer={steer}")

        ego_vehicle.apply_ackermann_control(carla.VehicleAckermannControl(speed=speed, steer=steer))

        # keep moving the spectator to keep up with ego vehicle
        spectator = world.get_spectator()
        transform = carla.Transform(
            ego_vehicle.get_transform().transform(carla.Location(x=-4, z=2.5)),
            ego_vehicle.get_transform().rotation,
        )
        spectator.set_transform(transform)

        # Update the display and check for the quit event
        pygame.display.flip()
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

        # Sleep to ensure consistent loop timing
        clock.tick(60)

if __name__ == "__main__":
    main()
