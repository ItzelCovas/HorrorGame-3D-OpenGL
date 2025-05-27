def calculate_face_normal(vertices):
    """Calculate the normal vector of a face"""
    if len(vertices) < 3:
        return [0, 1, 0]
    
    # Use first three vertices to calculate normal
    v1 = vertices[0]
    v2 = vertices[1]
    v3 = vertices[2]
    
    # Calculate two edge vectors
    edge1 = [v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]]
    edge2 = [v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]]
    
    # Cross product to get normal
    normal = [
        edge1[1] * edge2[2] - edge1[2] * edge2[1],
        edge1[2] * edge2[0] - edge1[0] * edge2[2],
        edge1[0] * edge2[1] - edge1[1] * edge2[0]
    ]
    
    # Normalize
    length = math.sqrt(normal[0]**2 + normal[1]**2 + normal[2]**2)
    if length > 0:
        normal = [normal[0]/length, normal[1]/length, normal[2]/length]
    
    return normal

# Backrooms Game - First Person Navigation with OBJ Map and Monster AI

import pygame
from pygame.locals import *
import os
import sys
import random
import time

# OpenGL libraries
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import math

# Import the OBJ loader
from objloader import OBJ

# Game constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
PLAYER_RADIUS = 0.3
PLAYER_HEIGHT = 2.0
MOVEMENT_SPEED = 0.2
ROTATION_SPEED = 2.0
MAP_BOUNDARY = 20.0

# Monster constants
MONSTER_RADIUS = 0.4
MONSTER_HEIGHT = 2.5
MONSTER_SPEED = 0.1  # Slightly slower than player
MONSTER_DETECTION_RANGE = 8.0  # Distance at which monster detects player
MONSTER_LOSE_RANGE = 15.0  # Distance at which monster loses player
MONSTER_ATTACK_RANGE = 1.5  # Distance at which monster catches player

# Camera/Observer variables
FOVY = 60.0
ZNEAR = 0.1
ZFAR = 1000.0

# Initial camera position
EYE_X = 0.0
EYE_Y = PLAYER_HEIGHT
EYE_Z = 0.0
CENTER_X = 1.0
CENTER_Y = PLAYER_HEIGHT
CENTER_Z = 0.0
UP_X = 0
UP_Y = 1
UP_Z = 0

# Direction vector for camera
direction = [1.0, 0.0, 0.0]
theta = 0.0

# Game objects
map_model = None
collision_faces = []

# Monster AI states
MONSTER_IDLE = 0
MONSTER_PATROLLING = 1
MONSTER_CHASING = 2
MONSTER_SEARCHING = 3

