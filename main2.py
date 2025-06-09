# Backrooms Game - First Person Navigation with Monster AI, Collectibles, and Win Condition
# main.py
import pygame
from pygame.locals import *
import os
import sys
import time

# OpenGL libraries
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import math

# Import custom modules
from objloader import OBJ
from monster import Monster
from game_over import GameOverScreen
from collectible import CollectibleManager
from win_screen import WinScreen

# Game constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
PLAYER_RADIUS = 0.3
PLAYER_HEIGHT = 1.0
MOVEMENT_SPEED = 0.3
ROTATION_SPEED = 3.5
MAP_BOUNDARY = 10.0 

# Camera/Observer variables
FOVY = 60.0
ZNEAR = 0.1
ZFAR = 1000.0

# Initial camera position
EYE_X = 0.0
EYE_Y = PLAYER_HEIGHT
EYE_Z = 0.0
CENTER_X = 1.5
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
monster = None
game_over_screen = None
win_screen = None
collectible_manager = None
game_state = "playing"  # "playing", "game_over", or "won"

def calculate_face_normal(vertices):
    """Calculate the normal vector of a face"""
    if len(vertices) < 3:
        return [0, 1, 0]
    
    v1 = vertices[0]
    v2 = vertices[1]
    v3 = vertices[2]
    
    edge1 = [v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]]
    edge2 = [v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]]
    
    normal = [
        edge1[1] * edge2[2] - edge1[2] * edge2[1],
        edge1[2] * edge2[0] - edge1[0] * edge2[2],
        edge1[0] * edge2[1] - edge1[1] * edge2[0]
    ]
    
    length = math.sqrt(normal[0]**2 + normal[1]**2 + normal[2]**2)
    if length > 0:
        normal = [normal[0]/length, normal[1]/length, normal[2]/length]
    
    return normal

def init_opengl():
    #configuración de OpenGL
    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Backrooms 3D - collect and escape")

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, SCREEN_WIDTH/SCREEN_HEIGHT, ZNEAR, ZFAR)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(EYE_X, EYE_Y, EYE_Z, CENTER_X, CENTER_Y, CENTER_Z, UP_X, UP_Y, UP_Z)
    
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    
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
    # deteccción de colisones para el mapa backrooms (su geometría)
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
    #verificar límites del mapa
    if abs(new_x) > MAP_BOUNDARY or abs(new_z) > MAP_BOUNDARY:
        return False
    
    if check_collision(new_x, new_z):
        return False
    
    return True

def draw_simple_floor():
    """Draw a simple floor if map doesn't load"""
    glColor3f(1.0, 1.0, 0.0)  # Yellow color like backrooms
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

def draw_hud():
    """Draw HUD with collectible count"""
    if game_state != "playing" or not collectible_manager:
        return
    
    # Save current OpenGL state
    glPushAttrib(GL_ALL_ATTRIB_BITS)
    glPushMatrix()
    
    # Configure for 2D rendering
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    # Switch to orthographic projection
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Draw collectible counter
    collected = collectible_manager.get_collected_count()
    total = collectible_manager.num_items
    
    
    # Text (simplified - just showing concept)
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2.0)
    
    # Draw "Items: X/Y" using simple lines
    # This is a simplified representation - in a real game you'd use proper text rendering
    
    # Restore projection
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    # Restore OpenGL state
    glPopMatrix()
    glPopAttrib()

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
    
    # Draw axes for debugging (comment out later)
    # draw_axes()
    
    # Draw the map or simple floor
    if map_model:
        glPushMatrix()
        glColor3f(1.0, 0.0, 0.0)  # Backrooms yellowish color
        map_model.render()
        glPopMatrix()
    else:
        draw_simple_floor()
    
    # Draw collectibles
    if collectible_manager:
        collectible_manager.render()
    
    # Draw monster if game is playing
    if game_state == "playing" and monster:
        monster.render()
    
    # Draw HUD
    draw_hud()

def handle_input():
    """Handle keyboard input during gameplay"""
    if game_state != "playing":
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

def reset_game():
    """Reset game to initial state"""
    global EYE_X, EYE_Y, EYE_Z, theta, direction, game_state, monster, collectible_manager
    
    # Reset player position
    EYE_X = 0.0
    EYE_Y = PLAYER_HEIGHT
    EYE_Z = 0.0
    theta = 0.0
    direction = [1.0, 0.0, 0.0]
    
    # Reset monster
    monster = Monster(start_x=8.0, start_z=8.0) 
    
    # Reset collectibles
    collectible_manager = CollectibleManager(num_items=3)  # Spawn 3 collectible items
    
    # Reset game state
    game_state = "playing"
    
    update_camera()
    print("Game reset!")
    print(f"Collect all {collectible_manager.num_items} items to win!")

def main():
    """Main game loop"""
    global monster, game_over_screen, win_screen, collectible_manager, game_state
    
    pygame.init()
    
    # Initialize OpenGL
    init_opengl()
    
    # Load map
    map_filename = 'backroom.obj'
    load_map(map_filename)
    
    # Initialize game objects
    monster = Monster(start_x=8.0, start_z=8.0)
    #monster =  None
    game_over_screen = GameOverScreen()
    win_screen = WinScreen()
    collectible_manager = CollectibleManager(num_items=3)  # 3 collectible items to win
    
    # Game loop
    clock = pygame.time.Clock()
    running = True
    
    print("BACKROOMS: COLLECT AND ESCAPE!")
    print("Controls:")
    print("- Arrow Keys or WASD: Move and rotate")
    print("- ESC: Exit")
    print("- R: Restart (during game over or win)")
    
    while running:
        current_time = time.time()
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and game_state in ["game_over", "won"]:
                    reset_game()
        
        if game_state == "playing":
            # Handle gameplay input
            handle_input()
            
            # Update collectibles
            if collectible_manager:
                collectible_manager.update(current_time, EYE_X, EYE_Z)
                
                # Check win condition
                if collectible_manager.all_collected():
                    game_state = "won"
                    print("¡CONGRATULATIONS! You collected all items!")
                    print("Press R to play again or ESC to exit")
            
            # Update monster AI
            if monster:
                game_over = monster.update(EYE_X, EYE_Z, collision_faces, current_time)
                if game_over:
                    game_state = "game_over"
                    print("Press R to restart or ESC to exit")
            
            # Render game
            render_scene()
            
        elif game_state == "game_over":
            # Render game over screen
            render_scene()  # Render scene in background
            game_over_screen.draw_game_over()
            
            # Handle game over input
            game_over_action = game_over_screen.handle_game_over_input()
            if game_over_action == "exit":
                running = False
            elif game_over_action == "restart":
                reset_game()
                
        elif game_state == "won":
            # Render win screen
            render_scene()  # Render scene in background
            win_screen.draw_win_screen()
            
            # Handle win screen input
            win_action = win_screen.handle_win_input()
            if win_action == "exit":
                running = False
            elif win_action == "restart":
                reset_game()
        
        # Update display
        pygame.display.flip()
        clock.tick(60)  # 60 FPS
    
    # Cleanup
    if map_model:
        map_model.free()
    if monster and monster.model:
        monster.model.free()
    pygame.quit()

if __name__ == "__main__":
    main()