import carla
import cv2
import numpy as np


class cameraTextProcessing:
    def __init__(self, camera_bp, ego_vehicle, bp_lib, world):
        self.ego_vehicle = ego_vehicle
        self.camera_bp = camera_bp
        self.bp_lib = bp_lib
        self.world = world

    def initialCamera(self):
        camera_bp = self.bp_lib.find("sensor.camera.rgb")
        camera_init_trans = carla.Transform(carla.Location(x=-0.1, z=1.7))
        camera = self.world.spawn_actor(
            camera_bp, camera_init_trans, attach_to=self.ego_vehicle
        )

        image_w = self.camera_bp.get_attribute("image_size_x").as_int()
        image_h = self.camera_bp.get_attribute("image_size_y").as_int()

        sensor_data = {"rgb_image": np.zeros((image_h, image_w, 4))}

        camera.listen(lambda image: self.rgb_callback(image, sensor_data))

        while True:
            # Output camera display onto an OpenCV Window
            cv2.imshow("RGB_Image", sensor_data["rgb_image"])
            if cv2.waitKey(1) == ord("q"):
                break

    def rgb_callback(image, data_dict):
        img = np.reshape(
            np.copy(image.raw_data), (image.height, image.width, 4)
        )  # Reshaping with alpha channel
        img[:, :, 3] = 255  # Setting the alpha to 255
        data_dict["rgb_image"] = img