class Monster:
    def __init__(self, x=5.0, z=5.0):
        self.x = x
        self.y = PLAYER_HEIGHT
        self.z = z
        self.state = MONSTER_IDLE
        self.speed = MONSTER_SPEED
        self.direction = [1.0, 0.0, 0.0]  # Direction monster is facing
        self.target_x = x
        self.target_z = z
        self.last_seen_player_x = 0.0
        self.last_seen_player_z = 0.0
        self.search_timer = 0.0
        self.patrol_points = [(5, 5), (-5, 5), (-5, -5), (5, -5)]  # Square patrol
        self.current_patrol_target = 0
        self.idle_timer = 0.0
        self.last_footstep_time = 0.0
        
    def get_distance_to_player(self):
        """Calculate distance to player"""
        dx = self.x - EYE_X
        dz = self.z - EYE_Z
        return math.sqrt(dx*dx + dz*dz)
    
    def can_see_player(self):
        """Simple line-of-sight check to player"""
        distance = self.get_distance_to_player()
        
        # Too far to see
        if distance > MONSTER_DETECTION_RANGE:
            return False
            
        # Check if there's a wall between monster and player
        steps = int(distance * 5)  # Check every 0.2 units
        if steps == 0:
            return True
            
        dx = (EYE_X - self.x) / steps
        dz = (EYE_Z - self.z) / steps
        
        for i in range(1, steps):
            check_x = self.x + dx * i
            check_z = self.z + dz * i
            if check_collision(check_x, check_z, 0.1):  # Small radius for line check
                return False
                
        return True
    
    def move_towards_target(self, target_x, target_z, dt):
        """Move towards a target position with collision detection"""
        dx = target_x - self.x
        dz = target_z - self.z
        distance = math.sqrt(dx*dx + dz*dz)
        
        if distance > 0.1:  # Not at target yet
            # Normalize direction
            dx /= distance
            dz /= distance
            
            # Calculate new position
            move_distance = self.speed * dt * 60  # 60 fps normalization
            new_x = self.x + dx * move_distance
            new_z = self.z + dz * move_distance
            
            # Check collision before moving
            if not check_collision(new_x, new_z, MONSTER_RADIUS):
                self.x = new_x
                self.z = new_z
                self.direction = [dx, 0.0, dz]
                return True
            else:
                # Try to navigate around obstacle
                # Try perpendicular directions
                perp_dirs = [[-dz, 0, dx], [dz, 0, -dx]]  # Perpendicular vectors
                for perp_dir in perp_dirs:
                    test_x = self.x + perp_dir[0] * move_distance
                    test_z = self.z + perp_dir[2] * move_distance
                    if not check_collision(test_x, test_z, MONSTER_RADIUS):
                        self.x = test_x
                        self.z = test_z
                        self.direction = perp_dir
                        return True
                return False
        return True  # Already at target

    def update_ai(self, dt):
        """Update monster AI based on current state"""
        distance_to_player = self.get_distance_to_player()
        
        # Check if player is caught
        if distance_to_player < MONSTER_ATTACK_RANGE:
            return "GAME_OVER"
        
        # State transitions
        if self.state == MONSTER_IDLE:
            self.idle_timer += dt
            if self.idle_timer > 2.0:  # Idle for 2 seconds
                self.state = MONSTER_PATROLLING
                self.idle_timer = 0.0
                
        elif self.state == MONSTER_PATROLLING:
            if self.can_see_player():
                self.state = MONSTER_CHASING
                self.last_seen_player_x = EYE_X
                self.last_seen_player_z = EYE_Z
            else:
                # Continue patrol
                target = self.patrol_points[self.current_patrol_target]
                if self.move_towards_target(target[0], target[1], dt):
                    # Check if reached patrol point
                    dx = target[0] - self.x
                    dz = target[1] - self.z
                    if math.sqrt(dx*dx + dz*dz) < 0.5:
                        self.current_patrol_target = (self.current_patrol_target + 1) % len(self.patrol_points)
                        
        elif self.state == MONSTER_CHASING:
            if self.can_see_player():
                # Update last seen position
                self.last_seen_player_x = EYE_X
                self.last_seen_player_z = EYE_Z
                # Chase player directly
                self.move_towards_target(EYE_X, EYE_Z, dt)
            elif distance_to_player > MONSTER_LOSE_RANGE:
                # Lost player, start searching
                self.state = MONSTER_SEARCHING
                self.search_timer = 0.0
            else:
                # Move to last seen position
                self.move_towards_target(self.last_seen_player_x, self.last_seen_player_z, dt)
                
        elif self.state == MONSTER_SEARCHING:
            self.search_timer += dt
            if self.search_timer > 5.0:  # Search for 5 seconds
                self.state = MONSTER_PATROLLING
                self.search_timer = 0.0
            else:
                if self.can_see_player():
                    self.state = MONSTER_CHASING
                    self.last_seen_player_x = EYE_X
                    self.last_seen_player_z = EYE_Z
                else:
                    # Random search movement
                    if self.search_timer % 1.0 < dt:  # Change direction every second
                        angle = random.uniform(0, 2 * math.pi)
                        self.target_x = self.last_seen_player_x + random.uniform(-3, 3)
                        self.target_z = self.last_seen_player_z + random.uniform(-3, 3)
                    self.move_towards_target(self.target_x, self.target_z, dt)
        
        return "CONTINUE"
    
    def play_footstep_sound(self):
        """Play monster footstep sound (placeholder)"""
        current_time = time.time()
        if current_time - self.last_footstep_time > 0.5:  # Footstep every 0.5 seconds
            # You can add actual sound playing here
            # pygame.mixer.Sound("monster_footstep.wav").play()
            self.last_footstep_time = current_time
    
    def render(self):
        """Render the monster as a simple dark figure"""
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        # Disable lighting for monster to make it darker/more ominous
        glDisable(GL_LIGHTING)
        glColor3f(0.1, 0.1, 0.1)  # Very dark gray/black
        
        # Draw monster as a tall rectangular prism
        glBegin(GL_QUADS)
        
        # Front face
        glVertex3f(-0.2, -1.0, 0.2)
        glVertex3f(0.2, -1.0, 0.2)
        glVertex3f(0.2, 1.5, 0.2)
        glVertex3f(-0.2, 1.5, 0.2)
        
        # Back face
        glVertex3f(-0.2, -1.0, -0.2)
        glVertex3f(-0.2, 1.5, -0.2)
        glVertex3f(0.2, 1.5, -0.2)
        glVertex3f(0.2, -1.0, -0.2)
        
        # Left face
        glVertex3f(-0.2, -1.0, -0.2)
        glVertex3f(-0.2, -1.0, 0.2)
        glVertex3f(-0.2, 1.5, 0.2)
        glVertex3f(-0.2, 1.5, -0.2)
        
        # Right face
        glVertex3f(0.2, -1.0, -0.2)
        glVertex3f(0.2, 1.5, -0.2)
        glVertex3f(0.2, 1.5, 0.2)
        glVertex3f(0.2, -1.0, 0.2)
        
        # Top face
        glVertex3f(-0.2, 1.5, -0.2)
        glVertex3f(-0.2, 1.5, 0.2)
        glVertex3f(0.2, 1.5, 0.2)
        glVertex3f(0.2, 1.5, -0.2)
        
        glEnd()
        
        # Add glowing red eyes
        glColor3f(1.0, 0.0, 0.0)  # Red
        glPointSize(5.0)
        glBegin(GL_POINTS)
        glVertex3f(-0.1, 0.8, 0.21)  # Left eye
        glVertex3f(0.1, 0.8, 0.21)   # Right eye
        glEnd()
        glPointSize(1.0)
        
        glEnable(GL_LIGHTING)
        glPopMatrix()

