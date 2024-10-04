import os
import sys
import re

output_logs_folder  = "parsedLogs"
output_filename     = "out.txt"
timekeeper          = 0
mcu_temp            = 0
amb_temp_a          = 0
amb_temp_b          = 0

def doNothing():
    return

def writeToOutput(newLine):
    global timekeeper
    output_f = os.path.join(output_logs_folder, output_filename)
    with open(output_f, "a") as file:
        file.write(f'{timekeeper}')
        file.write('\t')
        file.write(newLine)
        file.write('\n')
    file.close()

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

def handleReset(milliseconds):
    global mcu_temp, amb_temp_a, amb_temp_b, wdtimer, obtimer
    resetMessage = f"***Reset detected*** Runtime: {milliseconds} ms MCU Temp: {mcu_temp} Temp S0: {amb_temp_a} Temp S1: {amb_temp_b}*** *** ***"
    writeToOutput(resetMessage)
    
def updateRuntime(milliseconds):
    global timekeeper
    if( (milliseconds+10) < timekeeper):
        handleReset(timekeeper)
    timekeeper = milliseconds

def parse_log_entry(log_entry):
        # Regular expression to extract milliseconds value and the rest of the log
        log_entry = log_entry[1:].strip()
        pattern = r'^(\d+)\s+\[([^\]]+)\]\s+OBC\s+(.*)$'
        match = re.match(pattern, log_entry)
        
        if match:
            milliseconds = int(match.group(1))
            rest_of_log = match.group(3)
            updateRuntime(milliseconds)
            
            # Check the specific log content for categorization
            if "New TM" in rest_of_log:
                doNothing()
            elif "Sent CAN message to main CAN bus" in rest_of_log:
                doNothing()
            elif "Sent CAN message to redundant CAN bus" in rest_of_log:
                doNothing()
            elif "Sent 512 bytes payload message" in rest_of_log:
                doNothing()
            elif "Time" in rest_of_log:
               doNothing()
            elif "The temperature of the MCU is" in rest_of_log:
                global mcu_temp
                match = re.search(r"[-+]?\d*\.\d+|\d+", rest_of_log)
                if match:
                    mcu_temp = match.group()
                else:
                    mcu_temp = "??"
                mcu_temp = mcu_temp
                writeToOutput("MCU temp: "+str(mcu_temp))
            elif "Sensor with address" in rest_of_log:
                global amb_temp_a, amb_temp_b
                match = re.search(r"address\s+(\d+)\s+.*temperature\s*=\s*([-+]?\d*\.\d+|\d+)", rest_of_log)
            
                if match:
                    address = int(match.group(1))      # Extract the address (integer)
                    temperature = match.group(2)
                    if address:
                        amb_temp_a = temperature
                        writeToOutput("AMB0 temp: "+str(amb_temp_a))
                    else:
                        amb_temp_b = temperature
                        writeToOutput("AMB1 temp: "+str(amb_temp_b))
            elif "Watchdog reset" in rest_of_log:
                writeToOutput("Watchdog Reset")
            elif "MRAM read and write test succeeded" in rest_of_log:
                doNothing()
            elif "The ID of the NAND Flash is: 44 104 0 39 169 0 0 0" in rest_of_log:
                doNothing()
            elif "NAND read and write test succeeded" in rest_of_log:
                doNothing()
            elif "Write address is:" in rest_of_log:
                doNothing()
            elif "NAND erase test succeeded" in rest_of_log:
                doNothing()
            elif "Runtime init" in rest_of_log:
                doNothing()
            elif "The status of the 1st LUN (die)" in rest_of_log:
                doNothing()
            elif "Incoming Log from COMMS: CAN1 SAYS:" in rest_of_log:
                writeToOutput("CAN 1 OK")
            elif "Incoming Log from COMMS: CAN2 SAYS:" in rest_of_log:
                writeToOutput("CAN 2 OK")
            elif "CAN Message of Unknown type" in rest_of_log:
                doNothing()
            elif "Tried sending CAN Message while outgoing queue is full!" in rest_of_log:
                writeToOutput("CAN ERROR Q")
            elif "Resetting CAN LCLs" in rest_of_log:
                writeToOutput("CAN ERROR L")
            else:
                print(f"Unhandled log: {rest_of_log}")

def parseFile(filename):
    print("File: ",filename)
    global output_filename
    output_filename = 'out_'+str(filename)
    print("Output File: ", output_filename)

    current_dir = os.path.dirname(__file__)
    logs_folder = os.path.join(current_dir, "logFiles")
    filepath = os.path.join(logs_folder, filename)

    reader = read_file_line_by_line(filepath)
    new_log = reader()
    while new_log is not None:
        parse_log_entry(new_log)
        new_log = reader()
    print("Finished parsing")


if __name__ == '__main__':
    if(len(sys.argv) < 2):
        print("Please provide one file present in the logFiles directory, or type \"all\" to parse all available files in logFiles directory.")
        exit(1)

    if(sys.argv[1]=="all"):
        print("Parsing all files in logFiles directory")
        current_dir = os.path.dirname(__file__)
        logs_folder = os.path.join(current_dir, "logFiles")
        files_in_folder = [f for f in os.listdir(logs_folder) if os.path.isfile(os.path.join(logs_folder, f))]
        for f in files_in_folder:
            parseFile(f)
    else:
        current_dir = os.path.dirname(__file__)
        logs_folder = os.path.join(current_dir, "logFiles")
        file = sys.argv[1]
        print("Parsing: ", file)
        parseFile(file)

    
    


