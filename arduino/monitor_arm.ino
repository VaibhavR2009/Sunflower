#include <Servo.h>

Servo panServo;
Servo tiltServo;
Servo liftServo;

const int PAN_PIN = 9;
const int TILT_PIN = 10;
const int LIFT_PIN = 11;

int panAngle = 90;
int tiltAngle = 90;
int liftAngle = 90;

void setup()
{
  Serial.begin(115200);

  panServo.attach(PAN_PIN);
  tiltServo.attach(TILT_PIN);
  liftServo.attach(LIFT_PIN);

  panServo.write(panAngle);
  tiltServo.write(tiltAngle);
  liftServo.write(liftAngle);
}

// Parses the next comma-separated field. Returns -1 when there is no field.
int nextField(const String &line, int from, int &value)
{
  if (from < 0 || from >= (int)line.length())
  {
    return -1;
  }
  int comma = line.indexOf(',', from);
  String token = comma == -1 ? line.substring(from) : line.substring(from, comma);
  token.trim();
  value = token.toInt();
  return comma;
}

void loop()
{
  if (Serial.available())
  {
    String line = Serial.readStringUntil('\n');
    line.trim();

    int pan = 0;
    int tilt = 0;
    int lift = 0;

    int c1 = nextField(line, 0, pan);
    if (c1 > 0)
    {
      int c2 = nextField(line, c1 + 1, tilt);
      if (c2 > 0)
      {
        nextField(line, c2 + 1, lift);
        liftAngle = constrain(lift, 10, 170);
      }

      panAngle = constrain(pan, 10, 170);
      tiltAngle = constrain(tilt, 35, 145);

      panServo.write(panAngle);
      tiltServo.write(tiltAngle);
      liftServo.write(liftAngle);
    }
  }
}