# Initialize monster
monster = Monster(x=10.0, z=10.0)
game_state = "PLAYING"  # PLAYING, GAME_OVER
game_over_timer = 0.0

def init_opengl():
    """Initialize OpenGL settings"""
    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Backrooms - Monster Hunt")

    # Set up projection matrix
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, SCREEN_WIDTH/SCREEN_HEIGHT, ZNEAR, ZFAR)

    # Set up model view matrix
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(EYE_X, EYE_Y, EYE_Z, CENTER_X, CENTER_Y, CENTER_Z, UP_X, UP_Y, UP_Z)
    
    # OpenGL settings for better rendering
    glClearColor(0.1, 0.1, 0.1, 1.0)  # Dark background
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    
    # Set up lighting - dimmer for horror atmosphere
    glLightfv(GL_LIGHT0, GL_POSITION, [EYE_X, EYE_Y + 5, EYE_Z, 1])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.5, 0.5, 0.5, 1.0])
    
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

def load_map(obj_filename):
    """Load the OBJ map file and extract collision data"""
    global map_model, collision_faces
    try:
        if os.path.exists(obj_filename):
            map_model = OBJ(obj_filename, swapyz=False)
            extract_collision_data()
            print(f"Map loaded successfully: {obj_filename}")
            print(f"Collision faces extracted: {len(collision_faces)}")
        else:
            print(f"Map file not found: {obj_filename}")
            print("Creating a simple floor plane instead...")
            map_model = None
    except Exception as e:
        print(f"Error loading map: {e}")
        map_model = None

def extract_collision_data():
    """Extract collision geometry from the loaded OBJ model"""
    global collision_faces
    collision_faces = []
    
    if not map_model:
        return
    
    print("Analyzing map geometry...")
    
    for face_data in map_model.faces:
        vertices_indices, normals, texture_coords, material = face_data
        
        face_vertices = []
        for vertex_index in vertices_indices:
            if vertex_index <= len(map_model.vertices):
                vertex = map_model.vertices[vertex_index - 1]
                face_vertices.append([vertex[0], vertex[1], vertex[2]])
        
        if len(face_vertices) >= 3:
            normal = calculate_face_normal(face_vertices)
            min_y = min([v[1] for v in face_vertices])
            max_y = max([v[1] for v in face_vertices])
            face_type = classify_face(normal, face_vertices, min_y, max_y)
            
            if face_type in ['wall', 'obstacle']:
                collision_faces.append({
                    'vertices': face_vertices,
                    'normal': normal,
                    'type': face_type,
                    'min_y': min_y,
                    'max_y': max_y
                })
    
    print(f"Found {len(collision_faces)} collision faces")

