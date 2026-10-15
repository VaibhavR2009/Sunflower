#include <Servo.h>

Servo panServo;
Servo tiltServo;

const int PAN_PIN = 9;
const int TILT_PIN = 10;

int panAngle = 90;
int tiltAngle = 90;

void setup() {
  Serial.begin(115200);

  panServo.attach(PAN_PIN);
  tiltServo.attach(TILT_PIN);

  panServo.write(panAngle);
  tiltServo.write(tiltAngle);
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    int comma = line.indexOf(',');
    if (comma > 0) {
      int newPan = line.substring(0, comma).toInt();
      int newTilt = line.substring(comma + 1).toInt();

      newPan = constrain(newPan, 10, 170);
      newTilt = constrain(newTilt, 35, 145);

      panAngle = newPan;
      tiltAngle = newTilt;

      panServo.write(panAngle);
      tiltServo.write(tiltAngle);
    }
  }
}
