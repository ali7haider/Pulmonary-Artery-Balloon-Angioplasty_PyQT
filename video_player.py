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
from PyQt5.QtCore import QThread, pyqtSignal

class VideoPlayer(QMainWindow):
    recording_status_changed = pyqtSignal(str)  # Signal to indicate recording status

    def __init__(self, video_path, settings_data, user,test_category,test_subject):
        super(VideoPlayer, self).__init__()
        loadUi("UIs/videoScreen.ui", self)
        self.user = user
        self.test_category=test_category
        self.test_subject=test_subject
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
        # Connect the new signal to a method (optional)
        self.recording_status_changed.connect(self.handle_recording_status)

        # Connect button clicks to their respective methods
        self.btnStepBackward.clicked.connect(self.step_backward)
        self.btnStepUpward.clicked.connect(self.step_forward)
        self.btnEnd.clicked.connect(self.stop_video)
        self.btnZoomIn.clicked.connect(self.zoom_in_video)
        self.btnZoomOut.clicked.connect(self.zoom_out_video)

    def zoom_in_video(self):
        print("Zoom In Video")

    def zoom_out_video(self):
        print("Zoom Out Video")
        

    def step_backward(self):
        if not self.is_recording:
            # Calculate frame position 2 seconds back
            new_frame_position = max(0, self.video_frame - int(2 * self.fps))
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame_position)
            self.video_frame = new_frame_position  # Update current frame tracker
            self.display_message("Moved 2 seconds backward")
        else:
            self.display_message("Cannot move backward while recording is active")

    def step_forward(self):
        if not self.is_recording:
            # Calculate frame position 2 seconds forward
            new_frame_position = min(self.total_frames, self.video_frame + int(2 * self.fps))
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame_position)
            self.video_frame = new_frame_position  # Update current frame tracker
            self.display_message("Moved 2 seconds forward")
        else:
            self.display_message("Cannot move forward while recording is active")

    def stop_video(self):
        if not self.is_recording:
            self.timer.stop()
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset video to the start
            self.video_frame = 0  # Reset frame counter
            self.videoPrograssBar.setValue(0)
            self.display_message("Video stopped and reset to the beginning")
            self.btnPlayPause.setIcon(QIcon(":/images/images/icons8-play-25.png"))
            self.is_playing=False

        else:
            self.display_message("Cannot stop the video while recording is active")
    def toggle_recording(self):
        if not self.is_recording:
            # Start recording
            self.is_recording = True
            user_folder_name = f"{self.user['id']}_{self.user['username']}"
            self.recording_thread = RecordingThread(
                self.video_path, self.video_frame, user_folder_name, self.fps, 
                int(self.cap.get(3)), int(self.cap.get(4)),  # Pass width and height
                self.test_category,self.test_subject
            )
            self.recording_thread.recording_saved.connect(self.on_recording_saved)  # Connect the signal
            self.recording_thread.start()
            
            # Emit signal for recording start
            self.recording_status_changed.emit("Recording started")
            self.btnRecord.setStyleSheet("margin: 5px;")  # Start recording indication
        else:
            # Stop recording
            self.is_recording = False
            if self.recording_thread.isRunning():
                self.recording_thread.stop()
                self.recording_thread.wait()
            
            # Emit signal for recording stop
            self.recording_status_changed.emit("Recording stopped")
            self.btnRecord.setStyleSheet("margin: 0;")  # End recording indication
            self.display_message("Recording stopped")

    def on_recording_saved(self, message):
        """Handle the recording saved signal from the thread."""
        self.is_recording = False  # Update the recording status
        self.btnRecord.setStyleSheet("margin: 0;")  # End recording indication

        self.display_message(message)  # Display message with saved recording info

    def handle_recording_status(self, status_message):
        # Handle the recording status change (e.g., display a message)
        self.display_message(status_message)
    def record_video(self):
        user_folder_name = f"{self.user['id']}_{self.user['username']}"
        date_today = datetime.now().strftime("%Y-%m-%d")
        folder_path = os.path.join("userData", user_folder_name, self.test_category, self.test_subject, date_today)
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
            self.btnPlayPause.setIcon(QIcon(":/images/images/icons8-play-25.png"))
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

        # Define paths based on user info, test category, test subject, and current date
        user_folder_name = f"{self.user['id']}_{self.user['username']}"
        sanitized_user_folder = user_folder_name.strip()
        sanitized_test_category = self.test_category.strip()
        sanitized_test_subject = self.test_subject.strip()
        date_today = datetime.now().strftime("%Y-%m-%d")

        # Create folder path with test_subject as a subfolder
        folder_path = os.path.join("userData", sanitized_user_folder, sanitized_test_category, sanitized_test_subject, date_today)
        os.makedirs(folder_path, exist_ok=True)  # This will create the full path if it doesn't exist

        # Generate a unique timestamp for the image file name
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
class RecordingThread(QThread):
    recording_saved = pyqtSignal(str)  # Signal to emit when recording is done

    def __init__(self, video_path, frame_start, user_folder, fps, width, height, test_category,test_subject):
        super().__init__()
        self.video_path = video_path
        self.frame_start = frame_start
        self.user_folder = user_folder
        self.fps = fps
        self.width = width  # Store width
        self.height = height  # Store height
        self.test_category = test_category
        self.test_subject=test_subject
        self.is_recording = True

    def run(self):
        date_today = datetime.now().strftime("%Y-%m-%d")
        # Strip whitespace from user folder and test category names to prevent issues
        sanitized_user_folder = self.user_folder.strip()
        sanitized_test_category = self.test_category.strip()
        sanitized_test_subject = self.test_subject.strip()
        folder_path = os.path.join("userData", sanitized_user_folder, sanitized_test_category,sanitized_test_subject, date_today)
        os.makedirs(folder_path, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = os.path.join(folder_path, f"recorded_{timestamp}.avi")
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        writer = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))

        cap_recording = cv2.VideoCapture(self.video_path)
        cap_recording.set(cv2.CAP_PROP_POS_FRAMES, self.frame_start)

        while self.is_recording and cap_recording.isOpened():
            ret, frame = cap_recording.read()
            if not ret:
                break
            writer.write(frame)
            time.sleep(1 / self.fps)

        cap_recording.release()
        writer.release()
        self.recording_saved.emit(f"Recording Saved: recorded_{timestamp}.avi")  # Emit signal with path

    def stop(self):
        self.is_recording = False
