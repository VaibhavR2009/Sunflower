from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ArmAngles:
    pan: float
    tilt: float


class ArmController:
    """Converts face position errors into smooth pan/tilt target angles.

    This class does not move hardware by itself. It produces safe target angles
    that can later be sent to an Arduino over serial.
    """

    def __init__(
        self,
        pan_center: float = 90.0,
        tilt_center: float = 90.0,
        pan_min: float = 10.0,
        pan_max: float = 170.0,
        tilt_min: float = 35.0,
        tilt_max: float = 145.0,
        pan_direction: float = 1.0,
        tilt_direction: float = -1.0,
        gain: float = 0.75,
        smoothing: float = 0.15,
        deadband: float = 0.05,
    ):
        self.pan_center = pan_center
        self.tilt_center = tilt_center
        self.pan_min = pan_min
        self.pan_max = pan_max
        self.tilt_min = tilt_min
        self.tilt_max = tilt_max
        self.pan_direction = pan_direction
        self.tilt_direction = tilt_direction
        self.gain = gain
        self.smoothing = smoothing
        self.deadband = deadband

        self.current = ArmAngles(pan_center, tilt_center)

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

        desired_pan = max(self.pan_min, min(self.pan_max, desired_pan))
        desired_tilt = max(self.tilt_min, min(self.tilt_max, desired_tilt))

        a = self.smoothing
        self.current.pan += a * (desired_pan - self.current.pan)
        self.current.tilt += a * (desired_tilt - self.current.tilt)

        return self.current
