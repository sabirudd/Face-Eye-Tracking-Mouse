
import tkinter
import customtkinter
from pygrabber.dshow_graph import FilterGraph  #pip install pygrabber
import cv2
from PIL import Image
import time
import dlib
import numpy as np
from scipy.spatial import distance as dist
from HeadTracking import HeadTracking
from GazeDlib import GazeDlib
from PoseMediaPipe import PoseMediaPipe
#from pyuac import main_requires_admin
import string
import win32api
import win32con
import threading
import keyboard
import os


DARK_MODE = "dark"
customtkinter.set_appearance_mode(DARK_MODE)
customtkinter.set_default_color_theme("blue")

#@main_requires_admin
class App(customtkinter.CTk):

    frames = {"information": None, "gaze_dlib": None, "pose_mediapipe": None}

    def frame_information_selector(self):
        GazeDlib.frames["gaze_dlib"].pack_forget()
        PoseMediaPipe.frames["pose_mediapipe"].pack_forget()
        App.frames["information"].pack(in_=self.right_side_container,side=tkinter.TOP, fill=tkinter.BOTH, expand=True, padx=0, pady=0)
        self.set_selected_button("information")

    def frame_eye_dlib_selector(self):
        App.frames["information"].pack_forget()
        PoseMediaPipe.frames["pose_mediapipe"].pack_forget()
        GazeDlib.frames["gaze_dlib"].pack(in_=self.right_side_container,side=tkinter.TOP, fill=tkinter.BOTH, expand=True, padx=0, pady=0)
        self.set_selected_button("dlib")

    def frame_face_mediapipe_selector(self):
        App.frames["information"].pack_forget()
        GazeDlib.frames["gaze_dlib"].pack_forget()
        PoseMediaPipe.frames["pose_mediapipe"].pack(in_=self.right_side_container,side=tkinter.TOP, fill=tkinter.BOTH, expand=True, padx=0, pady=0)
        self.set_selected_button("mediapipe")
        
    def set_selected_button(self, name):
        self.bt_information.configure(fg_color=("gray75", "gray25") if name == "information" else "transparent")
        self.bt_eye_dlib.configure(fg_color=("gray75", "gray25") if name == "dlib" else "transparent")
        self.bt_face_mediapipe.configure(fg_color=("gray75", "gray25") if name == "mediapipe" else "transparent")

    def __init__(self):
        super().__init__()

        BUTTON_PADDING_X = 10
        BUTTON_PADDING_Y = 5
        BUTTON_PADDING_FIRST_LAST_Y = 10
        self.CAMERA_LIST = FilterGraph().get_input_devices()
        
        
        # Load images
        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
        self.info_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "information.png")), size=(20, 20))
        self.eye_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "eye.png")), size=(20, 20))
        self.face_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "face.png")), size=(20, 20))

        # self.state('withdraw')
        self.title("WMM")
        self.geometry(f"{1110}x{640}")

        # contains everything
        main_container = customtkinter.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill=tkinter.BOTH, expand=True, padx=10, pady=10)

        # left side panel -> for frame selection
        left_side_panel = customtkinter.CTkFrame(main_container, width=160, fg_color="transparent")
        left_side_panel.pack(side=tkinter.LEFT, fill=tkinter.Y, expand=False, padx=0, pady=10)


        # sidebar title
        self.logo_label = customtkinter.CTkLabel(left_side_panel, 
                                                 text="Webcam   \nMouse      \nMovement", 
                                                 font=customtkinter.CTkFont(size=20, weight="bold", family="Roboto Mono"))
        self.logo_label.grid(row=0, column=0, padx=BUTTON_PADDING_X, pady=BUTTON_PADDING_FIRST_LAST_Y)


        # Frame Padding
        self.frame_padding = customtkinter.CTkFrame(left_side_panel, width=160, height=214, fg_color="transparent")
        self.frame_padding.grid(row=4, column=0, padx=0, pady=0)

        # Appearance Mode
        self.appearance_mode_label = customtkinter.CTkLabel(left_side_panel, text="Appearance Mode:", width=120)
        self.appearance_mode_label.grid(row=5, column=0, padx=10, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(left_side_panel, 
                                                                       values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.set("System")
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=10, pady=(0, 10))
        
        # UI Scaling Option
        self.scaling_label = customtkinter.CTkLabel(left_side_panel, text="UI Scaling:", width=120)
        self.scaling_label.grid(row=7, column=0, padx=10, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(left_side_panel, 
                                                               values=["50%", "75%", "100%", "125%", "150%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=10, pady=(0, 10))
        self.scaling_optionemenu.set("100%")


        # Buttons to select the frames
        self.bt_information = customtkinter.CTkButton(left_side_panel, text="Information", command=self.frame_information_selector,
                                                 corner_radius=0, height=40, border_spacing=5,
                                                 fg_color=("gray75", "gray25"), text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                 image=self.info_image, compound="left", anchor="w")
        self.bt_information.grid(row=1, column=0, padx=(0,0), pady=BUTTON_PADDING_Y)

        self.bt_eye_dlib = customtkinter.CTkButton(left_side_panel, text="Gaze (Dlib)", command=self.frame_eye_dlib_selector,
                                              corner_radius=0, height=40, border_spacing=5,
                                              fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                              image=self.eye_image, compound="left", anchor="w")
        self.bt_eye_dlib.grid(row=2, column=0, padx=(0,0), pady=BUTTON_PADDING_Y)

        self.bt_face_mediapipe = customtkinter.CTkButton(left_side_panel, text="Pose (MediaPipe)", command=self.frame_face_mediapipe_selector,
                                                    corner_radius=0, height=40, border_spacing=5,
                                                    fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                    image=self.face_image, compound="left", anchor="w")
        self.bt_face_mediapipe.grid(row=3, column=0, padx=(0,0), pady=BUTTON_PADDING_Y)

        # Right side panel
        self.right_side_panel = customtkinter.CTkFrame(main_container)
        self.right_side_panel.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True, padx=10, pady=0)

        self.right_side_container = customtkinter.CTkFrame(self.right_side_panel)
        self.right_side_container.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True, padx=0, pady=0)

        App.frames['information'] = customtkinter.CTkFrame(fg_color="transparent", master=self)

        App.frames['gaze_dlib'] = GazeDlib(master=self, controller=self.right_side_container)
        App.frames['pose_mediapipe'] = PoseMediaPipe(master=self, controller=self.right_side_container)
        #App.frames['information'].pack(in_=self.right_side_container,side=tkinter.TOP, fill=tkinter.BOTH, expand=True, padx=10, pady=10)


        # Information frame
        self.info_frame = customtkinter.CTkFrame(App.frames['information'], height=600, width=890)
        self.info_frame.grid(row=1, column=1, padx=10, pady=10, sticky="n")

        self.info_title = customtkinter.CTkLabel(self.info_frame, font=customtkinter.CTkFont(size=26, weight="bold"), text=("Information"))
        self.info_title.grid(row=1, column=1, padx=10, pady=10, sticky="n")

        self.what_header = customtkinter.CTkLabel(self.info_frame, font=customtkinter.CTkFont(size=16, weight="bold"), text="What is this?")
        self.what_header.grid(row=2, column=1, padx=10, pady=2, sticky="n")
        what_content_string_1 = "A program which lets you control your computer with facial feature tracking. It currently supports two methods of detection.\n"
        what_content_string_2 = "These include gaze estimation with eye tracking and facial pose prediction with face tracking."
        self.what_content = customtkinter.CTkLabel(self.info_frame, font=customtkinter.CTkFont(size=12), text=(what_content_string_1+what_content_string_2))
        self.what_content.grid(row=3, column=1, padx=10, pady=(0,4), sticky="n")

        self.how_work_header = customtkinter.CTkLabel(self.info_frame, font=customtkinter.CTkFont(size=16, weight="bold"), text="How does it work?")
        self.how_work_header.grid(row=4, column=1, padx=10, pady=2, sticky="n")
        how_work_content_string_1 = "The facial tracking was built on models provided by Dlib and MediaPipe. The models give a way to gather points on the face,\n"
        how_work_content_string_2 = "known as facial landmarks. With these landmarks (and a lot of Math), we can make several assumptions (like predicting the\n eye gaze and face pose)."
        self.how_work_content = customtkinter.CTkLabel(self.info_frame, font=customtkinter.CTkFont(size=12), text=(how_work_content_string_1+how_work_content_string_2))
        self.how_work_content.grid(row=5, column=1, padx=10, pady=(0,4), sticky="n")

        self.how_use_header = customtkinter.CTkLabel(self.info_frame, font=customtkinter.CTkFont(size=16, weight="bold"), text="How do I use this?")
        self.how_use_header.grid(row=6, column=1, padx=10, pady=2, sticky="n")
        how_use_content_string_1 = "Click on one of the facial models on the left side panel. Once you click 'Activate', the tracking will start. An video of\n"
        how_use_content_string_2 = "the processed frames will show in the middle. You can adjust the settings of the image using the input options on the right.\n"
        how_use_content_string_3 = "Some information about the video will be below the frame. Once you are done, you can click 'Deactivate' to stop the program."
        self.how_use_content = customtkinter.CTkLabel(self.info_frame, font=customtkinter.CTkFont(size=12), text=(how_use_content_string_1+how_use_content_string_2+how_use_content_string_3))
        self.how_use_content.grid(row=7, column=1, padx=10, pady=(0,4), sticky="n")

        self.what_settings_header = customtkinter.CTkLabel(self.info_frame, font=customtkinter.CTkFont(size=16, weight="bold"), text="What do the settings do?")
        self.what_settings_header.grid(row=8, column=1, padx=10, pady=2, sticky="n")
        what_settings_string_1 = "Camera select - Select the camera you want to use \nGaze / Pose Actios - A selection of options which activate based on gaze / pose"
        what_settings_string_2 = "\nMouse Speed - The speed at which the mouse will move (if 'Mouse' action is selected) \nBlink Action - A selection of keys which activate based on blink status"
        what_settings_string_3 = "\nEAR Threshold - The threshold ratio of the eye where a blink is detected (lower = requires eyes to be closed more)"
        what_settings_string_4 = "\nEye Threshold - The point at which the iris can be separated from the rest of the eye (based on light intensity)"
        what_settings_string_5 = "\nX & Y Offset - Push the predicted point in a specific direction"
        what_settings_string = what_settings_string_1 + what_settings_string_2 + what_settings_string_3 + what_settings_string_4 + what_settings_string_5
        self.how_use_content = customtkinter.CTkLabel(self.info_frame, font=customtkinter.CTkFont(size=12), text=(what_settings_string))
        self.how_use_content.grid(row=9, column=1, padx=10, pady=(0,4), sticky="n")

        self.which_model_header = customtkinter.CTkLabel(self.info_frame, font=customtkinter.CTkFont(size=16, weight="bold"), text="Which tracking method should I use?")
        self.which_model_header.grid(row=10, column=1, padx=10, pady=2, sticky="n")
        which_model_content_string_1 = "The gaze tracking performs best in areas with consistent lighting and requires substantial computing performance. The pose tracking\n"
        which_model_content_string_2 = "is good for situations where you are relying heavily on the mouse control and is less computationally expensive to run. It provides various\n"
        which_model_content_string_3 = "speeds of mouse movement depending on the pose angle. So it is easy to make adjustments. In all cases, you should try to be framed at the\n"
        which_model_content_string_4 = "centre with your whole face visible for the best experience."
        which_model_content_string = which_model_content_string_1 + which_model_content_string_2 + which_model_content_string_3 + which_model_content_string_4
        self.how_use_content = customtkinter.CTkLabel(self.info_frame, font=customtkinter.CTkFont(size=12), text=(which_model_content_string))
        self.how_use_content.grid(row=11, column=1, padx=10, pady=(0,4), sticky="n")

        self.security_notice = customtkinter.CTkLabel(self.info_frame, font=customtkinter.CTkFont(size=20), 
                                                      text="⚠️No information is stored or collected. This application does not access the internet.     ⚠️")
        self.security_notice.grid(row=12, column=1, padx=10, pady=(4,5), sticky="s")
        self.security_notice = customtkinter.CTkLabel(self.info_frame, font=customtkinter.CTkFont(size=20), 
                                                      text="Emergency Shut Down Hotkey: ALT + Q")
        self.security_notice.grid(row=13, column=1, padx=10, pady=(4,5), sticky="s")



    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_window_scaling(new_scaling_float)
        customtkinter.set_widget_scaling(new_scaling_float)

       
a = App()

quit_event = threading.Event()

def stop_application():
    quit_event.set()
    a.quit()
keyboard.add_hotkey("alt+q", stop_application)

a.mainloop()

