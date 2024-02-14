## Details:
For windows only! <br />
Allows control of your computer with your face (pose) or eye (gaze). <br />
Supports mouse movement, WASD keys and arrow keys. <br />
Undergraduate final-year project (with dissertation detailing background and results). <br />
Uses MediaPipe 468-point face landmark model for pose estimation and Dlib 68-point face landmark model for gaze detection. <br />
Started 10/2022 - Finished 04/2023. <br />


## Required modules (installed through pip):
```
> cv2
> tkinter
> customtkinter
> pygrabber
> dlib
> numpy
> scipy
> win32api
> win32con
> keyboard
> mediapipe
```


## File structure:
```
.
├── images
│   ├── eye.png
│   ├── face.png
│   └── information.png
├── models
│   └── shape_predictor_68_face_landmarks.dat
├── GUI.py
├── GazeDlib.py
├── HeadTracking.py
└── PoseMediaPipe.py
```


## Running the program:
`python GUI.py`


## Images:
### Iris gaze tracking:
![Program screenshot 1](./screenshots/screenshot_2.png?raw=true "Program screenshot 2")
### Iris gaze tracking action options:
![Program screenshot 2](./screenshots/screenshot_3.png?raw=true "Program screenshot 3")
### Facial pose tracking:
![Program screenshot 3](./screenshots/screenshot_1.png?raw=true "Program screenshot 1")
