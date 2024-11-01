import os
import sys
import cv2
import pyttsx3
import time
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.uic import loadUi
from PyQt5.QtGui import QImage, QPixmap, QIcon
from sensor_management import SensorManager  # Import the SensorPage class
import resources_rc
import threading

class VideoPlayer(QMainWindow):
    def __init__(self, video_path, settings_data, user,test_category):
        super(VideoPlayer, self).__init__()
        loadUi("UIs/videoScreen.ui", self)
        self.user = user
        self.test_category=test_category
        
        self.video_path = video_path
        self.settings_data = settings_data
        self.video_frame = 0
        self.countdown_remaining = 0
        self.timer = QTimer()
        self.is_playing = True  # Initialize the playing state
        self.is_recording = False
        self.recording_thread = None
        self.recording_frame_count = 0
        
        # Initialize SensorManager
        self.sensor_manager = SensorManager(self)
        
        # Set up video display on lblVideo
        self.lblVideo.setAlignment(Qt.AlignCenter)
        self.lblVideo.setScaledContents(True)
        
        # Initialize video capture
        self.cap = cv2.VideoCapture(self.video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_delay = int(1000 / self.fps)
        
        # Connect timer for frame updates
        self.timer.timeout.connect(self.display_frame)
        self.timer.start(self.frame_delay)
        
        # Timer for countdown updates
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)
        
        # Connect btnPlayPause and btnCamera click events
        self.btnRecord.clicked.connect(self.toggle_recording)

        self.btnPlayPause.clicked.connect(self.toggle_play_pause)
        self.btnCamera.clicked.connect(self.capture_screenshot)
    def toggle_recording(self):
        if not self.is_recording:
            # Start recording
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self.record_video)
            self.recording_thread.start()
            self.btnRecord.setStyleSheet("margin: 5px;")  # Add margin to indicate recording
            self.display_message("Recording started")
        else:
            # Stop recording
            self.is_recording = False
            self.recording_thread.join()  # Wait for the thread to finish
            self.btnRecord.setStyleSheet("margin: 0;")  # Reset to default
            self.display_message("Recording stopped")
    
    def record_video(self):
        user_folder_name = f"{self.user['id']}_{self.user['username']}"
        date_today = datetime.now().strftime("%Y-%m-%d")
        folder_path = os.path.join("userData", user_folder_name, self.test_category, date_today)
        os.makedirs(folder_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Set up VideoWriter for recording
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        output_path = os.path.join(folder_path, f"recorded_{timestamp}.avi")
        writer = cv2.VideoWriter(output_path, fourcc, self.fps, (int(self.cap.get(3)), int(self.cap.get(4))))

        # Open a new capture for recording only
        cap_recording = cv2.VideoCapture(self.video_path)
        cap_recording.set(cv2.CAP_PROP_POS_FRAMES, self.video_frame)

        # Capture frames as long as is_recording is True and there are frames left
        while self.is_recording and cap_recording.isOpened():
            ret, frame = cap_recording.read()
            if not ret:
                break
            writer.write(frame)
            
            # Delay to simulate the frame rate and ensure real-time control
            time.sleep(1 / self.fps)

        # Release resources after recording
        cap_recording.release()
        writer.release()

        # Display message when recording is saved
        self.display_message(f"Video recording saved: recorded_{timestamp}.avi")


    def toggle_play_pause(self):
        if self.is_playing:
            self.timer.stop()
            self.btnPlayPause.setIcon(QIcon(":/images/images/icons8-play-25.png"))
            self.display_message("Video paused")
        else:
            self.timer.start(self.frame_delay)
            self.btnPlayPause.setIcon(QIcon(":/images/images/icons8-pause-25.png"))
            self.display_message("Video resumed")
        
        self.is_playing = not self.is_playing

    def display_message(self, message):
        self.lblMessage.setText(message)
        QTimer.singleShot(10000, self.clear_message)
    
    def clear_message(self):
        self.lblMessage.clear()

    def display_frame(self):
        if not self.is_playing:
            return
        
        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            self.cap.release()
            self.display_message("Video Finished")
            self.btnPlayPause.setIcon(QIcon(":/images/images/cil-media-play.png"))
            return

        frame = cv2.resize(frame, (720, 480))
        self.video_frame += 1
        
        # Update progress bar
        self.update_progress_bar()

        # Handle countdown and sensor prompts
        if self.video_frame in self.settings_data:
            setting = self.settings_data[self.video_frame]
            self.play_voice_prompt(setting["voice_prompt"])
            self.countdown_remaining = setting["countdown"]
            self.countdown_start_time = time.time()
            self.sensor_manager.start_sensor_reading(setting["sensor"], setting["countdown"])

        if self.countdown_remaining > 0:
            cv2.putText(frame, f"Countdown: {self.countdown_remaining} sec", 
                        (frame.shape[1] - 300, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        height, width, channel = frame.shape
        bytes_per_line = channel * width
        qt_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
        self.lblVideo.setPixmap(QPixmap.fromImage(qt_image))
        
    def update_progress_bar(self):
        progress = int((self.video_frame / self.total_frames) * 100)
        self.videoPrograssBar.setValue(progress)

    def update_countdown(self):
        if self.countdown_remaining > 0:
            self.countdown_remaining -= 1
        if self.countdown_remaining <= 0:
            self.countdown_remaining = 0

    def play_voice_prompt(self, voice_prompt):
        engine = pyttsx3.init()
        engine.say(voice_prompt)
        engine.runAndWait()

    def capture_screenshot(self):
        ret, frame = self.cap.read()
        if not ret:
            QMessageBox.warning(self, "Error", "Failed to capture frame.")
            return

        # Define paths based on user info and current date
        user_folder_name = f"{self.user['id']}_{self.user['username']}"
        test_category = self.test_category # Example category
        date_today = datetime.now().strftime("%Y-%m-%d")

        # Create folder path
        folder_path = os.path.join("userData", user_folder_name, test_category, date_today)
        os.makedirs(folder_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Save the frame as an image file
        image_path = os.path.join(folder_path, f"frame_{self.video_frame}_{timestamp}.png")
        cv2.imwrite(image_path, frame)
        self.display_message(f"Screenshot saved: frame_{self.video_frame}_{timestamp}.png")

    def closeEvent(self, event):
        if self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        event.accept()
