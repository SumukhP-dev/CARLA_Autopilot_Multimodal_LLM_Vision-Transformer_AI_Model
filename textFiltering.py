class textFiltering:
    def __init__(self):
        self.acceleration = 0
        self.left = False
        self.right = False
        self.stop = False

    def filterResponse(self, response):
        self.acceleration = 0
        self.left = False
        self.right = False
        self.stop = False

        filtered_response_start = response.rfind("")
        filtered_response = response[filtered_response_start:]

        filtered_response_action_start = filtered_response.find("**")
        filtered_response_action = filtered_response[
            filtered_response_action_start + 2 :
        ]

        filtered_response_action_end = filtered_response_action.find("**")
        filtered_response_action = filtered_response_action[
            0:filtered_response_action_end
        ]

        filtered_response_action_list = filtered_response_action.split("and")

        for item in filtered_response_action_list:
            if "left" or "merge" or "pass" in item:
                self.left = True
            if "right" in item:
                self.right = True
            if "stop" or "yield" or "wait" in item:
                self.stop = True

        # print("filtered_response_action: ", filtered_response_action)

        return self.acceleration, self.left, self.right, self.stop
