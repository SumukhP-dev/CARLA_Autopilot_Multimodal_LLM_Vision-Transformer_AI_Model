# CARLA will be imported after path setup in main script
import carla
import cv2
import numpy as np
from tensorflow import keras
from custom_layers import Patches, PatchEncoder

# Load model with custom objects
try:
    model = keras.models.load_model(
        "vision_transformer_model/model/my_model.keras",
        custom_objects={'Patches': Patches, 'PatchEncoder': PatchEncoder}
    )
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

def rgb_callback(image, data_dict):
    import carla  # Import here after path setup
    img = np.reshape(
        np.copy(image.raw_data), (image.height, image.width, 4)
    )  # Reshaping with alpha channel
    img[:, :, 3] = 255  # Setting the alpha to 255
    data_dict["rgb_image"] = img


class CameraTextProcessing:
    def __init__(self, camera_bp, ego_vehicle, bp_lib, world):
        self.ego_vehicle = ego_vehicle
        self.camera_bp = camera_bp
        self.bp_lib = bp_lib
        self.world = world
        self.current_image = None

    def initial_camera(self):
        camera_bp = self.bp_lib.find("sensor.camera.rgb")
        camera_init_trans = carla.Transform(carla.Location(x=-0.1, z=1.7))
        camera = self.world.spawn_actor(
            camera_bp, camera_init_trans, attach_to=self.ego_vehicle
        )

        image_w = self.camera_bp.get_attribute("image_size_x").as_int()
        image_h = self.camera_bp.get_attribute("image_size_y").as_int()

        sensor_data = {"rgb_image": np.zeros((image_h, image_w, 4))}

        camera.listen(lambda image: rgb_callback(image, sensor_data))
        
        # Store sensor data for later use
        self.sensor_data = sensor_data
        self.camera = camera
        
        # Initialize with a mock image for testing
        self.current_image = np.zeros((image_h, image_w, 4), dtype=np.uint8)
        print("Camera initialized successfully")

    def get_scenario_from_image(self):
        if self.current_image is not None and model is not None:
            # Convert image to the format expected by the model
            # Remove alpha channel and normalize
            img_rgb = self.current_image[:, :, :3]  # Remove alpha channel
            
            # Resize image to 224x224 as expected by the model
            img_resized = cv2.resize(img_rgb, (224, 224))
            
            img_normalized = img_resized.astype(np.float32) / 255.0
            img_batch = np.expand_dims(img_normalized, axis=0)  # Add batch dimension
            
            try:
                scenario = model.predict(img_batch, verbose=0)
                return scenario
            except Exception as e:
                print(f"Error predicting scenario: {e}")
                return ""
        else:
            return ""
