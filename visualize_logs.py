import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Function to parse the log file
def parse_log_file(filename):
    mcu_temps = []
    amb1_temps = []
    amb0_temps = []
    reset_points = []
    can_status = []

    offset = 0  # Offset to handle rollback after resets
    last_millisecond = 0

    with open(filename, 'r') as file:
        for line in file:
            parts = line.strip().split('\t')

            if len(parts) < 2:
                continue  # Skip lines that don't follow the format

            milliseconds = int(parts[0])
            message = parts[1]

            # If rollback (milliseconds are less than the last known millisecond), apply offset
            if milliseconds < last_millisecond:
                offset += last_millisecond

            adjusted_milliseconds = milliseconds + offset
            last_millisecond = milliseconds

            if message.startswith("MCU temp:"):
                mcu_temp = float(message.split(': ')[1])
                mcu_temps.append((adjusted_milliseconds, mcu_temp))
            elif message.startswith("AMB1 temp:"):
                amb1_temp = float(message.split(': ')[1])
                amb1_temps.append((adjusted_milliseconds, amb1_temp))
            elif message.startswith("AMB0 temp:"):
                amb0_temp = float(message.split(': ')[1])
                amb0_temps.append((adjusted_milliseconds, amb0_temp))
            elif "***Reset detected***" in message:
                reset_points.append(adjusted_milliseconds)
            elif message == "CAN 1 OK":
                can_status.append((adjusted_milliseconds, 10))
            elif message == "CAN 2 OK":
                can_status.append((adjusted_milliseconds, 10))
            elif message == "CAN ERROR L":
                can_status.append((adjusted_milliseconds, 0))
            elif message == "CAN ERROR Q":
                can_status.append((adjusted_milliseconds, 0))

    return mcu_temps, amb1_temps, amb0_temps, reset_points, can_status

# Function to plot the data
def plot_data(mcu_temps, amb1_temps, amb0_temps, reset_points, can_status, title):
    # Extract data for plotting
    mcu_x, mcu_y = zip(*mcu_temps)
    amb1_x, amb1_y = zip(*amb1_temps)
    amb0_x, amb0_y = zip(*amb0_temps)
    can_x, can_y = zip(*can_status)

    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.plot(mcu_x, mcu_y, label='MCU Temp', marker='o', color='blue')
    plt.plot(amb1_x, amb1_y, label='AMB1 Temp', marker='o', color='green')
    plt.plot(amb0_x, amb0_y, label='AMB0 Temp', marker='o', color='orange')
    plt.ylim(-30, 75)  # Adjust the y-axis limits as needed

    # Handle reset points and highlight clusters
    cluster_threshold = 500  # ms - Define what is considered "close"
    last_reset = None
    cluster_start = None

    for i, reset in enumerate(reset_points):
        if last_reset is not None and reset - last_reset < cluster_threshold:
            if cluster_start is None:
                cluster_start = last_reset  # Start of cluster
            # Continue the cluster by highlighting the area
            plt.axvspan(cluster_start, reset, color='gray', alpha=0.3)
        else:
            # End of a cluster, draw a thicker, shorter line if not clustered
            if cluster_start is not None:
                # Annotate the cluster with a label
                plt.text((cluster_start + last_reset) / 2, -5, 'Reset Cluster', color='red', fontsize=10)
            cluster_start = None
            # Draw reset point as a short, thicker line
            plt.axvline(x=reset, color='black', linestyle='--', linewidth=2, ymin=0.1, ymax=0.9)
        
        last_reset = reset

    # Plot CAN status as a step plot
    can_x_step = np.array(can_x)
    can_y_step = np.array(can_y)
    plt.step(can_x_step, can_y_step, where='post', label='CAN Status', color='red')

    # Add labels and title
    plt.xlabel('Milliseconds')
    plt.ylabel('Temperature / Status')
    plt.title(f'{title}')
    plt.legend()

    # Show the plot
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Main script
if __name__ == '__main__':

    if(len(sys.argv) < 2):
        print("Please provide one file present in the parsedLogs folder as input, or type all to plot all files available.")
        exit(1)
    
    if(sys.argv[1] == "all"):
        folder_path = 'parsedLogs'  # The folder containing log files
        # Get a list of all files in the "parsed logs" directory
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        # Process each file
        for file in files:
            file_path = os.path.join(folder_path, file)
            print(f"Ploting file: {file_path}")

            # Parse and plot the data for the current file
            mcu_temps, amb1_temps, amb0_temps, reset_points, can_status = parse_log_file(file_path)
            plot_data(mcu_temps, amb1_temps, amb0_temps, reset_points, can_status, title=file)

            # Wait for the user to press Enter before continuing to the next file
            input("Press Enter to continue to the next file...")
    else:
        folder_path = 'parsedLogs'  # The folder containing log files
        file = sys.argv[1]
        file_path = os.path.join(folder_path, file)
        print(f"Ploting file: {file_path}")
        mcu_temps, amb1_temps, amb0_temps, reset_points, can_status = parse_log_file(file_path)
        plot_data(mcu_temps, amb1_temps, amb0_temps, reset_points, can_status, title=file)
        print("Finished")


