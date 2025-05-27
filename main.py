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
    
    return normal# Backrooms Game - First Person Navigation with OBJ Map

import pygame
from pygame.locals import *
import os
import sys

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
PLAYER_RADIUS = 0.3  # Reduced for smaller map scale
PLAYER_HEIGHT = 2.0
MOVEMENT_SPEED = 0.2  # Reduced for smaller map scale
ROTATION_SPEED = 2.0
MAP_BOUNDARY = 20.0  # Adjusted for your map size (-15 to +15)

# Camera/Observer variables
FOVY = 60.0
ZNEAR = 0.1
ZFAR = 1000.0

# Initial camera position (adjust based on your map)
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
collision_faces = []  # Store faces for collision detection

def init_opengl():
    """Initialize OpenGL settings"""
    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Backrooms - First Person")

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
    
    # Set up lighting
    glLightfv(GL_LIGHT0, GL_POSITION, [0, 10, 0, 1])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

def load_map(obj_filename):
    """Load the OBJ map file and extract collision data"""
    global map_model, collision_faces
    try:
        if os.path.exists(obj_filename):
            map_model = OBJ(obj_filename, swapyz=False)
            # Extract collision data from the loaded model
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
    """Extract collision geometry from the loaded OBJ model - optimized for Backrooms structure"""
    global collision_faces
    collision_faces = []
    
    if not map_model:
        return
    
    print("Analyzing map geometry...")
    
    # Process each face from the OBJ model
    for face_data in map_model.faces:
        vertices_indices, normals, texture_coords, material = face_data
        
        # Get actual vertex coordinates
        face_vertices = []
        for vertex_index in vertices_indices:
            if vertex_index <= len(map_model.vertices):
                vertex = map_model.vertices[vertex_index - 1]  # OBJ indices start at 1
                face_vertices.append([vertex[0], vertex[1], vertex[2]])
        
        if len(face_vertices) >= 3:
            # Calculate face normal
            normal = calculate_face_normal(face_vertices)
            
            # Get face bounds
            min_y = min([v[1] for v in face_vertices])
            max_y = max([v[1] for v in face_vertices])
            
            # Classify face type based on normal and position
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
    # Check if it's mostly horizontal (floor/ceiling)
    if abs(normal[1]) > 0.8:  # Strong Y component
        if min_y < 0.5:  # Near ground level
            return 'floor'
        else:
            return 'ceiling'
    
    # Check if it's mostly vertical (wall)
    horizontal_strength = math.sqrt(normal[0]**2 + normal[2]**2)
    if horizontal_strength > 0.3:  # Has horizontal component
        # Check height - if it's tall enough, it's a wall
        height = max_y - min_y
        if height > 1.0:  # Taller than 1 unit
            return 'wall'
        else:
            return 'obstacle'
    
    return 'other'

def check_collision_with_box(new_x, new_z, box_vertices, box_min_y, box_max_y):
    """Check collision between player cylinder and a box-shaped obstacle"""
    player_y = EYE_Y
    player_min_y = player_y - PLAYER_HEIGHT/2
    player_max_y = player_y + PLAYER_HEIGHT/2
    
    # Check Y overlap first
    if player_max_y < box_min_y or player_min_y > box_max_y:
        return False
    
    # Get box bounds in X-Z plane
    box_min_x = min([v[0] for v in box_vertices])
    box_max_x = max([v[0] for v in box_vertices])
    box_min_z = min([v[2] for v in box_vertices])
    box_max_z = max([v[2] for v in box_vertices])
    
    # Check if player cylinder intersects with box in X-Z plane
    # Player is a circle, box is a rectangle
    closest_x = max(box_min_x, min(new_x, box_max_x))
    closest_z = max(box_min_z, min(new_z, box_max_z))
    
    # Distance from player center to closest point on box
    distance = math.sqrt((new_x - closest_x)**2 + (new_z - closest_z)**2)
    
    return distance < PLAYER_RADIUS

def check_collision(new_x, new_z, radius=PLAYER_RADIUS):
    """Improved collision detection for Backrooms geometry"""
    
    # Check collision with each face/obstacle
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
    # Check map boundaries (your map is roughly -15 to +15)
    if abs(new_x) > MAP_BOUNDARY or abs(new_z) > MAP_BOUNDARY:
        return False
    
    # Check collision with walls/obstacles
    if check_collision(new_x, new_z):
        return False
    
    return True

def draw_simple_floor():
    """Draw a simple floor if map doesn't load"""
    glColor3f(0.8, 0.8, 0.6)  # Yellowish color like backrooms
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
    
    # X axis in red
    glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_LINES)
    glVertex3f(-10, 0, 0)
    glVertex3f(10, 0, 0)
    glEnd()
    
    # Y axis in green
    glColor3f(0.0, 1.0, 0.0)
    glBegin(GL_LINES)
    glVertex3f(0, -10, 0)
    glVertex3f(0, 10, 0)
    glEnd()
    
    # Z axis in blue
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_LINES)
    glVertex3f(0, 0, -10)
    glVertex3f(0, 0, 10)
    glEnd()
    
    glLineWidth(1.0)
    glEnable(GL_LIGHTING)

def update_camera():
    """Update camera position and orientation"""
    global CENTER_X, CENTER_Z
    CENTER_X = EYE_X + direction[0]
    CENTER_Z = EYE_Z + direction[2]
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(EYE_X, EYE_Y, EYE_Z, CENTER_X, CENTER_Y, CENTER_Z, UP_X, UP_Y, UP_Z)

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
    
    # Check if the move is valid (no collision)
    if is_valid_move(new_x, new_z):
        EYE_X = new_x
        EYE_Z = new_z
        update_camera()

def move_backward(speed):
    """Move camera backward with collision detection"""
    global EYE_X, EYE_Z
    new_x = EYE_X - direction[0] * speed
    new_z = EYE_Z - direction[2] * speed
    
    # Check if the move is valid (no collision)
    if is_valid_move(new_x, new_z):
        EYE_X = new_x
        EYE_Z = new_z
        update_camera()

def render_scene():
    """Render the complete scene"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Draw axes for debugging (comment out later)
    draw_axes()
    
    # Draw the map or simple floor
    if map_model:
        glPushMatrix()
        # You might need to scale or transform your model here
        # glScalef(10, 10, 10)  # Scale if model is too small
        # glRotatef(-90, 1, 0, 0)  # Rotate if needed
        map_model.render()
        glPopMatrix()
    else:
        draw_simple_floor()

def handle_input():
    """Handle keyboard input"""
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
    pygame.init()
    
    # Initialize OpenGL
    init_opengl()
    
    # Load your map
    map_filename = 'backroom.obj'  # Your Blender exported map
    load_map(map_filename)
    
    # Game loop
    clock = pygame.time.Clock()
    running = True
    
    print("Controls:")
    print("- Arrow Keys or WASD: Move and rotate")
    print("- ESC: Exit")
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Handle continuous input
        handle_input()
        
        # Render
        render_scene()
        
        # Update display
        pygame.display.flip()
        clock.tick(60)  # 60 FPS
    
    # Cleanup
    if map_model:
        map_model.free()
    pygame.quit()

if __name__ == "__main__":
    main()