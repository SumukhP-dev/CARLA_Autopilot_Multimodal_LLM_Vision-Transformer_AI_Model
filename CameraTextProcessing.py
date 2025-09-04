import carla
import cv2
import numpy as np
from tensorflow import keras

model = keras.models.load_model("vision_transformer_model/model/my_model.keras")

def rgb_callback(image, data_dict):
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

        while True:
            # Output camera display onto an OpenCV Window
            cv2.imshow("RGB_Image", sensor_data["rgb_image"])
            self.current_image = sensor_data["rgb_image"]
            if cv2.waitKey(1) == ord("q"):
                break

    def get_scenario_from_image(self):
        if self.current_image is None:
            image_bytes = self.current_image.tobytes()

            scenario = model.predict(image_bytes)

            return scenario
        else:
            return ""
