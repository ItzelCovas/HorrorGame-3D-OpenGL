import math

class Camera:
    def __init__(self):
        self.pos = [0.0, 1.0, 0.0]  # Altura de la cámara
        self.pitch = 0.0
        self.yaw = 90.0
        self.speed = 0.1
        self.sensitivity = 0.1

    def get_direction(self):
        x = math.cos(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        y = math.sin(math.radians(self.pitch))
        z = math.sin(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        return [x, y, z]

    def move(self, keys):
        direction = self.get_direction()
        right = [direction[2], 0, -direction[0]]  # cruz con up vector (0, 1, 0)
        if keys["w"]:
            self.pos = [self.pos[i] + direction[i] * self.speed for i in range(3)]
        if keys["s"]:
            self.pos = [self.pos[i] - direction[i] * self.speed for i in range(3)]
        if keys["a"]:
            self.pos = [self.pos[i] - right[i] * self.speed for i in range(3)]
        if keys["d"]:
            self.pos = [self.pos[i] + right[i] * self.speed for i in range(3)]

    def look(self, dx, dy):
        self.yaw += dx * self.sensitivity
        self.pitch -= dy * self.sensitivity
        self.pitch = max(-89, min(89, self.pitch))
