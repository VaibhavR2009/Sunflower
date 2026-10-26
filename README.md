# Sunflower Monitor Arm

This project uses a camera to detect the face of a person and move a monitor arm so the screen follows them. This script is currently a work in progress, so you may need to adjust the direction and limits of the servos.

## `monitor_arm.py`

This is the main script that:

 - Opens the desired camera.
 - Uses the MediaPipe face landmarker model to detect a single face.
 - Calculates the distance of the face from the centre of the camera image.
 - Sends the horizontal and vertical error to the ArmController class.
 - Displays the camera feed with the detected face and the current pan, tilt and lift angles.
 - Optionally sends the angles to an Arduino via serial.


Press `q` in the camera window to stop the program.

Example:

```powershell
python monitor_arm.py --camera 0 --port COM5
```

The serial port is optional. If you don't include the --port argument the script will still display the tracking window but won't send the movement commands to the Arduino.

Some useful arguments:

- `--camera`: Which camera to use (default: `0`)
- `--port`: Which port the Arduino is on (e.g. `COM5`)
- `--baud`: How fast the serial is (default: `115200`)

This script expects the file `face_landmarker.task` to be in the same directory. If you don't have the model file run `download_model.ps1`.

## `arm_controller.py`

This file contains the ArmController class. This doesn't interact with the servos directly. It takes the error from the face and calculates the desired angles for each of the 3 channels.

- `pan`: Moves the monitor left and right.
- `tilt`: Changes the angle of the monitor head.
- `lift`: Moves the arm up and down.

This adds a deadband so if there isn't much movement in the face the arm won't move all the time. It also adds smoothing so there aren't any large jumps in the angles. All the channels will stay within their min and max angles.

The `pan_direction`, `tilt_direction`, and `lift_direction` can be changed if the servo is mounted the other way round. By default these are set to match the current hardware setup but you may need to change them when testing.


## Dependencies

Install the required Python packages with:

```powershell
pip install -r requirements.txt
```

You will also need a working camera and if using the hardware mode an Arduino connected to the expected serial port.

## Encountered Problems

 - The camera started running before MediaPipe began running and became idle. I fixed it to ensure that Mediapipe would start up first, and then camera would start
 - The deadband was too small, so I increased, reducing the problem of changing the angle when the user barely moves