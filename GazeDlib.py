import tkinter
import customtkinter
from pygrabber.dshow_graph import FilterGraph  #pip install pygrabber
import cv2
from PIL import Image
import time
import dlib
import numpy as np
from scipy.spatial import distance as dist
#from pyuac import main_requires_admin
import string
import win32api
import win32con


class GazeDlib(customtkinter.CTkFrame):

    frames = {"gaze_dlib": None}
    self_frame = None

    def __init__(self, master, controller):
        super().__init__(master)
        BUTTON_PADDING_X = 10
        BUTTON_PADDING_Y = 5
        BUTTON_PADDING_FIRST_LAST_Y = 10
        SMALL_FONT_SIZE = 12
        self.CAMERA_LIST = FilterGraph().get_input_devices()
        self.tracking_enabled = False
        self.time_since_last_click = 0
        self.cx, self.cy = 0, 0

        self.controller = controller

        self.frames['gaze_dlib'] = customtkinter.CTkFrame(master=master, fg_color="transparent")
        self.self_frame = self.frames['gaze_dlib']

        
        ########## View Frame ##########
        self.self_frame.view_frame = customtkinter.CTkFrame(self.self_frame, height=540, width=720)
        self.self_frame.view_frame.grid(row=1, column=1, padx=(10, 10), pady=(10, 0), sticky="nsew")

        ########## Details Frame ##########
        self.self_frame.details_frame = customtkinter.CTkFrame(self.self_frame, height=0)
        self.self_frame.details_frame.grid(row=2, column=1, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.self_frame.view_details_fps = customtkinter.CTkLabel(self.self_frame.details_frame,
                                                       text="Video FPS: ")
        self.self_frame.view_details_fps.grid(row=1, column=1, padx=(10,10), pady=(10, 10))


        ########## View Settings Frame ##########
        self.self_frame.view_settings_frame = customtkinter.CTkFrame(self.self_frame)
        self.self_frame.view_settings_frame.grid(row=1, column=2, padx=(10, 10), pady=(10, 0), sticky="nsew")

        # view settings title
        self.view_settings_title = customtkinter.CTkLabel(self.self_frame.view_settings_frame, 
                                                 text="View\nConfiguration", 
                                                 font=customtkinter.CTkFont(size=16, weight="bold", family="Roboto Mono"))
        self.view_settings_title.grid(row=0, column=2, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_Y)


        # Camera Select
        self.camera_label = customtkinter.CTkLabel(self.self_frame.view_settings_frame, text="Camera Select:", 
                                                 font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.camera_label.grid(row=1, column=2, padx=BUTTON_PADDING_X, pady=(0,0))
        self.self_frame.camera_optionmenu = customtkinter.CTkOptionMenu(self.self_frame.view_settings_frame, 
                                                             dynamic_resizing=False,
                                                             values=self.CAMERA_LIST)
        self.self_frame.camera_optionmenu.grid(row=2, column=2, padx=BUTTON_PADDING_X, pady=(0, BUTTON_PADDING_Y))


        # Action Select Pose
        self.self_frame.action_label = customtkinter.CTkLabel(self.self_frame.view_settings_frame, text="Gaze Action:", 
                                                 font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.action_label.grid(row=3, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y,0))
        self.self_frame.action_optionmenu = customtkinter.CTkOptionMenu(self.self_frame.view_settings_frame, 
                                                             dynamic_resizing=False,
                                                             values=["None", "Mouse", "WASD", "Arrow"])
        self.self_frame.action_optionmenu.grid(row=4, column=2, padx=BUTTON_PADDING_X, pady=(0, BUTTON_PADDING_Y))
        
        
        # Blink Action
        key_values = np.array(["None", "Left Click", "Right Click", "Spacebar"])
        key_values = np.concatenate((key_values, list(string.ascii_lowercase)))
        self.self_frame.action_blink_label = customtkinter.CTkLabel(self.self_frame.view_settings_frame, text="Blink Action:", 
                                                 font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.action_blink_label.grid(row=5, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y,0))
        self.self_frame.action_blink_optionmenu = customtkinter.CTkOptionMenu(self.self_frame.view_settings_frame, 
                                                             dynamic_resizing=False, values=key_values)
        self.self_frame.action_blink_optionmenu.grid(row=6, column=2, padx=BUTTON_PADDING_X, pady=(0, BUTTON_PADDING_Y))


        # Mouse Movement Multiplier
        verify_float_input = (self.register(self.verify_float))
        self.self_frame.mouse_multiplier_label = customtkinter.CTkLabel(self.self_frame.view_settings_frame, text="Mouse Speed:", 
                                                 font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.mouse_multiplier_label.grid(row=11, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y,0))
        self.self_frame.mouse_multiplier_entry = customtkinter.CTkEntry(self.self_frame.view_settings_frame, placeholder_text="0.3",
                                                                validate='all', validatecommand=(verify_float_input, '%P'))
        self.self_frame.mouse_multiplier_entry.grid(row=12, column=2, padx=BUTTON_PADDING_X, pady=(0, BUTTON_PADDING_Y))
        
        
        # Threshold
        verify_digit_input = (self.register(self.verify_digit))
        self.self_frame.threshold_label = customtkinter.CTkLabel(self.self_frame.view_settings_frame, text="Eye Threshold (0-225):", 
                                                 font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.threshold_label.grid(row=13, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y,0))
        self.self_frame.threshold_entry = customtkinter.CTkEntry(self.self_frame.view_settings_frame, placeholder_text="127", 
                                                                validate='all', validatecommand=(verify_digit_input, '%P'))
        self.self_frame.threshold_entry.grid(row=14, column=2, padx=BUTTON_PADDING_X, pady=(0, BUTTON_PADDING_Y))
        
        
        # EAR Threshold
        self.self_frame.ear_threshold_label = customtkinter.CTkLabel(self.self_frame.view_settings_frame, text="EAR Threshold:", 
                                                 font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.ear_threshold_label.grid(row=15, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y,0))
        self.self_frame.ear_threshold_entry = customtkinter.CTkEntry(self.self_frame.view_settings_frame, placeholder_text="0.45", 
                                                                validate='all', validatecommand=(verify_float_input, '%P'))
        self.self_frame.ear_threshold_entry.grid(row=16, column=2, padx=BUTTON_PADDING_X, pady=(0, BUTTON_PADDING_FIRST_LAST_Y))
    
    
        # Horizontal Flip Switch
        self.self_frame.horizontal_switch = customtkinter.CTkSwitch(self.self_frame.view_settings_frame, text="Horizontal Flip",
                                                                    font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.horizontal_switch.grid(row=17, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y, BUTTON_PADDING_Y))

        # Vertical Flip Switch
        self.self_frame.vertical_switch = customtkinter.CTkSwitch(self.self_frame.view_settings_frame, text=" Vertical Flip ",
                                                                  font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.vertical_switch.grid(row=18, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y, BUTTON_PADDING_Y))


        # Activate / Deactive Button Frame
        self.self_frame.activate_button_frame = customtkinter.CTkFrame(self.self_frame, fg_color="transparent")
        self.self_frame.activate_button_frame.grid(row=2, column=2, padx=(10, 10), pady=(10, 10), sticky="nsew")

        # Activate Button
        self.self_frame.view_settings_activate = customtkinter.CTkButton(self.self_frame.activate_button_frame, 
                                                              text="Activate", 
                                                              command=self.activate_tracking_event,
                                                              fg_color="#4F7942",
                                                              hover_color="#355E3B",
                                                              width=72,
                                                              height=48)
        self.self_frame.view_settings_activate.grid(row = 1, column=1, padx=(0, 5), pady=(0, 0))

        # Deactivate Button
        self.self_frame.view_settings_deactivate = customtkinter.CTkButton(self.self_frame.activate_button_frame, 
                                                                text="Deactivate", 
                                                                command=self.deactivate_tracking_event, 
                                                                state="disabled",
                                                                fg_color="#D22B2B",
                                                                hover_color="#A52A2A",
                                                                width=72,
                                                                height=48)
        self.self_frame.view_settings_deactivate.grid(row = 1, column=2, padx=(5, 0), pady=(0, 0))


        ##### WEBCAM TRACKING STUFF ######
        # self.gaze = GazeTracking()
        # self.webcam = cv2.VideoCapture(2)
        # self.lmain = customtkinter.CTkLabel(master=self.view_frame, text="")
        # self.lmain.grid(row=0, column=0)
        # self.show_frame()
        ##################################


    def camera_view_setup(self):
        if self.tracking_enabled:
            print("Dlib Tracking Enabled")
            camera_index = self.find_camera(self.self_frame.camera_optionmenu.get(), self.CAMERA_LIST)
            self.cap = cv2.VideoCapture(camera_index)
            self.lmain = customtkinter.CTkLabel(master=self.self_frame.view_frame, text="")
            self.lmain.grid(row=0, column=0)
            self.ear = 0
        else:
            camera_index, self.cap, self.lmain = None, None, None
            print("Dlib Tracking Disabled")

    def find_camera(self, value, list):
        index = 0
        for i in range(len(list)):
            if value == list[i]:
                return i
        return index


    def apply_event(self):
        self.camera_view_setup()
        self.track_eyes()

    def activate_tracking_event(self):
        self.tracking_enabled = True
        self.apply_event()
        self.self_frame.view_settings_activate.configure(state="disabled")
        self.self_frame.view_settings_deactivate.configure(state="enabled")

    def deactivate_tracking_event(self):
        self.tracking_enabled = False
        self.apply_event()
        self.self_frame.view_settings_activate.configure(state="enabled")
        self.self_frame.view_settings_deactivate.configure(state="disabled")


    prev_frame_time = 0
    new_frame_time = 0
    start_time = time.time()
    time_diff = 0

    def calculate_video_stats(self):
        self.new_frame_time = time.time()
        fps = 1/(self.new_frame_time- self.prev_frame_time)
        self.prev_frame_time = self.new_frame_time
        fps = round(fps, 2)
        self.time_diff = self.new_frame_time - self.start_time
        gaze_string = str(self.detect_gaze(self.ear, self.ear_threshold)[0]) + " " + str(self.detect_gaze(self.ear, self.ear_threshold)[1])
        self.self_frame.view_details_fps.configure(text=("Video FPS: " + str(fps) + " | Gaze: " + gaze_string))




    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor('./models/shape_predictor_68_face_landmarks.dat')
    left = [36, 37, 38, 39, 40, 41]
    right = [42, 43, 44, 45, 46, 47]
    
    def np_shape(self, shape):
        points = np.zeros((68, 2), dtype="int")
        for i in range(0, 68):
            points[i] = (shape.part(i).x, shape.part(i).y)
        return points

    def eye_on_mask(self, mask, side):
        points = [self.shape_array[i] for i in side]
        points = np.array(points, dtype=np.int32)
        mask = cv2.fillConvexPoly(mask, points, 255)
        return mask

    def calculate_centre(self, threshold, mid_x, right):
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        try:
            contour = max(contours, key=cv2.contourArea)
            M = cv2.moments(contour)
            self.cx = int(M['m10']/M['m00'])
            self.cy = int(M['m01']/M['m00'])
            if right:
                self.cx = int(M['m10']/M['m00']) + mid_x
            return self.cx, self.cy
        except:
            pass

    
    def track_eyes(self):
        if not self.tracking_enabled:
            cv2.destroyAllWindows()
            return
        
        flip_horizontal = self.self_frame.horizontal_switch.get()
        flip_vertical = self.self_frame.vertical_switch.get()
        
        self.eye_threshold = self.self_frame.threshold_entry.get()
        self.ear_threshold = self.self_frame.ear_threshold_entry.get()
        mode = self.self_frame.action_optionmenu.get()
        self.mouse_multiplier = self.self_frame.mouse_multiplier_entry.get()
        
        action_blink = self.self_frame.action_blink_optionmenu.get().lower()
        is_blink_key =  action_blink != "none" and action_blink != "left click" and action_blink !=  "right click"
        is_blink_mouse = action_blink == "left click" or action_blink ==  "right click"
        
        
        try:
            self.eye_threshold = int(self.eye_threshold)
        except:
            self.eye_threshold = int(127)
            
        try:
            self.ear_threshold = float(self.ear_threshold)
        except:
            self.ear_threshold = float(0.45)
            
        try:
            self.mouse_multiplier = float(self.mouse_multiplier)
        except:
            self.mouse_multiplier = float(1)

        self.calculate_video_stats()

        _, img = self.cap.read()        
        threshold_img = img.copy()
        
        if flip_horizontal:
            img = cv2.flip(img, 1)
        if flip_vertical:
            img = cv2.flip(img, 0)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        detections = self.detector(gray, 1)
        
        for detection in detections:
            shape = self.predictor(gray, detection)
            self.shape_array = self.np_shape(shape)

            mask = np.zeros(img.shape[:2], dtype=np.uint8)
            mask = self.eye_on_mask(mask, self.left)
            mask = self.eye_on_mask(mask, self.right)
            mask = cv2.dilate(mask, np.ones((9, 9)), 5)
            eyes = cv2.bitwise_and(img, img, mask=mask)

            mask = (eyes == [0, 0, 0]).all(axis=2)
            eyes[mask] = [255, 255, 255]
            mid_x = (self.shape_array[42][0] + self.shape_array[39][0]) // 2

            try:
                _, threshold_img = cv2.threshold(cv2.cvtColor(eyes, cv2.COLOR_BGR2GRAY), self.eye_threshold, 255, cv2.THRESH_BINARY)
                threshold_img = cv2.erode(threshold_img, None, iterations=2)
                threshold_img = cv2.dilate(threshold_img, None, iterations=4)
                threshold_img = cv2.medianBlur(threshold_img, 3)
                threshold_img = cv2.bitwise_not(threshold_img)
                
                cx_left, cy_left = self.calculate_centre(threshold_img[:, 0:mid_x], mid_x, False)
                cv2.circle(img, (cx_left, cy_left), 4, (0, 0, 255), 2)

                cx_right, cy_right = self.calculate_centre(threshold_img[:, mid_x:], mid_x, True)
                cv2.circle(img, (cx_right, cy_right), 4, (0, 0, 255), 2)
                cv2.imshow("image", threshold_img)
            except:
                print("could not calculate iris")


            for (x, y) in self.shape_array[36:48]:
                    cv2.circle(img, (x, y), 2, (255, 0, 0), -1)
                    
            for (x, y) in self.shape_array[42:43]:
                cv2.circle(img, (x,y), 2, (0, 255, 0), -1)
            for (x, y) in self.shape_array[45:46]:
                cv2.circle(img, (x,y), 2, (0, 255, 0), -1)

            for (x, y) in self.shape_array[44:45]:
                cv2.circle(img, (x,y), 2, (0, 255, 0), -1)
            for (x, y) in self.shape_array[46:47]:
                cv2.circle(img, (x,y), 2, (0, 255, 0), -1)

            for (x, y) in self.shape_array[33:34]:
                cv2.circle(img, (x,y), 2, (127, 255, 127), -1)

            self.ear = self.eye_aspect_ratio(shape=self.shape_array)
            gaze = self.detect_gaze(self.ear, self.ear_threshold)
            print(gaze)
            
            if gaze[0] != "Blinking":
                if mode == "Mouse":
                    self.mouse_mode(gaze[0], gaze[1], mouse_multiplier=self.mouse_multiplier)
                elif mode == "WASD":
                    self.wasd_mode(gaze[0], gaze[1])
                elif mode == "Arrow":
                    self.arrow_mode(gaze[0], gaze[1])
            
            if is_blink_key and action_blink != "none":
                self.action_hold_key(gaze[0] != "Blinking", action_blink)
            if is_blink_mouse and action_blink != "none":
                self.action_mouse_click(gaze[0] != "Blinking", action_blink, self.time_since_last_click)
            
        rgba_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        imgtk = customtkinter.CTkImage(Image.fromarray(rgba_img), size=(720,540))
        self.lmain.imgtk = imgtk
        self.lmain.configure(image=imgtk)
        self.lmain.after(10, self.track_eyes)


    def eye_aspect_ratio(self, shape):
        y1_right = dist.euclidean(shape[43], shape[47])
        y2_right = dist.euclidean(shape[44], shape[46])
        x_right = dist.euclidean(shape[42], shape[45])
        ratio_right = (y1_right + y2_right) / x_right

        y1_left = dist.euclidean(shape[37], shape[41])
        y2_left = dist.euclidean(shape[38], shape[40])
        x_left = dist.euclidean(shape[37], shape[39])
        ratio_left = (y1_left + y2_left) / x_left
        
        return (ratio_right + ratio_left) / 2
    
    
    def detect_gaze(self, ear, ear_threshold=0.45):
        if ear < self.ear_threshold:
            return ("Blinking", "", ear)
        else:
            self.horizontal_gaze = ""
            horizontal_gaze_threshold = 5
            if((self.cx - self.shape_array[42][0]) - (self.shape_array[45][0] - self.cx) > horizontal_gaze_threshold):
                self.horizontal_gaze = "Right"
            elif((self.cx - self.shape_array[42][0]) - (self.shape_array[45][0] - self.cx) < -horizontal_gaze_threshold):
                self.horizontal_gaze = "Left"
            else:
                self.horizontal_gaze = "Forward"

            self.vertical_gaze = ""
            # vertical_gaze_threshold = 10
            # if((self.cx - self.shape[44][0]) - (self.shape[46][0] - self.cx) > vertical_gaze_threshold):
            #     vertical_gaze = "up"
            # elif((self.cx - self.shape[44][0]) - (self.shape[46][0] - self.cx) < -vertical_gaze_threshold):
            #     vertical_gaze = "down"
            # else:
            #     vertical_gaze = "center"

            if ear > (ear_threshold+0.28):
                self.vertical_gaze = "Up"
            elif ear < (ear_threshold+0.12):
                self.vertical_gaze = "Down"
            else:
                self.vertical_gaze = "Centre"
            return (self.vertical_gaze, self.horizontal_gaze, ear)
        
        
    def verify_float(self, x):
        if len(x) > 0 and x[len(x)-1] == " ":
            return False
        if x == " ":
            return False
        if x == "":
            return True
        try:
            x = float(x)
            return True
        except:
            return False
    
    def verify_float_input(self, x):
        print(x)
        if self.verify_float(x) and x == "":
            return 0
        return float(x)
    
    def verify_digit(self, x):
        if len(x) > 0 and x[len(x)-1] == " ":
            return False
        if x == "":
            return True
        try:
            x = int(x)
            if x > 255 or x < 0:
                return False
            return True
        except:
            return False
        
    def verify_offset_input(self, x):
        if self.verify_digit(x) or x == "":
            return 0
        return int(x)
    
    
    def mouse_mode(self, gaze_y, gaze_x, mouse_multiplier):
        """Move mouse if x and y values are outside a deadzone

        Args:
            x (float): Pose direction in x-axis
            y (float): Pose direction in y-axis
            deadzone (float): Deadzone which x or y must cross to activate mouse movement
            multiplier (float): Multiplier to increase mouse movement speed
        """
        print(gaze_y, gaze_x)
        pos = win32api.GetCursorPos()        
        if gaze_x == "Left":
            print(pos[0] - (1*mouse_multiplier))
            win32api.SetCursorPos((int(pos[0] - (10*mouse_multiplier)), int(pos[1])))
        elif gaze_x == "Right":
            print(pos[0] + (1*mouse_multiplier))
            win32api.SetCursorPos((int(pos[0] + (10*mouse_multiplier)), int(pos[1])))

        pos = win32api.GetCursorPos()        
        if gaze_y == "Down":
            print(pos[1] - (1*mouse_multiplier))
            win32api.SetCursorPos((int(pos[0]), int(pos[1] + (10*mouse_multiplier))))
        elif gaze_y == "Up":
            print(pos[1] + (1*mouse_multiplier))
            win32api.SetCursorPos((int(pos[0]), int(pos[1] - (10*mouse_multiplier))))


    def wasd_mode(self, gaze_y, gaze_x):
        """Press WASD keys if x and y values are outside a deadzone

        Args:
            x (float): Pose direction in x-axis
            y (float): Pose direction in y-axis
            deadzone (float): Deadzone which x or y must cross to activate arrow key press
        """
        if gaze_x == "Left":
            win32api.keybd_event(self.KEY_CODE['a'], 0, 0, 0)
        elif gaze_x == "Right":
            win32api.keybd_event(self.KEY_CODE['d'], 0, 0, 0)
        else:
            win32api.keybd_event(self.KEY_CODE['a'], 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(self.KEY_CODE['d'], 0, win32con.KEYEVENTF_KEYUP, 0)
        
        if gaze_y == "Down":
            win32api.keybd_event(self.KEY_CODE['s'], 0, 0, 0)
        elif gaze_y == "Up":
            win32api.keybd_event(self.KEY_CODE['w'], 0, 0, 0)
        else:
            win32api.keybd_event(self.KEY_CODE['s'], 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(self.KEY_CODE['w'], 0, win32con.KEYEVENTF_KEYUP, 0)


    def arrow_mode(self, gaze_y, gaze_x):
        """Press arrow keys if x and y values are outside a deadzone

        Args:
            x (float): Pose direction in x-axis
            y (float): Pose direction in y-axis
            deadzone (float): Deadzone which x or y must cross to activate arrow key press
        """
        if gaze_x == "Left":
            win32api.keybd_event(self.KEY_CODE['left_arrow'], 0, 0, 0)
        elif gaze_x == "Right":
            win32api.keybd_event(self.KEY_CODE['right_arrow'], 0, 0, 0)
        else:
            win32api.keybd_event(self.KEY_CODE['left_arrow'], 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(self.KEY_CODE['right_arrow'], 0, win32con.KEYEVENTF_KEYUP, 0)
        
        if gaze_y == "Down":
            win32api.keybd_event(self.KEY_CODE['down_arrow'], 0, 0, 0)
        elif gaze_y == "Up":
            win32api.keybd_event(self.KEY_CODE['up_arrow'], 0, 0, 0)
        else:
            win32api.keybd_event(self.KEY_CODE['down_arrow'], 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(self.KEY_CODE['up_arrow'], 0, win32con.KEYEVENTF_KEYUP, 0)
            
            
    def action_hold_key(self, is_blinking, key):
        """Hold key while condition is met

        Args:
            is_blinking (bool): Check if user is blinking
            key (string): Input key string folllowing "Windows Virtual-Key Codes"
        """
        if is_blinking:
            win32api.keybd_event(self.KEY_CODE[key], 0, 0, 0)
        else:
            win32api.keybd_event(self.KEY_CODE[key], 0, win32con.KEYEVENTF_KEYUP, 0)
            
    
    def action_mouse_click(self, is_blinking, mouse_key, time_last_click):
        """Click left or right mouse buttom

        Args:
            is_blinking (bool): _description_
            mouse_key (string): Mouse button to click
            time_last_click (float): Epoch time stamp of last click action
        """
        if time.time() > time_last_click+1:
            if mouse_key.lower().__eq__("left click"):
                event_down = win32con.MOUSEEVENTF_LEFTDOWN
                event_up = win32con.MOUSEEVENTF_LEFTUP
            else:
                event_down = win32con.MOUSEEVENTF_RIGHTDOWN
                event_up = win32con.MOUSEEVENTF_RIGHTUP
                
            if is_blinking and mouse_key != "none":
                self.time_since_last_click = time.time()
                win32api.mouse_event(event_down, 0,0)
                time.sleep(0.1)
                win32api.mouse_event(event_up, 0,0)
