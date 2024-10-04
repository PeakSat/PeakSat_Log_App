import tkinter.messagebox
import customtkinter
import serial
import serial.tools.list_ports
import re
from PIL import Image
import os
import subprocess
from datetime import datetime

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

selected_file = "None"
playback_mode = False

save_logs           = False
output_logs_folder  = "logFiles"
output_filename     = "out.txt"

ser                 = None
serial_port_name    = None
serial_port_status  = False

timekeeper  = 0
mcu_temp    = 0
amb_temp_a  = 0
amb_temp_b  = 0
wdtimer     = 0
obtimer     = "-"

def generate_timestamped_filename():
    # Get the current date and time
    current_time = datetime.now()
    
    # Format the date and time as day_month_year_hour_minute
    formatted_time = current_time.strftime("%d_%m_%y_%H_%M")
    
    # Append ".txt" to the formatted string
    filename = f"{formatted_time}.txt"
    
    return filename

def connect_to_serial(port):
    print("Connecting to: "+port)
    global serial_port_name
    global serial_port_status
    global ser
    if ser:
        disconnect_from_serial()

    try:
        ser = serial.Serial(port, 115200, timeout=2)
        serial_port_name = port
        serial_port_status = True
        print("Connected")
    except Exception as e:
        print(f"Error connecting to serial port: {e}")

def disconnect_from_serial():
    global ser
    global serial_port_status

    if ser is not None:
        ser.close()
        ser = None
        serial_port_status = False
    #print("Disconnected from serial port")

def getPorts():
    av_ports = serial.tools.list_ports.comports()
    serial_ports = []
    for port in av_ports:
        if port.description != "n/a":
            serial_ports.append(port.device)
    return serial_ports

def readFromSerial():
    global serial_port_status
    global ser

    if serial_port_status:
        line = ser.readline().decode('utf-8').strip()
        line = line+"\n"
        return line
    return "Disconnected\n"

def getAvailableFiles():
    current_dir = os.path.dirname(__file__)
    logs_folder_path = os.path.join(current_dir, "logFiles")
    return os.listdir(logs_folder_path)

def read_file_line_by_line(file_path):
    def inner_reader():
        with open(file_path, 'r') as file:
            for line in file:
                yield line

    # Create and return the generator
    generator = inner_reader()
    
    def read_next_line():
        try:
            return next(generator)
        except StopIteration:
            return None  # Return None when EOF is reached
    
    return read_next_line

