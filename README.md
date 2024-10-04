# PeakSat Logs App

A python dashboard app that parses and displays the logs created from the PeakSat's OBC board, in a visual friendly way.

<p align="center">
    <img src="https://github.com/PeakSat/PeakSat_Log_App/blob/main/images/Screenshot_APP.jpg" alt="App_example"/>
</p>

---
## Running the App
- Clone the repo and navigate to the repo's directory.
- Open a terminal window and run the following command to install the needed python dependencies:
```bash
  pip install -r ./requirements.txt
```
- After successfully installing the dependencies in the terminal window run:
```bash
  python ./OBC_monitor.py
```
## Quick startup guide
### Connect to serial
- Select the correct serial port your device is connected to from the available ports dropdown menu.
- Press the "Connect serial" button. The logs should start appearing in the "Serial Monitor" textbox.
- Press the "Disconnect serial" button, to stop the serial communication with the device.

``📝NOTE: The device should be connected prior to starting the APP, this is a known bug and will be updated in a future version``
### Save logs
- Toggle the "Save logs" checkbox on the side pannel to enable/disable saving the logs.
- The logfile created will be saved in the "logFiles" folder, and it's name will be the current timestamp.

### Replay/Plot files
- Use the "Available files" droplist to select a file located in the logFiles folder.
- Press the "Replay file" button to replay the logs in the file and examine them through the APP.
- Press the "Plot file" button to parse and plot the available information in the file, the plotted variables include:
    - MCU Temperature.  (Blue line)
    - Temperature sensors 0 and 1. (Yellow and Green lines)
    - CAN bus status.   (Red line)
    - Resets.   (Black dashed vertical line)

<p align="center">
    <img src="https://github.com/PeakSat/PeakSat_Log_App/blob/main/images/Screenshot_plot_example.jpg" alt="Plot_example"/>
</p>

``📝NOTE: After ploting a file, a parsed log file will be created in the parsedLogs folder, delete this file if you wish to plot the same file again``

## Contributing
Feel free to suggest and implement changes and report bugs. Pull requests are welcome. Create issues to discuss further on future improvements/changes and implementations. 
This is still a work in progress so any feedback will be appreciated. 😊

## Authors

- [@giatats](https://github.com/giatats)