def classify_face(normal, vertices, min_y, max_y):
    """Classify a face as floor, ceiling, wall, or obstacle"""
    if abs(normal[1]) > 0.8:
        if min_y < 0.5:
            return 'floor'
        else:
            return 'ceiling'
    
    horizontal_strength = math.sqrt(normal[0]**2 + normal[2]**2)
    if horizontal_strength > 0.3:
        height = max_y - min_y
        if height > 1.0:
            return 'wall'
        else:
            return 'obstacle'
    
    return 'other'

def check_collision_with_box(new_x, new_z, box_vertices, box_min_y, box_max_y):
    """Check collision between player cylinder and a box-shaped obstacle"""
    player_y = EYE_Y
    player_min_y = player_y - PLAYER_HEIGHT/2
    player_max_y = player_y + PLAYER_HEIGHT/2
    
    if player_max_y < box_min_y or player_min_y > box_max_y:
        return False
    
    box_min_x = min([v[0] for v in box_vertices])
    box_max_x = max([v[0] for v in box_vertices])
    box_min_z = min([v[2] for v in box_vertices])
    box_max_z = max([v[2] for v in box_vertices])
    
    closest_x = max(box_min_x, min(new_x, box_max_x))
    closest_z = max(box_min_z, min(new_z, box_max_z))
    
    distance = math.sqrt((new_x - closest_x)**2 + (new_z - closest_z)**2)
    
    return distance < PLAYER_RADIUS

def check_collision(new_x, new_z, radius=PLAYER_RADIUS):
    """Improved collision detection for Backrooms geometry"""
    for face in collision_faces:
        vertices = face['vertices']
        face_type = face['type']
        min_y = face['min_y']
        max_y = face['max_y']
        
        if face_type in ['wall', 'obstacle']:
            if check_collision_with_box(new_x, new_z, vertices, min_y, max_y):
                return True
    
    return False

def is_valid_move(new_x, new_z):
    """Check if a move to the new position is valid"""
    if abs(new_x) > MAP_BOUNDARY or abs(new_z) > MAP_BOUNDARY:
        return False
    
    if check_collision(new_x, new_z):
        return False
    
    return True

def draw_simple_floor():
    """Draw a simple floor if map doesn't load"""
    glColor3f(0.8, 0.8, 0.6)
    glBegin(GL_QUADS)
    size = 50
    for x in range(-size, size, 5):
        for z in range(-size, size, 5):
            glVertex3f(x, 0, z)
            glVertex3f(x+5, 0, z)
            glVertex3f(x+5, 0, z+5)
            glVertex3f(x, 0, z+5)
    glEnd()

def draw_axes():
    """Draw coordinate axes for debugging"""
    glDisable(GL_LIGHTING)
    glLineWidth(3.0)
    
    glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_LINES)
    glVertex3f(-10, 0, 0)
    glVertex3f(10, 0, 0)
    glEnd()
    
    glColor3f(0.0, 1.0, 0.0)
    glBegin(GL_LINES)
    glVertex3f(0, -10, 0)
    glVertex3f(0, 10, 0)
    glEnd()
    
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_LINES)
    glVertex3f(0, 0, -10)
    glVertex3f(0, 0, 10)
    glEnd()
    
    glLineWidth(1.0)
    glEnable(GL_LIGHTING)

