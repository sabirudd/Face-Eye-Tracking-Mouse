import cv2
import numpy as np
import mediapipe as mp
import win32api
import win32con
from scipy.spatial import distance as dist
import time
from threading import Thread

class HeadTracking:
    """Head tracking for pose estimation with MediaPipe
    """
    def __init__(self, cap):
        """Creates MediaPipe FaceMesh and required information for pose estimation

        Args:
            cap: cv2.VideoCapture object
        """
        self.cap = cap
        self.LANDMARK_INDECIES = [1, 33, 61, 199, 263, 291]
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        
        self.focal_length = (self.height + self.width)/2
        self.camera_matrix = np.array([[self.focal_length, 0, self.width / 2],
                                       [0, self.focal_length, self.height / 2],
                                       [0, 0, 1]])
        self.dist_coeff = np.zeros((4, 1), dtype=np.float64)
        
        mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
        
        self.LEFT_EYE_LANDMARKS =[362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.RIGHT_EYE_LANDMARKS = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.face_2d_landmarks = []
        self.face_3d_landmarks = []
        
        self.time_since_last_click = 0


    def track(self, flip_horizontal=False, flip_vertical=False, mode="Mouse", 
              deadzone=7, x_offset=0, y_offset=0, mouse_multiplier=0.4, 
              ear_threshold=0.5, action_blink_left="None", action_blink_right="None"):
        """Calculate facial pose for a single frame

        Args:
            flip_horizontal (bool, optional): Horizontally flip the image. Defaults to False.
            flip_vertical (bool, optional): Vertically flip the image. Defaults to False.
            mode (str, optional): Action tied to pose. Defaults to "Mouse".
            deadzone (float, optional): Deadzone which x or y must cross to activate action. Defaults to 7.
            x_offset (float, optional): Pose calculation offset in x-axis. Defaults to 0.
            y_offset (float, optional): Pose calculation offset in x-axis. Defaults to 0.
            mouse_multiplier (float, optional): Multiplier to increase mouse movement speed. Defaults to 0.4.
            ear_threshold (float, optional): Ratio threshold to detect a blink. Defaults to 0.5.
            action_key (str, optional): The key input tied to the action. Defaults to "None".

        Returns:
            image: Image after processing
            pose_text (string): Estimated facial pose
            (x,y) (float, float): Tuple for pose direction in x and y axis
            (is_blinking_left, is_blinking_right) (bool, bool): Tuple representing if the left or right eye is blinking
            (ear_left, ear_right) (float, float): Tuple of aspect ratio calculation for left and right eye
        """
        pose_text = "No Face Detected"
        x, y = 0, 0
        is_blinking_left, is_blinking_right = False, False
        ear_left, ear_right = 0, 0
        
        if mouse_multiplier == 0:
            mouse_multiplier = 0.5
        if ear_threshold == 0:
            ear_threshold = 0.5

        ret, image = self.cap.read()
        if not ret:
            return

        if flip_horizontal:
            image = cv2.flip(image, 1)
        if flip_vertical:
            image = cv2.flip(image, 0)

        res = self.face_mesh.process(image)

        # Check if face is found
        if res.multi_face_landmarks:
            for face_landmarks in res.multi_face_landmarks:
                self.face_3d_landmarks = [[int(landmark.x * self.width), int(landmark.y * self.height), landmark.z] 
                                            for index, landmark in enumerate(face_landmarks.landmark)
                                            if index in self.LANDMARK_INDECIES]

                self.face_2d_landmarks = [[int(landmark.x * self.width), int(landmark.y * self.height)] 
                                          for index, landmark in enumerate(face_landmarks.landmark)
                                          if index in self.LANDMARK_INDECIES]
                
                self.face_2d_landmarks = np.array(self.face_2d_landmarks, dtype=np.float64)
                self.nose_landmark = self.face_2d_landmarks[0]
                self.face_3d_landmarks = np.array(self.face_3d_landmarks, dtype=np.float64)

                # Calculate horizontal and vertical euler angles
                _, rotation_vector, _ = cv2.solvePnP(self.face_3d_landmarks, self.face_2d_landmarks, 
                                                     self.camera_matrix, self.dist_coeff)
                rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
                euler_angles = cv2.RQDecomp3x3(rotation_matrix)[0]
                x = (euler_angles[1] * 360) + x_offset
                y = (euler_angles[0] * 360) + y_offset
                    
                    
                pose_text = self.check_pose(x, y, deadzone)

                ear_left, ear_right = self.eye_aspect_ratio(self.get_landmarks(image, res))
                ear_average = (ear_left + ear_right)/2

                if ear_left < ear_threshold:
                    is_blinking_left = True
                else:
                    is_blinking_left = False

                if ear_right < ear_threshold:
                    is_blinking_right = True
                else:
                    is_blinking_right = False
                    
                
                action_blink_left = action_blink_left.lower()
                action_blink_right = action_blink_right.lower()
                is_blink_left_key =  action_blink_left != "none" and action_blink_left != "left click" and action_blink_left !=  "right click"
                is_blink_right_key = action_blink_right != "none" and action_blink_right != "left click" and action_blink_right !=  "right click"
                is_blink_left_mouse = action_blink_left == "left click" or action_blink_left ==  "right click"
                is_blink_right_mouse = action_blink_right == "left click" or action_blink_right ==  "right click"
                
                is_same_action =  action_blink_left.__eq__(action_blink_right)
                if is_same_action:
                    use_average_ear = ear_average < ear_threshold or ear_left < ear_threshold or ear_right < ear_threshold
                
                if is_blink_left_key and is_blink_right_key:
                    if is_same_action:
                        self.action_hold_key(use_average_ear, action_blink_left)
                    else:
                        self.action_hold_key(ear_left < ear_threshold, action_blink_left)
                        self.action_hold_key(ear_right < ear_threshold, action_blink_right)
                elif is_blink_left_key and not is_blink_right_key:
                    self.action_hold_key(ear_left < ear_threshold, action_blink_left)
                elif not is_blink_left_key and is_blink_right_key:
                    self.action_hold_key(ear_right < ear_threshold, action_blink_right)
                    
                    
                if is_blink_left_mouse and is_blink_right_mouse:
                    action_blink_left = action_blink_left.lower()
                    action_blink_right = action_blink_right.lower()
                    if is_same_action:
                        self.action_mouse_click(use_average_ear, action_blink_left, self.time_since_last_click)
                    else:
                        self.action_mouse_click(ear_left < ear_threshold, action_blink_left, self.time_since_last_click)
                        self.action_mouse_click(ear_right < ear_threshold, action_blink_right, self.time_since_last_click)
                elif is_blink_left_mouse and not is_blink_right_mouse:
                    self.action_mouse_click(ear_right < ear_threshold, action_blink_right, self.time_since_last_click)
                elif not is_blink_left_mouse and is_blink_right_mouse:
                    self.action_mouse_click(ear_right < ear_threshold, action_blink_right, self.time_since_last_click)
                                    

                if mode == "Mouse":
                    self.mouse_mode(x, y, deadzone, mouse_multiplier)
                elif mode == "WASD":
                    self.wasd_mode(x, y, deadzone)
                elif mode == "Arrow":
                    self.arrow_mode(x, y, deadzone)

                p1 = (int(self.nose_landmark[0]), int(self.nose_landmark[1]))
                p2 = (int(self.nose_landmark[0] + x * 10) , int(self.nose_landmark[1] - y * 10))
                #p2 = int(self.nose_landmark[0] - math.sin(y)*math.cos(x)*50), int(self.nose_landmark[1] + math.sin(x)*50)
            
                cv2.line(image, p1, p2, (255, 0, 0), 3)

        return image, pose_text, (x, y), (is_blinking_left, is_blinking_right), (ear_left, ear_right)
    
    
    def check_pose(self, x, y, deadzone):
        """Creates string based on estimated facial pose

        Args:
            x (float): Pose direction in x-axis
            y (float): Pose direction in y-axis
            deadzone (float): Deadzone which x or y must cross for a direction

        Returns:
            string: Estimated facial pose
        """
        if x < -deadzone:
            pose_text = "Left"
        elif x > deadzone:
            pose_text = "Right"
        else:
            pose_text = "Forward"
        if y < -deadzone:
            pose_text = pose_text + " Down"
        elif y > deadzone:
            pose_text = pose_text + " Up"
        else:
            pose_text = pose_text + " Centre"
        return pose_text

    def mouse_mode(self, x, y, deadzone, multiplier):
        """Move mouse if x and y values are outside a deadzone

        Args:
            x (float): Pose direction in x-axis
            y (float): Pose direction in y-axis
            deadzone (float): Deadzone which x or y must cross to activate mouse movement
            multiplier (float): Multiplier to increase mouse movement speed
        """
        pos = win32api.GetCursorPos()        
        if x < -deadzone or x > deadzone:
            win32api.SetCursorPos((int(pos[0] + (x*multiplier)), int(pos[1])))

        pos = win32api.GetCursorPos()
        if y < -deadzone or y > deadzone:
            win32api.SetCursorPos((int(pos[0]), int(pos[1] + (-y*multiplier))))


    def wasd_mode(self, x, y, deadzone):
        """Press WASD keys if x and y values are outside a deadzone

        Args:
            x (float): Pose direction in x-axis
            y (float): Pose direction in y-axis
            deadzone (float): Deadzone which x or y must cross to activate arrow key press
        """
        if x < -deadzone:
            win32api.keybd_event(self.KEY_CODE['a'], 0, 0, 0)
        elif x > deadzone:
            win32api.keybd_event(self.KEY_CODE['d'], 0, 0, 0)
        else:
            win32api.keybd_event(self.KEY_CODE['a'], 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(self.KEY_CODE['d'], 0, win32con.KEYEVENTF_KEYUP, 0)
        
        if y < -deadzone:
            win32api.keybd_event(self.KEY_CODE['s'], 0, 0, 0)
        elif y > deadzone:
            win32api.keybd_event(self.KEY_CODE['w'], 0, 0, 0)
        else:
            win32api.keybd_event(self.KEY_CODE['s'], 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(self.KEY_CODE['w'], 0, win32con.KEYEVENTF_KEYUP, 0)


    def arrow_mode(self, x, y, deadzone):
        """Press arrow keys if x and y values are outside a deadzone

        Args:
            x (float): Pose direction in x-axis
            y (float): Pose direction in y-axis
            deadzone (float): Deadzone which x or y must cross to activate arrow key press
        """
        if x < -deadzone:
            win32api.keybd_event(self.KEY_CODE['left_arrow'], 0, 0, 0)
        elif x > deadzone:
            win32api.keybd_event(self.KEY_CODE['right_arrow'], 0, 0, 0)
        else:
            win32api.keybd_event(self.KEY_CODE['left_arrow'], 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(self.KEY_CODE['right_arrow'], 0, win32con.KEYEVENTF_KEYUP, 0)
        
        if y < -deadzone:
            win32api.keybd_event(self.KEY_CODE['down_arrow'], 0, 0, 0)
        elif y > deadzone:
            win32api.keybd_event(self.KEY_CODE['up_arrow'], 0, 0, 0)
        else:
            win32api.keybd_event(self.KEY_CODE['down_arrow'], 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(self.KEY_CODE['up_arrow'], 0, win32con.KEYEVENTF_KEYUP, 0)


    def get_landmarks(self, img, results):
        """Get the 2-Dimensional facial landmarks within an image

        Args:
            img: Image
            results: Result from FaceMesh processing

        Returns:
           [(int[], int[])]: 2-Dimensional facial landmarks
        """
        height, width = img.shape[:2]
        landmarks = [(int(landmark.x * width), int(landmark.y * height)) 
                     for landmark in results.multi_face_landmarks[0].landmark]
        return landmarks


    def eye_aspect_ratio(self, landmarks):
        """Calculate Eye Aspect Ratio

        Args:
            landmarks ([(int[], int[])]): 2-Dimensional facial landmarks in an array

        Returns:
            (float, float): Tuple for EAR (EAR_Left, EAR_Right)
        """
        x_right = dist.euclidean(landmarks[self.RIGHT_EYE_LANDMARKS[0]], landmarks[self.RIGHT_EYE_LANDMARKS[8]])
        y_right = dist.euclidean(landmarks[self.RIGHT_EYE_LANDMARKS[12]], landmarks[self.RIGHT_EYE_LANDMARKS[4]])
        ratio_right = (2*y_right)/x_right

        x_left = dist.euclidean(landmarks[self.LEFT_EYE_LANDMARKS[0]], landmarks[self.LEFT_EYE_LANDMARKS[8]])
        y_left = dist.euclidean(landmarks[self.LEFT_EYE_LANDMARKS[12]], landmarks[self.LEFT_EYE_LANDMARKS[4]])
        ratio_left = (2*y_left)/x_left

        return ratio_left, ratio_right


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
            
    
    KEY_CODE = {'backspace':0x08,
                'tab':0x09,
                'clear':0x0C,
                'enter':0x0D,
                'shift':0x10,
                'ctrl':0x11,
                'alt':0x12,
                'pause':0x13,
                'caps_lock':0x14,
                'esc':0x1B,
                'spacebar':0x20,
                'page_up':0x21,
                'page_down':0x22,
                'end':0x23,
                'home':0x24,
                'left_arrow':0x25,
                'up_arrow':0x26,
                'right_arrow':0x27,
                'down_arrow':0x28,
                'select':0x29,
                'print':0x2A,
                'execute':0x2B,
                'print_screen':0x2C,
                'ins':0x2D,
                'del':0x2E,
                'help':0x2F,
                '0':0x30,
                '1':0x31,
                '2':0x32,
                '3':0x33,
                '4':0x34,
                '5':0x35,
                '6':0x36,
                '7':0x37,
                '8':0x38,
                '9':0x39,
                'a':0x41,
                'b':0x42,
                'c':0x43,
                'd':0x44,
                'e':0x45,
                'f':0x46,
                'g':0x47,
                'h':0x48,
                'i':0x49,
                'j':0x4A,
                'k':0x4B,
                'l':0x4C,
                'm':0x4D,
                'n':0x4E,
                'o':0x4F,
                'p':0x50,
                'q':0x51,
                'r':0x52,
                's':0x53,
                't':0x54,
                'u':0x55,
                'v':0x56,
                'w':0x57,
                'x':0x58,
                'y':0x59,
                'z':0x5A,
                'numpad_0':0x60,
                'numpad_1':0x61,
                'numpad_2':0x62,
                'numpad_3':0x63,
                'numpad_4':0x64,
                'numpad_5':0x65,
                'numpad_6':0x66,
                'numpad_7':0x67,
                'numpad_8':0x68,
                'numpad_9':0x69,
                'multiply_key':0x6A,
                'add_key':0x6B,
                'separator_key':0x6C,
                'subtract_key':0x6D,
                'decimal_key':0x6E,
                'divide_key':0x6F,
                'F1':0x70,
                'F2':0x71,
                'F3':0x72,
                'F4':0x73,
                'F5':0x74,
                'F6':0x75,
                'F7':0x76,
                'F8':0x77,
                'F9':0x78,
                'F10':0x79,
                'F11':0x7A,
                'F12':0x7B,
                'F13':0x7C,
                'F14':0x7D,
                'F15':0x7E,
                'F16':0x7F,
                'F17':0x80,
                'F18':0x81,
                'F19':0x82,
                'F20':0x83,
                'F21':0x84,
                'F22':0x85,
                'F23':0x86,
                'F24':0x87,
                'num_lock':0x90,
                'scroll_lock':0x91,
                'left_shift':0xA0,
                'right_shift ':0xA1,
                'left_control':0xA2,
                'right_control':0xA3,
                'left_menu':0xA4,
                'right_menu':0xA5,
                'browser_back':0xA6,
                'browser_forward':0xA7,
                'browser_refresh':0xA8,
                'browser_stop':0xA9,
                'browser_search':0xAA,
                'browser_favorites':0xAB,
                'browser_start_and_home':0xAC,
                'volume_mute':0xAD,
                'volume_Down':0xAE,
                'volume_up':0xAF,
                'next_track':0xB0,
                'previous_track':0xB1,
                'stop_media':0xB2,
                'play/pause_media':0xB3,
                'start_mail':0xB4,
                'select_media':0xB5,
                'start_application_1':0xB6,
                'start_application_2':0xB7,
                'attn_key':0xF6,
                'crsel_key':0xF7,
                'exsel_key':0xF8,
                'play_key':0xFA,
                'zoom_key':0xFB,
                'clear_key':0xFE,
                '+':0xBB,
                ',':0xBC,
                '-':0xBD,
                '.':0xBE,
                '/':0xBF,
                '`':0xC0,
                ';':0xBA,
                '[':0xDB,
                '\\':0xDC,
                ']':0xDD,
                "'":0xDE,
                '`':0xC0
                }
