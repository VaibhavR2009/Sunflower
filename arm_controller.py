from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ArmAngles:
    pan: float
    tilt: float
    lift: float


class ArmController:
    """Converts face position errors into smooth pan/tilt/lift target angles.

    Left/right face movement drives pan exactly as before.

    Up/down face movement is split across two channels:
      * lift - moves the monitor arm up and down, so lowering/raising the
        arm does the bulk of the vertical tracking.
      * tilt - adjusts the angle of the monitor head. As the arm lowers the
        head tilts up, and as it raises the head tilts down, so the screen
        keeps facing the person.

    Person moves DOWN (face low in the frame)  -> lift angle decreases,
                                                  tilt angle increases.
    Person moves UP (face high in the frame)   -> lift angle increases,
                                                  tilt angle decreases.

    This class does not move hardware by itself. It produces safe target angles that can later be sent to an Arduino over serial.

    If a channel moves the wrong way on servo mounting, flip that channel's *_direction parameter between 1.0 and -1.0.
    """

    def __init__(
        self,
        pan_center: float = 90.0,
        tilt_center: float = 90.0,
        lift_center: float = 90.0,
        pan_min: float = 10.0,
        pan_max: float = 170.0,
        tilt_min: float = 35.0,
        tilt_max: float = 145.0,
        lift_min: float = 10.0,
        lift_max: float = 170.0,
        pan_direction: float = 1.0,
        tilt_direction: float = 1.0,
        lift_direction: float = -1.0,
        gain: float = 0.75,
        smoothing: float = 0.15,
        lift_gain: float = 0.75,
        lift_smoothing: float = 0.1,
        deadband: float = 0.05,
    ):
        self.pan_center = pan_center
        self.tilt_center = tilt_center
        self.lift_center = lift_center
        self.pan_min = pan_min
        self.pan_max = pan_max
        self.tilt_min = tilt_min
        self.tilt_max = tilt_max
        self.lift_min = lift_min
        self.lift_max = lift_max
        self.pan_direction = pan_direction
        self.tilt_direction = tilt_direction
        self.lift_direction = lift_direction
        self.gain = gain
        self.smoothing = smoothing
        self.lift_gain = lift_gain
        self.lift_smoothing = lift_smoothing
        self.deadband = deadband

        self.current = ArmAngles(pan_center, tilt_center, lift_center)

    @staticmethod
    def _deadband(value: float, band: float) -> float:
        if abs(value) < band:
            return 0.0
        return value

    def update(self, error_x: float, error_y: float) -> ArmAngles:
        error_x = self._deadband(error_x, self.deadband)
        error_y = self._deadband(error_y, self.deadband)

        desired_pan = self.pan_center + self.pan_direction * error_x * 90.0 * self.gain
        desired_tilt = self.tilt_center + self.tilt_direction * error_y * 60.0 * self.gain
        desired_lift = self.lift_center + self.lift_direction * error_y * 60.0 * self.lift_gain

        desired_pan = max(self.pan_min, min(self.pan_max, desired_pan))
        desired_tilt = max(self.tilt_min, min(self.tilt_max, desired_tilt))
        desired_lift = max(self.lift_min, min(self.lift_max, desired_lift))

        a = self.smoothing
        al = self.lift_smoothing
        self.current.pan += a * (desired_pan - self.current.pan)
        self.current.tilt += a * (desired_tilt - self.current.tilt)
        self.current.lift += al * (desired_lift - self.current.lift)

        return self.current
