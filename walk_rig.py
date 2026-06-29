"""Turn a single side-profile sprite into an articulated walk cycle (cutout rig).

We slice the sprite into a static upper body and two legs, then swing the legs
with phase-offset sines so the character actually steps instead of just bobbing.
Pure procedural — no extra art frames needed. Works because the sprite is a
clean side profile (rotation-only cutout is valid for profile views).
"""

import math

import pygame


class WalkRig:
    def __init__(self, sprite, hip_frac=0.62):
        """sprite: an RGBA Surface facing RIGHT. hip_frac: where the legs begin
        (fraction of height from the top — just below the dress hem)."""
        self.sprite = sprite
        self.w, self.h = sprite.get_size()
        self.hip_y = int(self.h * hip_frac)

        # upper body = everything above the hip line (kept rigid)
        self.upper = sprite.subsurface(
            pygame.Rect(0, 0, self.w, self.hip_y)).copy()

        # legs region = from hip to bottom. Split into front/back halves by x at
        # the hip so each leg can swing independently around the hip joint.
        legs = sprite.subsurface(
            pygame.Rect(0, self.hip_y, self.w, self.h - self.hip_y)).copy()
        self.leg_h = legs.get_height()

        # find the horizontal centre of the leg mass at the hip line to split L/R
        split = self._leg_split_x(legs)
        # back leg = left part, front leg = right part (sprite faces right)
        back = legs.copy()
        back.fill((0, 0, 0, 0), pygame.Rect(split, 0, self.w - split, self.leg_h))
        front = legs.copy()
        front.fill((0, 0, 0, 0), pygame.Rect(0, 0, split, self.leg_h))
        self.back_leg = back
        self.front_leg = front
        # pivot (hip) is at the split x, at the top of the legs strip
        self.pivot_x = split

    def _leg_split_x(self, legs):
        """Column with the least opaque pixels near the top = the gap between legs."""
        w, h = legs.get_size()
        band = min(h, 30)
        best_x, best_count = w // 2, 10 ** 9
        for x in range(int(w * 0.3), int(w * 0.7)):
            count = sum(1 for y in range(band) if legs.get_at((x, y))[3] > 40)
            if count < best_count:
                best_count, best_x = count, x
        return best_x

    def _swing(self, leg, angle_deg):
        """Rotate a leg surface around the hip joint (top of the strip)."""
        # rotate about the hip: translate so pivot is at origin, rotate, re-place
        rotated = pygame.transform.rotate(leg, angle_deg)
        # pygame rotates about centre; compute where the hip point moved to
        ox = self.pivot_x - leg.get_width() / 2
        oy = -leg.get_height() / 2  # hip is at top of the strip
        rad = math.radians(-angle_deg)
        nx = ox * math.cos(rad) - oy * math.sin(rad)
        ny = ox * math.sin(rad) + oy * math.cos(rad)
        # offset so the hip stays anchored at (pivot_x, 0) of the legs region
        off_x = self.pivot_x - (rotated.get_width() / 2 + nx)
        off_y = 0 - (rotated.get_height() / 2 + ny)
        return rotated, off_x, off_y

    def render(self, phase, flip):
        """Compose a walking frame for the given stride phase. Returns a Surface
        the same canvas size as the original sprite, legs swung by `phase`."""
        # leg swing: front and back legs are 180° out of phase
        amp = 18.0
        front_a = amp * math.sin(phase)
        back_a = amp * math.sin(phase + math.pi)

        canvas = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        # draw legs first (behind), then upper body on top
        for leg, ang in ((self.back_leg, back_a), (self.front_leg, front_a)):
            rot, ox, oy = self._swing(leg, ang)
            canvas.blit(rot, (ox, self.hip_y + oy))
        canvas.blit(self.upper, (0, 0))

        if flip:
            canvas = pygame.transform.flip(canvas, True, False)
        return canvas