line_reader = read_file_line_by_line("logFiles/file_a.txt")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("OBC Monitor App")
        self.minsize(1200, 750)
        self.maxsize(1300, 900)
        # self.geometry(f"{1100}x{580}")

        dashboard_font = customtkinter.CTkFont(family='Helvetica', size=20)
        OBTime_font = customtkinter.CTkFont(family='Helvetica', size=18)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure((0, 1), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(12, weight=1)

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="OBC Monitor", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="Available ports", anchor="w")
        self.scaling_label.grid(row=1, column=0, padx=20, pady=(50, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=getPorts(),
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=2, column=0, pady=10)
        
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, command=self.sidebar_connect_event, text="Connect serial")
        self.sidebar_button_1.grid(row=3, column=0, padx=20, pady=10)
        
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, command=self.sidebar_disconnect_event, text="Disconnect serial")
        self.sidebar_button_2.grid(row=4, column=0, padx=20, pady=10)

        self.save_logs_checkbox = customtkinter.CTkCheckBox(self.sidebar_frame, text="Save logs", command=self.save_logs_callback)
        self.save_logs_checkbox.grid(row=5, column=0, padx=0, pady=10)

        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="Available files", anchor="w")
        self.scaling_label.grid(row=6, column=0, pady=(50, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=getAvailableFiles(),
                                                               command=self.select_file_event)
        self.scaling_optionemenu.grid(row=7, column=0, pady=10)

        self.sidebar_button_plot_file = customtkinter.CTkButton(self.sidebar_frame, command=self.plot_button_event, text="Plot file")
        self.sidebar_button_plot_file.grid(row=8, column=0, padx=20, pady=10)

        self.sidebar_button_play_file = customtkinter.CTkButton(self.sidebar_frame, command=self.play_button_event, text="Replay file")
        self.sidebar_button_play_file.grid(row=9, column=0, padx=20, pady=10)
         
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode", anchor="w")
        self.appearance_mode_label.grid(row=10, column=0, padx=20, pady=(80, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=11, column=0, pady=10)

        # create textbox frame
        self.textbox_frame = customtkinter.CTkFrame(self, width=1000, corner_radius=0, fg_color="transparent")
        self.textbox_frame.grid(row=0, column=1, sticky="nsew")
        self.textbox_frame.grid_rowconfigure((0, 1), weight=1)
        self.textbox_frame.grid_columnconfigure(0, weight=1)
        # create textbox
        self.textbox = customtkinter.CTkTextbox(self.textbox_frame, width=770, height=400)
        self.textbox.grid(row=1, column=0, padx=(10, 0), pady=(10, 10), sticky="nsew")
        self.textboxlabel = customtkinter.CTkLabel(self.textbox_frame, font=dashboard_font, text="Serial Monitor")
        self.textboxlabel.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="nsew")


        # create main dashboard frame
        self.main_dashboard_frame = customtkinter.CTkFrame(self, width=1000, fg_color="transparent")
        self.main_dashboard_frame.grid(row=1, column=1, padx=(0, 0), pady=(0, 0), sticky="nsew")
        self.textbox_frame.grid_columnconfigure((0, 1), weight=0)
        self.textbox_frame.grid_columnconfigure(2, weight=1)
        self.textbox_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.mcuTempDisplay = customtkinter.CTkTextbox(self.main_dashboard_frame, width=170, height=50, font=dashboard_font)
        self.mcuTempDisplay.grid(row=1, column=0, padx=(10, 10), pady=(0, 0), sticky="nsew")
        self.mcutemplabel = customtkinter.CTkLabel(self.main_dashboard_frame, text="MCU Temp")
        self.mcutemplabel.grid(row=0, column=0, padx=(10, 10), pady=(0 ,0), sticky="nsew")

        self.ambSensOne = customtkinter.CTkTextbox(self.main_dashboard_frame, width=170, height=50, font=dashboard_font)
        self.ambSensOne.grid(row=1, column=1, padx=(10, 10), pady=(0, 0), sticky="nsew")
        self.ambSensOnelabel = customtkinter.CTkLabel(self.main_dashboard_frame, text="Amb Sens 1")
        self.ambSensOnelabel.grid(row=0, column=1, padx=(10, 10), pady=(0 ,0), sticky="nsew")

        self.ambSensTwo = customtkinter.CTkTextbox(self.main_dashboard_frame, width=170, height=50, font=dashboard_font)
        self.ambSensTwo.grid(row=3, column=1, padx=(10, 10), pady=(0, 0), sticky="nsew")
        self.ambSensTwolabel = customtkinter.CTkLabel(self.main_dashboard_frame, text="Amb Sens 2")
        self.ambSensTwolabel.grid(row=2, column=1, padx=(10, 10), pady=(0 ,0), sticky="nsew")

        self.currentRuntime = customtkinter.CTkTextbox(self.main_dashboard_frame, width=170, height=50, font=dashboard_font)
        self.currentRuntime.grid(row=3, column=0, padx=(10, 10), pady=(0, 0), sticky="nsew")
        self.currentRuntimelabel = customtkinter.CTkLabel(self.main_dashboard_frame, text="Runtime")
        self.currentRuntimelabel.grid(row=2, column=0, padx=(10, 10), pady=(0 ,0), sticky="nsew")

        self.onBoardTime = customtkinter.CTkTextbox(self.main_dashboard_frame, width=170, height=50, font=OBTime_font)
        self.onBoardTime.grid(row=5, column=0, padx=(10, 10), pady=(0, 0), sticky="nsew")
        self.onBoardTimelabel = customtkinter.CTkLabel(self.main_dashboard_frame, text="On Board Time")
        self.onBoardTimelabel.grid(row=4, column=0, padx=(10, 10), pady=(0 ,0), sticky="nsew")

        self.WDReset = customtkinter.CTkTextbox(self.main_dashboard_frame, width=170, height=50, font=dashboard_font)
        self.WDReset.grid(row=5, column=1, padx=(10, 10), pady=(0, 0), sticky="nsew")
        self.WDResetlabel = customtkinter.CTkLabel(self.main_dashboard_frame, text="Last WD Reset")
        self.WDResetlabel.grid(row=4, column=1, padx=(10, 10), pady=(0 ,0), sticky="nsew")

        # create console output frame
        self.console_frame = customtkinter.CTkFrame(self.main_dashboard_frame, width=1000, fg_color="transparent")
        self.console_frame.grid(row=1, column=2, rowspan=5, padx=(0, 0), pady=(0, 0), sticky="nsew")
        self.console_frame.rowconfigure(0, weight=1)
        self.console_frame.columnconfigure(0, weight=1)
        
        self.output = customtkinter.CTkTextbox(self.console_frame, width=400)
        self.output.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="nsew")
        self.outputlabel = customtkinter.CTkLabel(self.main_dashboard_frame, text="Console Output")
        self.outputlabel.grid(row=0, column=2, padx=(0, 0), pady=(0 ,0), sticky="nsew")

        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
        self.displayImage = customtkinter.CTkImage(Image.open(os.path.join(image_path, "peaksat_patch_full_2x.png")), size=(250, 250))
        self.frame_image = customtkinter.CTkLabel(self, image=self.displayImage, text="")
        self.frame_image.grid(row=1, column=2, padx=(10, 10), pady=(10, 20), sticky="nsew")

        # create checkbox and switch frame
        self.checkbox_slider_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0, fg_color="transparent")
        self.checkbox_slider_frame.grid(row=0, column=2, padx=(20, 20), pady=(20, 0), sticky="nsew")

        self.boxMRAM = customtkinter.CTkLabel(self.checkbox_slider_frame, text="       ", bg_color="red", corner_radius=5)
        self.boxMRAM.grid(row=0, column=0, padx=(10, 10), pady=(30, 30))
        self.boxMRAMlabel = customtkinter.CTkLabel(self.checkbox_slider_frame, text="MRAM", bg_color="transparent")
        self.boxMRAMlabel.grid(row=0, column=1, padx=(5, 10), pady=(30, 30))

        self.boxNAND = customtkinter.CTkLabel(self.checkbox_slider_frame, text="       ", bg_color="red", corner_radius=5)
        self.boxNAND.grid(row=1, column=0, padx=(10, 10), pady=(10, 30))
        self.boxNANDlabel = customtkinter.CTkLabel(self.checkbox_slider_frame, text="NAND", bg_color="transparent")
        self.boxNANDlabel.grid(row=1, column=1, padx=(5, 10), pady=(10, 30))

        self.boxCANMain = customtkinter.CTkLabel(self.checkbox_slider_frame, text="       ", bg_color="red", corner_radius=5)
        self.boxCANMain.grid(row=2, column=0, padx=(10, 10), pady=(10, 30))
        self.boxCANMainlabel = customtkinter.CTkLabel(self.checkbox_slider_frame, text="CAN M", bg_color="transparent")
        self.boxCANMainlabel.grid(row=2, column=1, padx=(5, 10), pady=(10, 30))

        self.boxCANRed = customtkinter.CTkLabel(self.checkbox_slider_frame, text="       ", bg_color="red", corner_radius=5)
        self.boxCANRed.grid(row=3, column=0, padx=(10, 10), pady=(10, 30))
        self.boxCANRedlabel = customtkinter.CTkLabel(self.checkbox_slider_frame, text="CAN R", bg_color="transparent")
        self.boxCANRedlabel.grid(row=3, column=1, padx=(5, 10), pady=(10, 30))


        # Initial Values
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("-")
        self.textbox.insert("0.0", "Logs Start")

    def updateMRAMCheckbox(self, status):
        self.boxMRAM.destroy()
        if status:
            self.boxMRAM = customtkinter.CTkLabel(self.checkbox_slider_frame, text="       ", bg_color="green", corner_radius=5)
        else:
            self.boxMRAM = customtkinter.CTkLabel(self.checkbox_slider_frame, text="       ", bg_color="red", corner_radius=5)
        self.boxMRAM.grid(row=0, column=0, padx=(10, 10), pady=(30, 30))

    def updateNANDCheckbox(self, status):
        self.boxNAND.destroy()
        if status:
            self.boxNAND = customtkinter.CTkLabel(self.checkbox_slider_frame, text="       ", bg_color="green", corner_radius=5)
        else:
            self.boxNAND = customtkinter.CTkLabel(self.checkbox_slider_frame, text="       ", bg_color="red", corner_radius=5)
        self.boxNAND.grid(row=1, column=0, padx=(10, 10), pady=(10, 30))

    def updateCANMainCheckbox(self, status):
        self.boxCANMain.destroy()
        if status:
            self.boxCANMain = customtkinter.CTkLabel(self.checkbox_slider_frame, text="       ", bg_color="green", corner_radius=5)
        else:
            self.boxCANMain = customtkinter.CTkLabel(self.checkbox_slider_frame, text="       ", bg_color="red", corner_radius=5)
        self.boxCANMain.grid(row=2, column=0, padx=(10, 10), pady=(10, 30))

    def updateCANRedCheckbox(self, status):
        self.boxCANRed.destroy()
        if status:
            self.boxCANRed = customtkinter.CTkLabel(self.checkbox_slider_frame, text="       ", bg_color="green", corner_radius=5)
        else:
            self.boxCANRed = customtkinter.CTkLabel(self.checkbox_slider_frame, text="       ", bg_color="red", corner_radius=5)
        self.boxCANRed.grid(row=3, column=0, padx=(10, 10), pady=(10, 30))


    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_port: str):
        global serial_port_name 
        serial_port_name = new_port
        self.updateConsoleTextbox("Selected port: "+ (serial_port_name))

    def select_file_event(self, new_file: str):
        global selected_file 
        selected_file = new_file
        self.updateConsoleTextbox("Selected file: "+ (selected_file))

    def sidebar_connect_event(self):
        global serial_port_name
        connect_to_serial(serial_port_name)
        self.textbox.after(150, self.updateLogsTextbox)
    
    def writeToOutput(self, newLine):
        global output_logs_folder
        global output_filename
        output_f = os.path.join(output_logs_folder, output_filename)
        with open(output_f, "a") as file:
            file.write(f'{timekeeper}')
            file.write('\t')
            file.write(newLine)
        file.close()

    def play_button_event(self):
        global playback_mode
        global selected_file
        global line_reader
        current_dir = os.path.dirname(__file__)
        logs_folder_path = os.path.join(current_dir, "logFiles")
        file_path = os.path.join(logs_folder_path, selected_file)
        line_reader = read_file_line_by_line(file_path)
        playback_mode = True
        self.textbox.after(100, self.updateLogsTextbox)

    def plot_button_event(self):
        global selected_file
        current_dir = os.path.dirname(__file__)
        logs_folder_path = os.path.join(current_dir, "logFiles")
        file_path = os.path.join(logs_folder_path, selected_file)
        command = ["python", "fileParser.py", selected_file]
        result = subprocess.run(command, capture_output=True, text=True)
        if(result.returncode == 0):
            self.updateConsoleTextbox(result.stdout)
            parsed_file = "out_"+selected_file
            command = ["python", "visualize_logs.py", parsed_file]
            result = subprocess.run(command, capture_output=True, text=True)
            if(result.returncode == 0):
                self.updateConsoleTextbox(result.stdout)
            else:
                self.updateConsoleTextbox("Error ploting the file")
        else:
            self.updateConsoleTextbox("Error parsing the file")

    def save_logs_callback(self):
        global save_logs
        global output_filename
        output_filename = generate_timestamped_filename()
        save_logs = self.save_logs_checkbox.get()
        if(save_logs):
            self.updateConsoleTextbox("Saving logs to file: "+str(output_filename))
        else:
            self.updateConsoleTextbox("Stopped saving logs")

    def sidebar_disconnect_event(self):
        disconnect_from_serial()
        self.textbox.after_cancel()

    def updateLogsTextbox(self):
        global serial_port_status
        global playback_mode
        global save_logs
        if(playback_mode):
            newLog = line_reader()
            if(newLog is None):
                self.textbox.insert("end", "END OF FILE\n\n")
                self.textbox.yview("end")
                playback_mode = False
            else:
                self.parse_log_entry(newLog)
                self.textbox.insert("end", newLog)
                self.textbox.yview("end")
                self.textbox.after(100, self.updateLogsTextbox)
        else:
            newLog = readFromSerial()
            #print("New log: "+newLog)
            self.textbox.insert("end", newLog)
            self.textbox.yview("end")
            if serial_port_status:
                self.parse_log_entry(newLog)
                self.textbox.after(150, self.updateLogsTextbox)
                if save_logs:
                    self.writeToOutput(newLog)


    def updateConsoleTextbox(self, log):
        log = log+"\n"
        self.output.insert("end", log)
        self.output.yview("end")

    def updateRuntime(self, milliseconds):
        global timekeeper
        if(milliseconds < timekeeper):
            self.handleReset(timekeeper)
        timekeeper = milliseconds
        self.currentRuntime.delete("1.0", customtkinter.END)
        seconds = milliseconds // 1000
        remaining_milliseconds = milliseconds % 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        runtime = f"{int(hours):03}:{int(minutes):02}:{int(seconds):02}:{int(remaining_milliseconds):03}"
        self.currentRuntime.insert("0.0", runtime)

    def handleReset(self, milliseconds):
        global mcu_temp, amb_temp_a, amb_temp_b, wdtimer, obtimer
        resetMessage = f"***Reset detected***\nRuntime: {milliseconds} ms\nMCU Temp: {mcu_temp}\nTemp S0: {amb_temp_a}\nTemp S1: {amb_temp_b}\nLast WDRST: {wdtimer} ms\nOB time: {obtimer}\n*** *** ***"
        self.updateConsoleTextbox(resetMessage)

    def handle_new_tm_message(self, rest_of_log):
        return
        self.updateConsoleTextbox(f"TM message: {rest_of_log}")

    def handle_payload_message(self, rest_of_log):
        self.updateConsoleTextbox(f"Sent payload message")

    def handle_watchdog_message(self, milliseconds):
        global wdtimer
        wdtimer = milliseconds
        self.WDReset.delete("1.0", customtkinter.END)
        seconds = milliseconds // 1000
        remaining_milliseconds = milliseconds % 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        runtime = f"{int(hours):03}:{int(minutes):02}:{int(seconds):02}:{int(remaining_milliseconds):03}"
        self.WDReset.insert("0.0", runtime)
        

    def handle_time_log(self, rest_of_log):
        global obtimer
        obtimer = rest_of_log[5:].strip()
        self.onBoardTime.delete("1.0", customtkinter.END)
        self.onBoardTime.insert("0.0", rest_of_log[5:].strip())

    def handle_mcu_temp_log(self, rest_of_log):
        global mcu_temp
        self.mcuTempDisplay.delete("1.0", customtkinter.END)
        match = re.search(r"[-+]?\d*\.\d+|\d+", rest_of_log)
        if match:
            mcu_temp = match.group()
        else:
            mcu_temp = "??"
        mcu_temp = mcu_temp+" C"
        self.mcuTempDisplay.insert("0.0", mcu_temp)

    def handle_ambient_temp_log(self, rest_of_log):
        global amb_temp_a, amb_temp_b
        match = re.search(r"address\s+(\d+)\s+.*temperature\s*=\s*([-+]?\d*\.\d+|\d+)", rest_of_log)
    
        if match:
            address = int(match.group(1))      # Extract the address (integer)
            temperature = match.group(2) + " C"
            if address:
                amb_temp_a = temperature
                self.ambSensOne.delete("1.0", customtkinter.END)
                self.ambSensOne.insert("0.0", temperature)
            else:
                amb_temp_b = temperature
                self.ambSensTwo.delete("1.0", customtkinter.END)
                self.ambSensTwo.insert("0.0", temperature)

    def parse_log_entry(self, log_entry):
        # Regular expression to extract milliseconds value and the rest of the log
        log_entry = log_entry[1:].strip()
        pattern = r'^(\d+)\s+\[([^\]]+)\]\s+OBC\s+(.*)$'
        match = re.match(pattern, log_entry)
        
        if match:
            milliseconds = int(match.group(1))
            rest_of_log = match.group(3)
            self.updateRuntime(milliseconds)
            
            # Check the specific log content for categorization
            if "New TM" in rest_of_log:
                self.handle_new_tm_message(rest_of_log)
            elif "Sent CAN message to main CAN bus" in rest_of_log:
                self.updateConsoleTextbox(f"CAN Sent main")
            elif "Sent CAN message to redundant CAN bus" in rest_of_log:
                self.updateConsoleTextbox(f"CAN Sent redundant")
            elif "Sent 512 bytes payload message" in rest_of_log:
                self.handle_payload_message(rest_of_log)
            elif "Time" in rest_of_log:
                self.handle_time_log(rest_of_log)
            elif "The temperature of the MCU is" in rest_of_log:
                self.handle_mcu_temp_log(rest_of_log)
            elif "Sensor with address" in rest_of_log:
                self.handle_ambient_temp_log(rest_of_log)
            elif "Watchdog reset" in rest_of_log:
                self.handle_watchdog_message(milliseconds)
            elif "MRAM read and write test succeeded" in rest_of_log:
                self.updateMRAMCheckbox(True)
            elif "The ID of the NAND Flash is: 44 104 0 39 169 0 0 0" in rest_of_log:
                self.updateConsoleTextbox(f"NAND ID OK")
            elif "NAND read and write test succeeded" in rest_of_log:
                self.updateNANDCheckbox(True)
            elif "Write address is:" in rest_of_log:
                self.updateConsoleTextbox(f"New Write Address")
            elif "NAND erase test succeeded" in rest_of_log:
                self.updateNANDCheckbox(True)
            elif "Incoming Log from COMMS: CAN1 SAYS:" in rest_of_log:
                self.updateCANMainCheckbox(True)
            elif "Incoming Log from COMMS: CAN2 SAYS:" in rest_of_log:
                self.updateCANRedCheckbox(True)
            elif "CAN Message of Unknown type" in rest_of_log:
                # self.updateCANMainCheckbox(False)
                # self.updateCANRedCheckbox(False)
                self.updateConsoleTextbox(f"CAN Unknown message")
            elif "Tried sending CAN Message while outgoing queue is full!" in rest_of_log:
                self.updateCANMainCheckbox(False)
                self.updateCANRedCheckbox(False)
                self.updateConsoleTextbox(f"CAN Queue Full")
            elif "Resetting CAN LCLs" in rest_of_log:
                self.updateCANMainCheckbox(False)
                self.updateCANRedCheckbox(False)
                self.updateConsoleTextbox(f"CAN LCLs reset")
            else:
                self.updateConsoleTextbox(f"Unhandled: {rest_of_log}")
  

if __name__ == "__main__":
    app = App()
    app.mainloop()