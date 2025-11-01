# CARLA will be imported after path setup in main script
import carla
import cv2
import numpy as np
try:
    from tensorflow import keras
    from custom_layers import Patches, PatchEncoder
    TF_AVAILABLE = True
except Exception as e:
    print(f"TensorFlow unavailable, vision model disabled: {e}")
    keras = None
    TF_AVAILABLE = False
    Patches = None
    PatchEncoder = None

# Load model with custom objects only if TensorFlow is available
if TF_AVAILABLE and keras is not None:
    try:
        model = keras.models.load_model(
            "vision_transformer_model/model/my_model.keras",
            custom_objects={'Patches': Patches, 'PatchEncoder': PatchEncoder}
        )
        print("Model loaded successfully")
    except Exception as e:
        print(f"Error loading model: {e}")
        model = None
else:
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
        # Get the latest image from sensor data
        if hasattr(self, 'sensor_data') and 'rgb_image' in self.sensor_data:
            image_data = self.sensor_data['rgb_image']
        elif self.current_image is not None:
            image_data = self.current_image
        else:
            return ""
        
        if model is not None and image_data is not None:
            # Convert image to the format expected by the model
            # Remove alpha channel and normalize
            img_rgb = image_data[:, :, :3]  # Remove alpha channel
            
            # Resize image to 224x224 as expected by the model
            img_resized = cv2.resize(img_rgb, (224, 224))
            
            img_normalized = img_resized.astype(np.float32) / 255.0
            img_batch = np.expand_dims(img_normalized, axis=0)  # Add batch dimension
            
            try:
                prediction = model.predict(img_batch, verbose=0)
                # Convert prediction to text string description
                if isinstance(prediction, np.ndarray):
                    pred_array = prediction[0] if prediction.ndim > 1 else prediction
                    
                    # If prediction is a probability distribution or embeddings
                    # Create a descriptive text based on the values
                    if len(pred_array) > 1:
                        # Get the top elements (most significant features)
                        top_indices = np.argsort(pred_array)[-3:][::-1]  # Top 3
                        descriptions = []
                        scene_labels = [
                            "road ahead clear", "vehicles nearby", "obstacles detected",
                            "lane markings visible", "traffic signs present", "pedestrians nearby",
                            "intersection ahead", "curved road", "straight road", "construction zone"
                        ]
                        
                        for idx in top_indices:
                            if idx < len(scene_labels):
                                confidence = pred_array[idx]
                                if confidence > 0.05:  # Threshold for significant detection
                                    descriptions.append(f"{scene_labels[idx]} (confidence: {confidence:.2f})")
                        
                        if descriptions:
                            scenario_text = "Scene contains: " + ", ".join(descriptions)
                        else:
                            scenario_text = "Scene analyzed: road conditions normal"
                    else:
                        scenario_text = f"Scene analyzed: prediction value {pred_array}"
                else:
                    scenario_text = str(prediction)
                return scenario_text
            except Exception as e:
                print(f"Error predicting scenario: {e}")
                import traceback
                traceback.print_exc()
                return "Scene analysis unavailable"
        else:
            return ""
