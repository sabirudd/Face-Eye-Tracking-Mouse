import tkinter
import customtkinter
from pygrabber.dshow_graph import FilterGraph  #pip install pygrabber
import cv2
from PIL import Image
import time
import numpy as np
from scipy.spatial import distance as dist
from HeadTracking import HeadTracking
#from pyuac import main_requires_admin
import string

class PoseMediaPipe(customtkinter.CTkFrame):

    frames = {"pose_mediapipe": None}
    self_frame = None


    def __init__(self, master, controller):
        super().__init__(master)

       
        BUTTON_PADDING_X = 10
        BUTTON_PADDING_Y = 5
        BUTTON_PADDING_FIRST_LAST_Y = 10
        SMALL_FONT_SIZE = 12
        self.CAMERA_LIST = FilterGraph().get_input_devices()

        self.head_tracking = None
        self.pose_text = None
        self.pose_values = None
        self.tracking_enabled = False
        self.is_blinking = (False, False)
        self.ear = (0, 0)

        self.controller = controller

        self.frames['pose_mediapipe'] = customtkinter.CTkFrame(master=master, fg_color="transparent")
        # bt_from_frame2 = customtkinter.CTkButton(self.frames['gaze_dlib'], text="Test 2544545", command=lambda:print("test 21341324"))
        # bt_from_frame2.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        self.self_frame = self.frames['pose_mediapipe']



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
        self.self_frame.action_label = customtkinter.CTkLabel(self.self_frame.view_settings_frame, text="Pose Action:", 
                                                 font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.action_label.grid(row=3, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y,0))
        self.self_frame.action_optionmenu = customtkinter.CTkOptionMenu(self.self_frame.view_settings_frame, 
                                                             dynamic_resizing=False,
                                                             values=["None", "Mouse", "WASD", "Arrow"])
        self.self_frame.action_optionmenu.grid(row=4, column=2, padx=BUTTON_PADDING_X, pady=(0, BUTTON_PADDING_Y))
        
        
        # Blink Action
        self.self_frame.blink_action_frame = customtkinter.CTkFrame(self.self_frame.view_settings_frame, fg_color="transparent", width=160)
        self.self_frame.blink_action_frame.grid(row=5, column=2)
        key_values = np.array(["None", "Left Click", "Right Click", "Spacebar"])
        key_values = np.concatenate((key_values, list(string.ascii_lowercase)))
        
            #Left
        self.self_frame.action_blink_left_label = customtkinter.CTkLabel(self.self_frame.blink_action_frame, text="Blink Left:", 
                                                 font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.action_blink_left_label.grid(row=0, column=0, padx=(BUTTON_PADDING_X, 0), pady=(BUTTON_PADDING_Y,0))
        self.self_frame.action_blink_left_optionmenu = customtkinter.CTkOptionMenu(self.self_frame.blink_action_frame, 
                                                             dynamic_resizing=False, values=key_values, width=61)
        self.self_frame.action_blink_left_optionmenu.grid(row=1, column=0, padx=(BUTTON_PADDING_X, 0), pady=(0, BUTTON_PADDING_Y))
        
            #Right
        self.self_frame.action_blink_right_label = customtkinter.CTkLabel(self.self_frame.blink_action_frame, text="Blink Right:", 
                                                 font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.action_blink_right_label.grid(row=0, column=1, padx=0, pady=(BUTTON_PADDING_Y,0))
        self.self_frame.action_blink_right_optionmenu = customtkinter.CTkOptionMenu(self.self_frame.blink_action_frame, 
                                                             dynamic_resizing=False, values=key_values, width=61)
        self.self_frame.action_blink_right_optionmenu.grid(row=1, column=1, padx=(BUTTON_PADDING_X, BUTTON_PADDING_X), pady=(0, BUTTON_PADDING_Y))
        

        # Apply Button
        # self.self_frame.view_settings_apply = customtkinter.CTkButton(self.self_frame.view_settings_frame, 
        #                                                    text="Apply", 
        #                                                    command=self.apply_event)
        # self.self_frame.view_settings_apply.grid(row = 8, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y, BUTTON_PADDING_Y))

        #self.self_frame.
        # self.self_frame.progressbar_1 = customtkinter.CTkProgressBar(self.self_frame.view_settings_frame, width=140)
        # self.self_frame.progressbar_1.grid(row=5, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_FIRST_LAST_Y, BUTTON_PADDING_Y), sticky="ew")
        # self.self_frame.slider_1 = customtkinter.CTkSlider(self.self_frame.view_settings_frame, from_=0, to=1, number_of_steps=4, width=140)
        # self.self_frame.slider_1.grid(row=6, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y, BUTTON_PADDING_FIRST_LAST_Y), sticky="ew")


        # Offset Entry
        verify_offset_input = (self.register(self.verify_digit))
        
        self.self_frame.offset_frame = customtkinter.CTkFrame(self.self_frame.view_settings_frame, fg_color="transparent", width=160)
        self.self_frame.offset_frame.grid(row=10, column=2)
        
        self.self_frame.x_offset_label = customtkinter.CTkLabel(self.self_frame.offset_frame, text="X Offset:", 
                                                 font=customtkinter.CTkFont(size=SMALL_FONT_SIZE), anchor="w")
        self.self_frame.x_offset_label.grid(row=0, column=0, padx=(BUTTON_PADDING_X, 0), pady=(BUTTON_PADDING_Y,0))
        self.self_frame.x_offset_entry = customtkinter.CTkEntry(self.self_frame.offset_frame, placeholder_text="0", width=61, 
                                                                validate='all', validatecommand=(verify_offset_input, '%P'))
        self.self_frame.x_offset_entry.grid(row=1, column=0, padx=(BUTTON_PADDING_X, 0), pady=(0, BUTTON_PADDING_Y))

        self.self_frame.y_offset_label = customtkinter.CTkLabel(self.self_frame.offset_frame, text="Y Offset:", 
                                                 font=customtkinter.CTkFont(size=SMALL_FONT_SIZE), anchor="w")
        self.self_frame.y_offset_label.grid(row=0, column=1, padx=0, pady=(BUTTON_PADDING_Y,0))
        self.self_frame.y_offset_entry = customtkinter.CTkEntry(self.self_frame.offset_frame, placeholder_text="0", width=61, 
                                                                validate='all', validatecommand=(verify_offset_input, '%P'))
        self.self_frame.y_offset_entry.grid(row=1, column=1, padx=(BUTTON_PADDING_X, BUTTON_PADDING_X), pady=(0, BUTTON_PADDING_Y))


        # Mouse Movement Multiplier
        verify_float_input = (self.register(self.verify_float))
        self.self_frame.mouse_multiplier_label = customtkinter.CTkLabel(self.self_frame.view_settings_frame, text="Mouse Speed:", 
                                                 font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.mouse_multiplier_label.grid(row=11, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y,0))
        self.self_frame.mouse_multiplier_entry = customtkinter.CTkEntry(self.self_frame.view_settings_frame, placeholder_text="0.3", 
                                                                validate='all', validatecommand=(verify_float_input, '%P'))
        self.self_frame.mouse_multiplier_entry.grid(row=12, column=2, padx=BUTTON_PADDING_X, pady=(0, BUTTON_PADDING_Y))

        # Eye Aspect Ratio Threshold
        self.self_frame.mouse_ear_threshold_label = customtkinter.CTkLabel(self.self_frame.view_settings_frame, text="EAR Threshold:", 
                                                 font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.mouse_ear_threshold_label.grid(row=13, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y,0))
        self.self_frame.mouse_ear_threshold_entry = customtkinter.CTkEntry(self.self_frame.view_settings_frame, placeholder_text="0.45", 
                                                                validate='all', validatecommand=(verify_float_input, '%P'))
        self.self_frame.mouse_ear_threshold_entry.grid(row=14, column=2, padx=BUTTON_PADDING_X, pady=(0, BUTTON_PADDING_FIRST_LAST_Y))

    
        # Horizontal Flip Switch
        self.self_frame.horizontal_switch = customtkinter.CTkSwitch(self.self_frame.view_settings_frame, text="Horizontal Flip",
                                                                    font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.horizontal_switch.grid(row=15, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y, BUTTON_PADDING_Y))

        # Vertical Flip Switch
        self.self_frame.vertical_switch = customtkinter.CTkSwitch(self.self_frame.view_settings_frame, text=" Vertical Flip ",
                                                                  font=customtkinter.CTkFont(size=SMALL_FONT_SIZE))
        self.self_frame.vertical_switch.grid(row=16, column=2, padx=BUTTON_PADDING_X, pady=(BUTTON_PADDING_Y, BUTTON_PADDING_Y))


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

    def verify_digit(self, x):
        if len(x) > 0 and x[len(x)-1] == " ":
            return False
        if x == "" or x == "-":
            return True
        try:
            x = int(x)
            return True
        except:
            return False
        
    def verify_offset_input(self, x):
        if self.verify_digit(x) and (x == "" or x == "-"):
            return 0
        return int(x)
    
    def verify_float_input(self, x):
        if self.verify_float(x) and x == "" and x != " ":
            return 0
        return float(x)


    def find_camera(self, value, list):
        index = 0
        for i in range(len(list)):
            if value == list[i]:
                return i
        return index
    

    def camera_view_setup(self):
        if self.tracking_enabled:
            print("MediaPipe Tracking Enabled")
            camera_index = self.find_camera(self.self_frame.camera_optionmenu.get(), self.CAMERA_LIST)
            self.cap = cv2.VideoCapture(camera_index)
            self.lmain = customtkinter.CTkLabel(master=self.self_frame.view_frame, text="")
            self.lmain.grid(row=0, column=0)
            self.head_tracking = HeadTracking(self.cap)
        else:
            camera_index, self.cap, self.lmain, self.head_tracking = None, None, None, None
        

    def apply_event(self):
        self.camera_view_setup()
        self.track_face()
        


    def track_face(self):
        if self.tracking_enabled:
            x_offset = self.verify_offset_input(self.self_frame.x_offset_entry.get())
            y_offset = self.verify_offset_input(self.self_frame.y_offset_entry.get())
            mouse_speed = self.verify_float_input(self.self_frame.mouse_multiplier_entry.get())
            ear_input = self.verify_float_input(self.self_frame.mouse_ear_threshold_entry.get())
            action_blink_left = self.self_frame.action_blink_left_optionmenu.get()
            action_blink_right = self.self_frame.action_blink_right_optionmenu.get()
            
            horizontal_flip = self.self_frame.horizontal_switch.get()
            vertical_flip = self.self_frame.vertical_switch.get()
            action_mode = self.self_frame.action_optionmenu.get()
            image, self.pose_text, self.pose_values, self.is_blinking, self.ear = self.head_tracking.track(flip_horizontal=horizontal_flip, 
                                                                                                           flip_vertical=vertical_flip, 
                                                                                                           mode=action_mode, 
                                                                                                           x_offset=x_offset, 
                                                                                                           y_offset=y_offset,
                                                                                                           mouse_multiplier=mouse_speed,
                                                                                                           ear_threshold=ear_input,
                                                                                                           action_blink_left=action_blink_left,
                                                                                                           action_blink_right=action_blink_right)
            cv2img = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
            imgtk = customtkinter.CTkImage(Image.fromarray(cv2img), size=(720,540))
            self.lmain.imgtk = imgtk
            self.lmain.configure(image=imgtk)
            self.calculate_video_fps()
            self.lmain.after(10, self.track_face)
        else:
            print("MediaPipe Tracking Disabled")


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

    def calculate_video_fps(self):
        self.new_frame_time = time.time()
        fps = 1/(self.new_frame_time- self.prev_frame_time)
        self.prev_frame_time = self.new_frame_time
        fps = round(fps, 2)
        self.time_diff = self.new_frame_time - self.start_time
        pose_x = round(self.pose_values[0], 2)
        pose_y = round(self.pose_values[1], 2)
        ear_left = round(self.ear[0], 2)
        ear_right = round(self.ear[1], 2)
        self.self_frame.view_details_fps.configure(text=("Video FPS: " + str(fps) + 
                                                         " | Pose: " + self.pose_text + 
                                                         " | X: " + str(pose_x) + ", Y: " + str(pose_y) +
                                                         " | Blinking Left: " + str(self.is_blinking[0]) + " (" + str(ear_left) + ")" +
                                                         ", Blinking Right: " + str(self.is_blinking[1]) + " (" + str(ear_right) + ")"
                                                         ))
