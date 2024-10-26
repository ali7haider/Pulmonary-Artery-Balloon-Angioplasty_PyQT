import numpy as np
import time
import serial
from scipy.integrate import simps
import matplotlib.pyplot as plt
from PyQt5.QtGui import QPixmap
import os

class SensorManager:
    def __init__(self, parent):
        self.parent = parent
        self.serial_port = ''  # Will be set by user input
        self.baud_rate = 9600  # Update with your baud rate
        self.ser = None
        self.pressure_data = []
        self.reference_curve = []
        self.key_type = 'S1'
        self.X_type = 'S2'
        self.tube_rotate_type = 'S3'
        self.pressure_type = 'S4'
        self.flow_type = 'S5'

    def connect_to_sensor(self, port):
        self.serial_port = port
        
        try:
            self.ser = serial.Serial(self.serial_port, baudrate=self.baud_rate, timeout=1)
            if self.ser.is_open:
                self.parent.lblConnectStatus.setText("port is open")
                self.parent.lblConnectStatus.setStyleSheet("color: green;")
                print(f"Connected to sensor at {self.serial_port}")
            else:
                self.parent.lblConnectStatus.setText("port is not open")
                self.parent.lblConnectStatus.setStyleSheet("color: red;")
        except serial.SerialException as e:
            self.parent.lblConnectStatus.setText("could not connect")
            self.parent.lblConnectStatus.setStyleSheet("color: red;")
            print(f"Error: {e}")

    def reset_all(self):
        self.pressure_data = []
        # self.update_pressure_plot()
        self.parent.txtPressureVal.setText("0")
        self.parent.txtXrayOnVal.setText("off")
        self.parent.txtXrayOffVal.setText("on")
        self.parent.lblPositionVal.setText("up")
        self.parent.lblConnectStatus.setText("not connected")
        self.parent.lblConnectStatus.setStyleSheet("color: red;")
        print("Reset all displays")

    def test_pressure(self):
        print("Testing pressure...")
        # Simulate pressure test status
        self.parent.txtPressureVal.setText("Pressure Test")
        self.start_sensor_reading(self.pressure_type,10)

    def start_sensor_reading(self, sensor_type, sensor_time):
        if self.ser and self.ser.is_open:
            try:
                command = f"{sensor_type} START {sensor_time}\n"
                self.ser.write(command.encode('utf-8'))
                print(f"Command sent: {command.strip()}")

                start_time = time.time()
                confirmation = ""

                while time.time() - start_time < 2:
                    confirmation = self.ser.readline().decode('utf-8').strip()
                    if confirmation:
                        break

                if confirmation == "OK":
                    print("Device confirmed receipt of command")
                    time.sleep(sensor_time)
                    self.receive_sensor_data()
                else:
                    print(f"Did not receive correct confirmation; received: {confirmation if confirmation else 'no response'}")
            except serial.SerialException as e:
                print(f"Serial communication error: {e}")
        else:
            print("Sensor not connected, please connect")


    def receive_sensor_data(self):
        try:
            if self.ser.is_open:
                data = self.ser.read_all().decode('utf-8')
                print(f"Received data: {data}")
                # Process the received data and update pressure data
                # self.pressure_data = self.process_data(data)  # Implement your data processing logic
                # self.update_pressure_plot()
            else:
                print("Serial port is not open")
        except serial.SerialException as e:
            print(f"Error receiving data: {e}")
    def test_xray_on(self):
        print("Testing X-ray on...")
        # Simulate X-ray on status
        self.parent.txtXrayOnVal.setText("open")

    def test_xray_off(self):
        print("Testing X-ray off...")
        # Simulate X-ray off status
        self.parent.txtXrayOffVal.setText("closed")
    def show_position(self):
            print("Showing position...")
            # Simulate position status
            self.parent.lblPositionVal.setText("down")

    def evaluate_pressure(self):
        if len(self.pressure_data) == 0 or len(self.reference_curve) == 0:
            self.parent.txtEvaluationResult.setText("No data to evaluate.")
            return
        
        area_new = simps(self.pressure_data)
        area_ref = simps(self.reference_curve)
        area_diff = abs(area_new - area_ref) / area_ref
        
        max_new = max(self.pressure_data)
        max_ref = max(self.reference_curve)
        max_diff = abs(max_new - max_ref) / max_ref

        result_text = f"Area Diff: {area_diff:.2f}\nMax Diff: {max_diff:.2f}"
        self.parent.txtEvaluationResult.setText(result_text)
        print(f"Evaluation Results - Area Diff: {area_diff:.2f}, Max Diff: {max_diff:.2f}")

    def update_pressure_plot(self):
        # Create a new figure and axis for the pressure plot
        fig, ax = plt.subplots(figsize=(8, 6))  # Set a larger figure size for better resolution

        # Plot reference curve if available
        if len(self.reference_curve) > 0:
            x_ref = np.linspace(0, len(self.reference_curve), len(self.reference_curve))
            ax.plot(x_ref, self.reference_curve, 'r--', label="Reference Curve")

        # Plot pressure data if available
        if len(self.pressure_data) > 0:
            x_data = np.linspace(0, len(self.pressure_data), len(self.pressure_data))
            ax.plot(x_data, self.pressure_data, 'g-', label="New Pressure Data")

        # Set titles and labels
        ax.set_title("Pressure Data (Gaussian Distribution)")
        ax.set_xlabel("Time")
        ax.set_ylabel("Pressure")
        # Add a legend if there are any labels to display
        handles, labels = ax.get_legend_handles_labels()
        if handles:  # Only create a legend if there are handles
            ax.legend(handles, labels)

        # Save the figure as an image
        image_path = 'pressure.png'
        fig.savefig(image_path, bbox_inches='tight')
        plt.close(fig)  # Close the figure after saving to release resources

        # Create a QPixmap from the saved image
        pixmap = QPixmap(image_path)

        # Set the QPixmap to a QLabel (assuming you have a QLabel named "lblPressureGraph")
        self.parent.lblPressureGraph.setPixmap(pixmap)

        # Delete the image from the local directory
        if os.path.exists(image_path):
            os.remove(image_path)



    def set_reference_curve(self):
        mu, sigma = 60, 12  # Mean and standard deviation for reference
        x = np.linspace(mu - 4 * sigma, mu + 4 * sigma, 100)
        self.reference_curve = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
        self.update_pressure_plot()
        print("Reference curve set.")
    def plot_curve(self,data):
        # Set the reference curve to be used for comparison
        mu, sigma = 60, 12  # Mean and standard deviation for reference
        x = np.linspace(mu - 4*sigma, mu + 4*sigma, 100)
        self.reference_curve = (1/(sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
        self.update_pressure_plot()
        print("Reference curve set.")