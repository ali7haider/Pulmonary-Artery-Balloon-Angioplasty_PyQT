import cv2  # OpenCV for camera handling
from PyQt5.QtGui import QPixmap
from class_camera import camera
from PyQt5.QtWidgets import QFileDialog
import numpy as np
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QImage, QPixmap
class CameraManager:
    def __init__(self, parent):
        self.parent = parent
        self.camera_capture = None
        self.camera_playing = False
        self.start_angle, self.end_angle = 0, 360
        self.calibrate_flag = 0
        self.total_frames = 0
        self.current_frame = 0
        self.frame_time = 0
        self.video_capture = None
        self.line_pixels = {}
        self.line_pick_pixels = {}
        self.plot_5_circles_flag = 0
        self.first_frame = None
        self.plot_monitor_pixels_flag = 0
        self.threshold = 20
         # Bind the mouse click event to the canvas
        #self.canvas.bind("<Button-1>", self.mark_position)
        self.manual_circle = []#used to store the 5 circle info
    def connect_camera(self):
        if not self.camera_playing:
            self.camera_capture = camera(6000)
            #self.camera_playing = True
            #self.frame_time = 1000 // 25  # Set frame time for 25 fps
            #self.update_camera_frame()
    def plot_lines(self):
        self.start_angle, self.end_angle = 0, 360
    def load_video(self):
        try:
            options = QFileDialog.Options()
            filename, _ = QFileDialog.getOpenFileName(self.parent, "Open Video File", "", "Video Files (*.mp4 *.avi)", options=options)
            
            if filename:
                self.video_capture = cv2.VideoCapture(filename)
                
                # Check if video capture is successful
                if not self.video_capture.isOpened():
                    print("Error: Unable to open video file.")
                    return

                self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
                # self.slider.config(to=self.total_frames)  # If using a slider in PyQt, replace with QSlider logic
                
                # Calculate frame time based on the video's frame rate
                frame_rate = self.video_capture.get(cv2.CAP_PROP_FPS)
                if frame_rate > 0:
                    self.frame_time = int(0.3 * 1000 / frame_rate)  # Time per frame in milliseconds
                else:
                    print("Error: Frame rate is not valid.")
                    return
                
                self.current_frame = 0
                print("Video loaded successfully.")
                self.update_video_frame()
        
        except Exception as e:
            print(f"An error occurred while loading the video: {e}")

    def calibrate_circle(self):
        try:
            # Find 5 circles in the roughly specified regions
            self.manual_circle = [(760, 196), (2361, 245), (752, 1821), (2342, 1794), (1578, 1018)]
            
            # Convert the frame to grayscale
            gray = cv2.cvtColor(self.video_frame, cv2.COLOR_BGR2GRAY)

            # Extract regions around the specified manual circle points
            regions = [
                gray[self.manual_circle[i][1] - 100:self.manual_circle[i][1] + 100,
                    self.manual_circle[i][0] - 100:self.manual_circle[i][0] + 100]
                for i in range(5)
            ]

            self.circles = []

            # Process each region to find contours
            for i, region in enumerate(regions):
                circle_contour = self.get_contour(region)
                if circle_contour:
                    # Update the circles list with adjusted coordinates
                    self.circles.append((circle_contour[0] + self.manual_circle[i][0] - 100,
                                        circle_contour[1] + self.manual_circle[i][1] - 100))
                else:
                    print(f"No contour found for region {i + 1}.")
            
            # Check if at least 5 circles were found
            if len(self.circles) < 5:
                print("Not enough circles found, calibration cannot be completed.")
                return

            self.plot_5_circles_flag = 1
            temp = list(self.circles[4])
            temp[0] -= 25
            temp[1] -= 25
            self.circles[4] = tuple(temp)

            # Calculate the radius using the first and the center circle
            self.radius = int(np.sqrt(
                (self.circles[0][0] - self.circles[4][0]) ** 2 +
                (self.circles[0][1] - self.circles[4][1]) ** 2
            )) - 100  # Reduce circle area

        except Exception as e:
            print(f"An error occurred during calibration: {e}")


    def update_frame(self, value):
        if self.video_capture is not None:
            if int(value) + 1 != self.current_frame:
                self.current_frame = int(value)
                self.update_video_frame()


    def update_video_frame(self):
        try:
            if self.video_capture is not None:
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
                ret, self.video_frame = self.video_capture.read()

                if not ret:
                    print("No frame read from video capture.")
                    return  # If no frame is read, exit

                # Check if the first frame is captured for background reference
                if self.first_frame is None:
                    self.first_frame = self.video_frame.copy()
                    self.first_frame_gray = cv2.cvtColor(self.first_frame, cv2.COLOR_BGR2GRAY)
                    center, radius = (1546, 992), 980
                    # self.process_diff = ProcessDiff(self.first_frame_gray, center, radius)
                    print("First frame captured for background reference.")

                # Preserve original dimensions and calculate aspect ratio
                self.original_height, self.original_width, _ = self.video_frame.shape
                aspect_ratio = self.original_width / self.original_height
                new_width = int(1000 * aspect_ratio)  # New width for resized frame

                # Work on a copy of the video frame for drawing
                cv2image_video = self.video_frame.copy()

                # Plotting circles if the flag is set
                if self.plot_5_circles_flag:
                    print("Plotting circles.")
                    for i in range(5):
                        cv2.circle(cv2image_video, self.circles[i], 5, (0, 255, 0), -1)
                    cv2.circle(cv2image_video, self.circles[4], self.radius, (0, 255, 0), 2)

                # Plot monitor pixels if the flag is set
                if self.plot_monitor_pixels_flag:
                    print("Processing monitor pixels.")
                    cv2image_video_gray = cv2.cvtColor(cv2image_video, cv2.COLOR_BGR2GRAY)
                    obj_d, obj_pos = self.process_diff.run_all(cv2image_video_gray)
                    color = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]  # Red, Green, Blue
                    count = 0
                    for pos in obj_pos:
                        if pos is not None:
                            cv2.circle(cv2image_video, pos, 15, color[count], thickness=-1)  # Filled circle
                        count += 1

                # Resize image for display
                cv2image_video_disp = cv2.resize(cv2image_video, (new_width, 1000))

                # Convert to RGB for displaying in PyQt
                img_show = cv2.cvtColor(cv2image_video_disp, cv2.COLOR_BGR2RGB)
                h, w, ch = img_show.shape
                bytes_per_line = ch * w
                q_image = QImage(img_show.data, w, h, bytes_per_line, QImage.Format_RGB888)

                # Display the image in the GUI using QLabel
                pixmap = QPixmap.fromImage(q_image)
                self.parent.lblCamera.setPixmap(pixmap)

                # Increment frame counter
                self.current_frame += 1
                if self.current_frame < self.total_frames:
                    QTimer.singleShot(self.frame_time, self.update_video_frame)

        except Exception as e:
            print(f"An error occurred while updating video frame: {e}")

    def update_frame(self, value):
        try:
            if self.video_capture is not None:
                # Update current frame if it is different from the value passed
                if int(value) + 1 != self.current_frame:
                    self.current_frame = int(value)
                    self.update_video_frame()

        except Exception as e:
            print(f"An error occurred while updating the frame: {e}")


    def get_contour(self,input_img):
        #choose image area from the circle_center
        
        _, thresh = cv2.threshold(input_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_circle_area = 100  # Adjust this value based on the size of the circles
        filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_circle_area]
        filtered_contours.sort(key=cv2.contourArea, reverse=True)
        sel_contour = filtered_contours[0]
        M = cv2.moments(sel_contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        return (cx,cy)
    def get_observe_pixel(self):
        if self.first_frame is not None:
            #self.analyzer = LineAnalyzer(self.first_frame, self.circles[4], self.radius)
            #self.line_pixels=self.analyzer.find_white_regions()#the first region is the center white circle
            self.plot_monitor_pixels_flag = 1
            #make a list, 

        pass