import time
import serial
import matplotlib.pyplot as plt
from PyQt5.QtGui import QPixmap
import os
import threading
from threading import Lock
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
class SensorManager:
    def __init__(self, parent):
        self.parent = parent
        self.serial_port = ''  # Will be set by user input
        self.serial_port_1 = ''
        self.baud_rate = 57600
        self.ser = None
        self.pressure_data, self.flow_data, self.rotate_data, self.vertical_data = [], [], [], []
        self.press_time,self.release_time = None,None
        self.lock = Lock()
        self.keyboard_return,self.keyboard_send = ['EBEB', 'BEBE'],'F1'
    
        self.rotate_return,self.rotate_send= ['ECEC', 'CECE'],'F3'
        self.pressure_return,self.pressure_send =['EDED', 'DEDE'],'F5' 
        self.flow_return,self.flow_send = ['EAEA', 'AEAE'],'F4'
        self.store_data_flag_1,self.store_data_flag_2 = False,False
        self.time_stamps, self.flow_data,self.pressure_data,self.rotate_data= [],[],[],[]
        # 存储按键及其按下和释放键值
        self.key_map = {
            'S1': {'press': 0x81, 'release': 0x01},
            'S2': {'press': 0x82, 'release': 0x02},
            'S3': {'press': 0x83, 'release': 0x03},
            'S4': {'press': 0x84, 'release': 0x04},
            'S5': {'press': 0x85, 'release': 0x05},
            'S6': {'press': 0x86, 'release': 0x06},
            'S7': {'press': 0x87, 'release': 0x07},
            'S8': {'press': 0x88, 'release': 0x08},
            'S9': {'press': 0x8B, 'release': 0x0B},
            'S10': {'press': 0x8C, 'release': 0x0C},
            'S11': {'press': 0x8D, 'release': 0x0D},
            'S12': {'press': 0x8E, 'release': 0x0E},
            'S13': {'press': 0x8F, 'release': 0x0F},
            'S14': {'press': 0x90, 'release': 0x10},
            'S15': {'press': 0x91, 'release': 0x11},
            'S16': {'press': 0x92, 'release': 0x12},
            'S17': {'press': 0x95, 'release': 0x15},
            'S18': {'press': 0x96, 'release': 0x16},
            'S19': {'press': 0x97, 'release': 0x17},
            'S20': {'press': 0x98, 'release': 0x18},
            'S21': {'press': 0x99, 'release': 0x19},
            'S22': {'press': 0x9A, 'release': 0x1A},
            'S23': {'press': 0xA0, 'release': 0x20},
            'S24': {'press': 0x9F, 'release': 0x1F},
            'S25': {'press': 0xA2, 'release': 0x22},
            'S26': {'press': 0xA1, 'release': 0x21},
            'S27': {'press': 0xA4, 'release': 0x24},
            'S28': {'press': 0xA3, 'release': 0x23},
            'S29': {'press': 0xA6, 'release': 0x26},
            'S30': {'press': 0xA5, 'release': 0x25},
            'S31': {'press': 0x9B, 'release': 0x1B},
            'S32': {'press': 0x9C, 'release': 0x1C},
            'S33': {'press': 0xC0, 'release': 0x40},
            'S34': {'press': 0xBF, 'release': 0x3F},
            'S35': {'press': 0xBD, 'release': 0x3D},
            'S36': {'press': 0xBE, 'release': 0x3E},
            'S37': {'press': 0xC4, 'release': 0x44},
            'S38': {'press': 0xC3, 'release': 0x43},
            'S39': {'press': 0xC1, 'release': 0x41},
            'S40': {'press': 0xC2, 'release': 0x42},
            'S41': {'press': 0xC8, 'release': 0x48},
            'S42': {'press': 0xC7, 'release': 0x47},
            'S43': {'press': 0xC5, 'release': 0x45},
            'S44': {'press': 0xC6, 'release': 0x46}
        }
        # Create a matplotlib figure and canvas
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.draw()

        # Convert the canvas to QPixmap and set it on QLabel "lblPressureGraph"

        # Plotting
        self.ax.set_title("Sensor Data")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Value")

        # Display the figure
        self.canvas.draw()
        pixmap = self.canvas.grab()
        self.lblPressureGraph.setPixmap(pixmap)
        self.parent.connect_button.clicked.connect(self.connect_to_sensor)
        # self.parent.btnResetSensor.clicked.connect(self.reset_all)
        self.parent.play_button_keyboard.clicked.connect(self.test_keyboard)  # Example sensor type
        self.parent.play_button_pressure.clicked.connect(self.test_pressure)  # Example sensor type
        self.parent.play_button_rotate.clicked.connect(self.test_rotate)  # Example sensor type
        self.parent.play_button_flow.clicked.connect(self.test_flow)  # Example sensor type
        # self.parent.btnEvaluatePressure.clicked.connect(self.evaluate_pressure)  # Example sensor type
        # self.update_pressure_plot()
    def __getattr__(self, name):
        """Delegate attribute access to the UI instance if not found in ConfigSystem."""
        return getattr(self.parent, name)

    def connect_to_sensor(self):
        self.serial_port_1, self.serial_port_2 = self.port_entry_1.text(), self.port_entry_2.text()

        # Connect to the first sensor
        try:
            self.ser_1 = serial.Serial(self.serial_port_1, baudrate=self.baud_rate, timeout=1)
            if self.ser_1.is_open:
                self.connect_status.setText("Port 1 is open")
                self.connect_status.setStyleSheet("color: green;")
                print(f"Connected to sensor at {self.serial_port_1}")
                self.listening_1 = True
                threading.Thread(target=self.run_listening_thread_1, daemon=True).start()
            else:
                self.connect_status.setText("Port 1 is not open")
                self.connect_status.setStyleSheet("color: red;")
                print(f"Failed to connect to sensor at {self.serial_port_1}")
        except serial.SerialException as e:
            self.connect_status.setText("Could not connect to Port 1")
            self.connect_status.setStyleSheet("color: red;")
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error in connect_to_sensor (Port 1): {e}")

        # Connect to the second sensor
        try:
            self.ser_2 = serial.Serial(self.serial_port_2, baudrate=self.baud_rate, timeout=1)
            if self.ser_2.is_open:
                self.connect_status.setText("Port 2 is open")
                self.connect_status.setStyleSheet("color: green;")
                print(f"Connected to sensor at {self.serial_port_2}")
                self.listening_2 = True
                threading.Thread(target=self.run_listening_thread_2, daemon=True).start()
            else:
                self.connect_status.setText("Port 2 is not open")
                self.connect_status.setStyleSheet("color: red;")
                print(f"Failed to connect to sensor at {self.serial_port_2}")
        except serial.SerialException as e:
            self.connect_status.setText("Could not connect to Port 2")
            self.connect_status.setStyleSheet("color: red;")
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error in connect_to_sensor (Port 2): {e}")

    def run_listening_thread_1(self):
        """Background thread to listen on Port 1 and handle exceptions."""
        while self.listening_1:
            try:
                with self.lock:  # Ensure thread-safe access to the serial port
                    if self.ser_1 and self.ser_1.is_open:
                        if self.ser_1.in_waiting > 0:
                            data = self.ser_1.read_all()
                            if hasattr(self, 'store_data_flag_1') and self.store_data_flag_1:
                                self.handle_valid_data(data)
            except serial.SerialException as e:
                print(f"SerialException occurred: {e}")
                self.listening_1 = False  # Stop listening to prevent repeated errors
            except OSError as e:
                print(f"OSError occurred: {e}")
                self.listening_1 = False  # Stop listening to prevent repeated errors
            except Exception as e:
                print(f"Unexpected error in run_listening_thread_1: {e}")
            time.sleep(0.5)  # Set a 0.5-second interval to reduce resource usage

    def run_listening_thread_2(self):
        """Background thread to listen on Port 2 and handle exceptions."""
        while self.listening_2:
            try:
                with self.lock:  # Ensure thread-safe access to the serial port
                    if self.ser_2 and self.ser_2.is_open:
                        if self.ser_2.in_waiting > 0:
                            data = self.ser_2.read_all()
                            if hasattr(self, 'store_data_flag_2') and self.store_data_flag_2:
                                self.handle_valid_data(data)
            except serial.SerialException as e:
                print(f"SerialException occurred: {e}")
                self.listening_2 = False  # Stop listening to prevent repeated errors
            except OSError as e:
                print(f"OSError occurred: {e}")
                self.listening_2 = False  # Stop listening to prevent repeated errors
            except Exception as e:
                print(f"Unexpected error in run_listening_thread_2: {e}")
            time.sleep(0.5)  # Set a 0.5-second interval to reduce resource usage

    def handle_valid_data(self, data):
        """Process valid data and safely update the UI."""
        try:
            if hasattr(self, 'sensor_type'):
                if self.sensor_type == 'F1':
                    if data.startswith(b'\xEB\xEB') and data.endswith(b'\xBE\xBE'):
                        self.parse_keyboard_data(data)
                elif self.sensor_type == 'F3':
                    if data.startswith(b'\xEC\xEC') and data.endswith(b'\xCE\xCE'):
                        self.parse_rotate_data(data)
                elif self.sensor_type == 'F4':
                    if data.startswith(b'\xEA\xEA') and data.endswith(b'\xAE\xAE'):
                        self.parse_flow_data(data)
                elif self.sensor_type == 'F5':
                    if data.startswith(b'\xED\xED') and data.endswith(b'\xDE\xDE'):
                        self.parse_pressure_data(data)
                else:
                    print("Unknown data format:", data)
            else:
                print("Sensor type not set.")
        except Exception as e:
            print(f"Error in handle_valid_data: {e}")





    def parse_keyboard_data(self, data):
        """Parse F1 format: EB EB n1 n2 BE BE and update the UI based on key values."""
        status = []
        try:
            # Ensure the data length is a multiple of 6 (each command is 6 bytes long)
            if len(data) % 6 != 0:
                print("Warning: Incomplete or invalid data length detected.")

            # Iterate through each 6-byte command sequence
            for i in range(0, len(data) - 5, 6):  # Step by 6 bytes to get each command
                command = data[i:i + 6]
                
                # Verify that it matches the expected format (EB EB n1 n2 BE BE)
                if command[0] == 0xEB and command[1] == 0xEB and command[-2] == 0xBE and command[-1] == 0xBE:
                    n1 = command[2]
                    n2 = command[3]

                    # Check the key_map for matching pressed or released keys
                    for key, values in self.key_map.items():
                        if n1 == values['press']:
                            status = 'press'
                            self.press_time  = time.time() - self.start_time
                            print(f"{key} pressed")
                            self.keyboard_val.setText(f"{key} pressed")
                            break
                        elif n1 == values['release']:
                            status = 'release'
                            self.release_time  = time.time() - self.start_time
                            print(f"{key} released")
                            self.keyboard_val.setText(f"{key} released")
                            break
                    else:
                        print(f"Unknown key code: {n1}")
                else:
                    print("Invalid F1 command format detected.")
        except Exception as e:
            print(f"Error in parse_keyboard_data: {e}")

        return key, status

    def parse_pressure_data(self, data):
        try:
            if len(data) >= 8:
                results, count, self.time_stamps = [], 0, []
                slice_length = 2  # Set the length of each slice, adjust as needed
                data_slices = [data[i:i+slice_length] for i in range(5, len(data)-3, slice_length)]

                for data_slice in data_slices:
                    result = 0
                    for byte in data_slice:
                        result = (result << 8) | byte  # Shift left by 8 bits and add the new byte
                    results.append(result)  # Append the converted integer to the results list
                    count += 1
                    self.time_stamps.append(0.01*count)
                print(f"Converted integers: {results}")
                self.pressure_data = results
                # Update UI or graph as needed
                self.update_plot()
        except Exception as e:
            print(f"Error in parse_pressure_data: {e}")

    def parse_rotate_data(self, data):
        try:
            if len(data) >= 8:
                self.time_stamps = []

                # Parse rotation angle data (bytes 2-3)
                rotate_value_raw = int.from_bytes(data[2:4], byteorder='big', signed=False)
                if rotate_value_raw & 0x8000:  # If the high bit is 1, it's negative
                    rotate_value = -(~rotate_value_raw & 0xFFFF) - 1
                else:
                    rotate_value = rotate_value_raw
                # Convert to millimeters (1 unit = 0.25 mm)
                rotate_position_mm = rotate_value * 0.25

                # Parse vertical displacement data (bytes 4-5)
                vertical_value_raw = int.from_bytes(data[4:6], byteorder='big', signed=False)
                if vertical_value_raw & 0x8000:  # If the high bit is 1, it's negative
                    vertical_value = -(~vertical_value_raw & 0xFFFF) - 1
                else:
                    vertical_value = vertical_value_raw
                # Convert to millimeters (1 unit = 0.25 mm)
                vertical_position_mm = vertical_value * 0.25

                # Get the current timestamp
                current_time = time.time() - self.start_time
                self.time_stamps.append(current_time)

                # Save parsed data
                self.rotate_data.append(rotate_position_mm)
                self.vertical_data.append(vertical_position_mm)  

                # Update GUI and plot
                print(f"Rotate Data -> Position (mm): {rotate_position_mm}")
                print(f"Vertical Data -> Position (mm): {vertical_position_mm}")
                self.rotate_val.setText(f"Rotate: {rotate_position_mm:.2f} mm")
                self.vertical_val.setText(f"Vertical: {vertical_position_mm:.2f} mm")  
                self.update_plot()
        except Exception as e:
            print(f"Error in parse_rotate_data: {e}")



    def parse_flow_data(self, data):
        try:
            if len(data) >= 8:
                results, count, self.time_stamps = [], 0, []
                slice_length = 2  # Set the length of each slice, adjust as needed
                data_slices = [data[i:i+slice_length] for i in range(5, len(data)-3, slice_length)]

                for data_slice in data_slices:
                    result = 0
                    for byte in data_slice:
                        result = (result << 8) | byte  # Shift left by 8 bits and add the new byte
                    results.append(result)  # Append the converted integer to the results list
                    count += 1
                    self.time_stamps.append(0.05*count)
                print(f"Converted integers: {results}")
                self.flow_data = results
                # Update UI or graph as needed
                self.update_plot()
        except Exception as e:
            print(f"Error in parse_flow_data: {e}")

    def close_hardware(self, sensor_type):
        try:
            if sensor_type.startswith("F1"):  # Example: Keyboard sensor
                self.send_sensor_command(self.ser_1, self.keyboard_send, 10, 0)
            elif sensor_type.startswith("F3"):  # Example: Pressure sensor
                self.send_sensor_command(self.ser_1, self.pressure_send, 10, 0)
            elif sensor_type.startswith("F4"):  # Example: Rotation sensor
                self.send_sensor_command(self.ser_1, self.rotate_send, 10, 0)
            elif sensor_type.startswith("F5"):  # Example: Flow sensor
                self.send_sensor_command(self.ser_1, self.flow_send, 10, 0)
        except Exception as e:
            print(f"Error in close_hardware: {e}")

    def update_plot(self):
        try:
            self.ax.clear()
            self.ax.set_title("Sensor Data")
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Value")
            
            if hasattr(self, 'pressure_data') and self.pressure_data:
                self.ax.plot(self.time_stamps, self.pressure_data, label='Pressure', color='blue')
            if hasattr(self, 'rotate_data') and self.rotate_data:
                self.ax.plot(self.time_stamps, self.rotate_data, label='Rotate', color='green')
            if hasattr(self, 'flow_data') and self.flow_data:
                self.ax.plot(self.time_stamps, self.flow_data, label='Flow', color='red')

            self.ax.legend()
            
            # Save the plot to a temporary file
            image_path = "temp_plot.png"
            self.fig.savefig(image_path)
            plt.close(self.fig)  # Close the figure to release resources

            # Create a QPixmap from the saved image
            pixmap = QPixmap(image_path)

            # Set the QPixmap to the QLabel
            self.parent.lblPressureGraph.setPixmap(pixmap)

            # Delete the temporary image file
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error in update_plot: {e}")

    def test_keyboard(self):
        try:
            print("Testing keyboard...")
            val = self.send_sensor_command(self.ser_2, self.keyboard_send, 10, 1)
            self.store_data_flag_2 = True
            self.keyboard_val.setText("Keyboard Test")
            return val
        except Exception as e:
            print(f"Error in test_keyboard: {e}")
            return None  # Indicate failure or an invalid result

    def test_pressure(self):
        try:
            print("Testing pressure...")
            self.start_time = time.time()
            val = self.send_sensor_command(self.ser_1, self.pressure_send, 15, 1)
            self.store_data_flag_1 = True
            self.pressure_val.setText("Pressure Test")
            return val
        except Exception as e:
            print(f"Error in test_pressure: {e}")
            return None  # Indicate failure or an invalid result

    def test_rotate(self):
        try:
            print("Testing rotate...")
            self.start_time = time.time()
            val = self.send_sensor_command(self.ser_1, self.rotate_send, 10, 1)
            self.store_data_flag_1 = True
            self.rotate_val.setText("Rotate Test")
            return val
        except Exception as e:
            print(f"Error in test_rotate: {e}")
            return None  # Indicate failure or an invalid result

    def test_flow(self):
        try:
            print("Testing flow...")
            self.start_time = time.time()
            val = self.send_sensor_command(self.ser_1, self.flow_send, 10, 1)
            self.store_data_flag_1 = True
            self.flow_val.setText("Flow Test")
            return val
        except Exception as e:
            print(f"Error in test_flow: {e}")
            return None  # Indicate failure or an invalid result

    def flip_hex_byte(self, byte):
        try:
            return ((byte & 0x0F) << 4) | ((byte & 0xF0) >> 4)
        except Exception as e:
            print(f"Error in flip_hex_byte: {e}")
            return None  # Return None to indicate an error occurred

    def wait_for_confirmation(self, sensor_type, send_status):
        """Wait and process confirmation packets from the hardware."""
        sensor_type_byte = int(sensor_type, 16)

        while True:
            try:
                if self.ser_1 and self.ser_1.is_open:
                    if self.ser_1.in_waiting >= 6:  # Check if there are at least 6 bytes available
                        response = self.ser_1.read(6)
                        if (response[0] == 0xEF and response[1] == 0xEF and
                                response[2] == self.flip_hex_byte(sensor_type_byte) and
                                response[3] == send_status and
                                response[4] == 0xFE and response[5] == 0xFE):
                            print("Immediate valid confirmation packet received:", response)
                            return True
                        else:
                            print("Invalid or unmatched confirmation packet received:", response)
                else:
                    print("Serial port not open or available.")
                    return False

                time.sleep(0.1)  # Small delay to prevent CPU overuse
            except Exception as e:
                print(f"Error in wait_for_confirmation: {e}")
                return False

    def send_sensor_command(self, ser_port, sensor_type, duration, send_status):
        try:
            # Send command
            header = [0xEF, 0xEF]
            tail = [0x0D, 0x0A]
            
            sensor_type_byte = int(sensor_type, 16)
            duration_byte = duration & 0xFF
            send_status_byte = 0x01 if send_status else 0x00
            
            packet = header + [sensor_type_byte, duration_byte, send_status_byte] + tail
            ser_port.reset_input_buffer()
            time.sleep(0.1)
            ser_port.write(bytes(packet))
            print(f"Sent command: {packet}")
            return self.wait_for_confirmation(sensor_type, send_status_byte)
        except Exception as e:
            print(f"Error in send_sensor_command: {e}")
            return None  # Indicate failure or an invalid result

    def on_closing(self):
        try:
            """Handle application closure by stopping listening threads and closing serial connections."""
            self.listening_1 = False
            self.listening_2 = False
            if self.ser_1 and self.ser_1.is_open:
                self.ser_1.close()
                print("Serial connection on Port 1 closed.")
            if self.ser_2 and self.ser_2.is_open:
                self.ser_2.close()
                print("Serial connection on Port 2 closed.")
            # Assuming a parent QWidget, call close() instead of quit()
            if hasattr(self, 'parent') and self.parent:
                self.parent.close()
        except Exception as e:
            print(f"Error in on_closing: {e}")



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
   