def draw_hud():
    """Draw HUD information"""
    # Set up 2D rendering
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    # Monster distance indicator (simple color bar)
    distance = monster.get_distance_to_player()
    if distance < MONSTER_DETECTION_RANGE:
        # Red warning when monster is close
        intensity = 1.0 - (distance / MONSTER_DETECTION_RANGE)
        glColor3f(intensity, 0.0, 0.0)
        
        # Draw warning rectangle
        glBegin(GL_QUADS)
        glVertex2f(10, SCREEN_HEIGHT - 30)
        glVertex2f(200, SCREEN_HEIGHT - 30)
        glVertex2f(200, SCREEN_HEIGHT - 10)
        glVertex2f(10, SCREEN_HEIGHT - 10)
        glEnd()
    
    # Game over text
    if game_state == "GAME_OVER":
        glColor3f(1.0, 0.0, 0.0)
        # Note: You'd need to implement text rendering here
        # For now, just a red overlay
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(SCREEN_WIDTH, 0)
        glVertex2f(SCREEN_WIDTH, SCREEN_HEIGHT)
        glVertex2f(0, SCREEN_HEIGHT)
        glEnd()
    
    # Restore 3D rendering
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def update_camera():
    """Update camera position and orientation"""
    global CENTER_X, CENTER_Z
    CENTER_X = EYE_X + direction[0]
    CENTER_Z = EYE_Z + direction[2]
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(EYE_X, EYE_Y, EYE_Z, CENTER_X, CENTER_Y, CENTER_Z, UP_X, UP_Y, UP_Z)
    
    # Update light position to follow player
    glLightfv(GL_LIGHT0, GL_POSITION, [EYE_X, EYE_Y + 2, EYE_Z, 1])

def rotate_camera(angle):
    """Rotate camera by given angle"""
    global direction, theta
    theta += angle
    rads = math.radians(theta)
    direction[0] = math.cos(rads)
    direction[2] = math.sin(rads)
    update_camera()

def move_forward(speed):
    """Move camera forward with collision detection"""
    global EYE_X, EYE_Z
    new_x = EYE_X + direction[0] * speed
    new_z = EYE_Z + direction[2] * speed
    
    if is_valid_move(new_x, new_z):
        EYE_X = new_x
        EYE_Z = new_z
        update_camera()

def move_backward(speed):
    """Move camera backward with collision detection"""
    global EYE_X, EYE_Z
    new_x = EYE_X - direction[0] * speed
    new_z = EYE_Z - direction[2] * speed
    
    if is_valid_move(new_x, new_z):
        EYE_X = new_x
        EYE_Z = new_z
        update_camera()

def render_scene():
    """Render the complete scene"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Draw the map or simple floor
    if map_model:
        glPushMatrix()
        map_model.render()
        glPopMatrix()
    else:
        draw_simple_floor()
    
    # Draw the monster
    monster.render()
    
    # Draw HUD
    draw_hud()

def handle_input():
    """Handle keyboard input"""
    global game_state
    
    if game_state == "GAME_OVER":
        return
        
    keys = pygame.key.get_pressed()
    
    # Movement
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        move_forward(MOVEMENT_SPEED)
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        move_backward(MOVEMENT_SPEED)
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        rotate_camera(-ROTATION_SPEED)
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        rotate_camera(ROTATION_SPEED)

def main():
    """Main game loop"""
    global game_state, game_over_timer
    
    pygame.init()
    
    # Initialize OpenGL
    init_opengl()
    
    # Load your map
    map_filename = 'backroom.obj'
    load_map(map_filename)
    
    # Game loop
    clock = pygame.time.Clock()
    running = True
    
    print("Controls:")
    print("- Arrow Keys or WASD: Move and rotate")
    print("- ESC: Exit")
    print("- Avoid the monster! It will hunt you down!")
    
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and game_state == "GAME_OVER":
                    # Restart game
                    game_state = "PLAYING"
                    game_over_timer = 0.0
                    # Reset player position
                    EYE_X = 0.0
                    EYE_Z = 0.0
                    # Reset monster
                    monster.__init__(x=10.0, z=10.0)
        
        if game_state == "PLAYING":
            # Handle continuous input
            handle_input()
            
            # Update monster AI
            result = monster.update_ai(dt)
            if result == "GAME_OVER":
                game_state = "GAME_OVER"
                game_over_timer = 0.0
                print("GAME OVER! The monster caught you!")
                print("Press R to restart or ESC to exit")
        
        elif game_state == "GAME_OVER":
            game_over_timer += dt
        
        # Render
        render_scene()
        
        # Update display
        pygame.display.flip()
    
    # Cleanup
    if map_model:
        map_model.free()
    pygame.quit()

if __name__ == "__main__":
    main()