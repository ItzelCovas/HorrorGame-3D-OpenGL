# monster.py
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import time
from collections import deque
import random
from objloader import OBJ

class Monster:
    def __init__(self, start_x=10.0, start_z=10.0):
        # Position and movement
        self.x = start_x
        self.z = start_z
        self.y = 0.7  # Height above ground
        self.target_x = start_x
        self.target_z = start_z
        
        # Monster properties
        self.radius = 0.4  # Collision radius
        self.height = 1.0  # Monster height
        self.speed = 0.04  # Movement speed (slower than player)
        self.detection_range = 18.0  # How far monster can "see" player
        
        # AI and pathfinding
        self.path = []  # Current path to follow
        self.current_path_index = 0
        self.last_pathfind_time = 0
        self.pathfind_interval = 5.0  # Recalculate path every second
        self.grid_size = 1.5  # Grid resolution for pathfinding
        self.last_player_pos = (0, 0)
        
        # State management
        self.state = "patrol"  # "patrol", "hunting", "following_path"
        self.patrol_points = [(8, 8), (8, -8), (8, -8), (-8, 8)]
        self.current_patrol_index = 0
        
        # Model loading
        self.model = None
        self.load_model()
        
        # Animation
        self.bob_offset = 0
        self.bob_speed = 0.0
        
        print(f"Monster spawned at ({self.x}, {self.z})")
    
    def load_model(self):
        """Load monster 3D model"""
        try:
            self.model = OBJ('monster.obj', swapyz=False)
            print("Monster model loaded successfully")
        except Exception as e:
            print(f"Could not load monster model: {e}")
            self.model = None
    
    def world_to_grid(self, x, z):
        """Convert world coordinates to grid coordinates"""
        grid_x = int((x + 20) / self.grid_size)  # Offset to make positive
        grid_z = int((z + 20) / self.grid_size)
        return (grid_x, grid_z)
    
    def grid_to_world(self, grid_x, grid_z):
        """Convert grid coordinates to world coordinates"""
        world_x = (grid_x * self.grid_size) - 20
        world_z = (grid_z * self.grid_size) - 20
        return (world_x, world_z)
    
    def is_position_valid(self, x, z, collision_faces):
        """Check if a position is valid (no collision with walls)"""
        # Check map boundaries
        if abs(x) > 19.0 or abs(z) > 19.0:
            return False
        
        # Check collision with walls using same logic as player
        for face in collision_faces:
            vertices = face['vertices']
            face_type = face['type']
            min_y = face['min_y']
            max_y = face['max_y']
            
            if face_type in ['wall', 'obstacle']:
                if self.check_collision_with_box(x, z, vertices, min_y, max_y):
                    return False
        
        return True
    
    def check_collision_with_box(self, x, z, box_vertices, box_min_y, box_max_y):
        """Check collision between monster and a box-shaped obstacle"""
        monster_min_y = self.y - self.height/2
        monster_max_y = self.y + self.height/2
        
        # Check vertical overlap
        if monster_max_y < box_min_y or monster_min_y > box_max_y:
            return False
        
        # checar horizontal collision
        box_min_x = min([v[0] for v in box_vertices])
        box_max_x = max([v[0] for v in box_vertices])
        box_min_z = min([v[2] for v in box_vertices])
        box_max_z = max([v[2] for v in box_vertices])
        
        closest_x = max(box_min_x, min(x, box_max_x))
        closest_z = max(box_min_z, min(z, box_max_z))
        
        distance = math.sqrt((x - closest_x)**2 + (z - closest_z)**2)
        
        return distance < self.radius
    
    def get_neighbors(self, grid_pos, collision_faces):
        #Obtener posiciones vecinas válidas"""
        neighbors = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), 
                    (-1, -1), (-1, 1), (1, -1), (1, 1)]  # 8-directional movimiento
        
        for dx, dz in directions:
            new_grid_x = grid_pos[0] + dx
            new_grid_z = grid_pos[1] + dz
            
            # Convert to world coordinates and check validity
            world_x, world_z = self.grid_to_world(new_grid_x, new_grid_z)
            
            if self.is_position_valid(world_x, world_z, collision_faces):
                neighbors.append((new_grid_x, new_grid_z))
        
        return neighbors
    
    def bfs_pathfind(self, start_pos, target_pos, collision_faces):
        #BFS para el camino más corto al jugador 
        start_grid = self.world_to_grid(start_pos[0], start_pos[1])
        target_grid = self.world_to_grid(target_pos[0], target_pos[1])
        
        if start_grid == target_grid:
            return []
        
        # BFS implementation
        queue = deque([(start_grid, [])])
        visited = set([start_grid])
        max_iterations = 90  # Prevent infinite loops
        iterations = 0
        
        while queue and iterations < max_iterations:
            iterations += 1
            current_pos, path = queue.popleft()
            
            # checa si se llegó al objetivo
            if current_pos == target_grid:
                # Convert path back to world coordinates
                world_path = []
                for grid_pos in path:
                    world_x, world_z = self.grid_to_world(grid_pos[0], grid_pos[1])
                    world_path.append((world_x, world_z))
                return world_path
            
            # ver vecinos
            for neighbor in self.get_neighbors(current_pos, collision_faces):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = path + [neighbor]
                    queue.append((neighbor, new_path))
        
        # No path found
        return []
    
    def can_see_player(self, player_x, player_z, collision_faces):
        """Check if monster has line of sight to player"""
        distance = math.sqrt((player_x - self.x)**2 + (player_z - self.z)**2)
        
        if distance > self.detection_range:
            return False
        
        # Simple line of sight check - sample points along the line
        num_samples = int(distance / 0.5)  # Sample every 0.5 units
        
        for i in range(1, num_samples):
            t = i / num_samples
            check_x = self.x + t * (player_x - self.x)
            check_z = self.z + t * (player_z - self.z)
            
            if not self.is_position_valid(check_x, check_z, collision_faces):
                return False
        
        return True
    
    def update_ai_state(self, player_x, player_z, collision_faces, current_time):
        #Update monster AI state based on player position
        #Estados: patrol, hunting, following_path
        player_distance = math.sqrt((player_x - self.x)**2 + (player_z - self.z)**2)
        can_see = self.can_see_player(player_x, player_z, collision_faces)
        
        #Estados
        if can_see and player_distance <= self.detection_range:
            if self.state != "hunting":
                self.state = "hunting"
                print("Monstruo cazando")
        elif self.state == "hunting" and (not can_see or player_distance > self.detection_range * 1.5):
            # Lost sight of player, regresa a patrol
            self.state = "patrol"
            print("Monster lost sight of player, returning to patrol") #para debbug
        
        # Handle pathfinding
        if current_time - self.last_pathfind_time > self.pathfind_interval:
            self.last_pathfind_time = current_time
            
            if self.state == "hunting":
                # encontrar camino a jugador
                new_path = self.bfs_pathfind((self.x, self.z), (player_x, player_z), collision_faces)
                if new_path:
                    self.path = new_path
                    self.current_path_index = 0
                    self.state = "following_path"
                    self.last_player_pos = (player_x, player_z)
            
            elif self.state == "patrol":
                # Find path to next patrol point
                patrol_target = self.patrol_points[self.current_patrol_index]
                patrol_distance = math.sqrt((patrol_target[0] - self.x)**2 + (patrol_target[1] - self.z)**2)
                
                if patrol_distance < 1.0:  # Reached patrol point
                    self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)
                    patrol_target = self.patrol_points[self.current_patrol_index]
                
                new_path = self.bfs_pathfind((self.x, self.z), patrol_target, collision_faces)
                if new_path:
                    self.path = new_path
                    self.current_path_index = 0
                    self.state = "following_path"
    
    def follow_path(self):
        #move along current path
        if not self.path or self.current_path_index >= len(self.path):
            return
        
        target_x, target_z = self.path[self.current_path_index]
        
        dx = target_x - self.x
        dz = target_z - self.z
        distance = math.sqrt(dx**2 + dz**2)
        
        if distance < 0.3:  # Close enough to current waypoint
            self.current_path_index += 1
            if self.current_path_index >= len(self.path):
                # Reached end of path
                self.path = []
                self.current_path_index = 0
                if self.state == "following_path":
                    self.state = "patrol"  # Return to patrol after reaching destination
        else:
            # Move towards waypoint
            move_x = (dx / distance) * self.speed
            move_z = (dz / distance) * self.speed
            
            self.x += move_x
            self.z += move_z
    
    def check_player_collision(self, player_x, player_z):
        """Check if monster caught the player"""
        distance = math.sqrt((player_x - self.x)**2 + (player_z - self.z)**2)
        return distance < (self.radius + 0.5)  # Monster radius + player buffer
    
    def update(self, player_x, player_z, collision_faces, current_time):
        """Main update function"""
        # Update AI state and pathfinding
        self.update_ai_state(player_x, player_z, collision_faces, current_time)
        
        # Move along current path
        self.follow_path()
        
        # Update animation
        self.bob_offset = math.sin(current_time * self.bob_speed) * 0.1
        
        # Check if monster caught player
        if self.check_player_collision(player_x, player_z):
            return True  # Game over
        
        return False
    
    def render(self):
        """Render the monster"""
        glPushMatrix()
        
        # Position the monster
        glTranslatef(self.x, self.y, self.z)
        
        # Scale the monster
        glScalef(0.8, 0.8, 0.8)
        
        if self.model:
            # Render the loaded model
            glColor3f(0.3, 0.1, 0.1)  # Dark red color
            self.model.render()
        else:
            # Render a simple geometric shape if model doesn't load
            glColor3f(0.8, 0.2, 0.2)  # Red color
            
            # Draw a simple monster shape using primitives
            glPushMatrix()
            glTranslatef(0, 0, 0)
            
            # Body (main cylinder)
            glPushMatrix()
            glRotatef(90, 1, 0, 0)
            quadric = gluNewQuadric()
            gluCylinder(quadric, 0.3, 0.3, 1.5, 8, 1)
            gluDeleteQuadric(quadric)
            glPopMatrix()
            
            # Head (sphere)
            glPushMatrix()
            glTranslatef(0, 0.8, 0)
            quadric = gluNewQuadric()
            gluSphere(quadric, 0.4, 8, 8)
            gluDeleteQuadric(quadric)
            glPopMatrix()
            
            # Eyes (small spheres)
            glColor3f(1.0, 0.0, 0.0)  # Bright red eyes
            glPushMatrix()
            glTranslatef(-0.15, 0.9, 0.3)
            quadric = gluNewQuadric()
            gluSphere(quadric, 0.05, 6, 6)
            gluDeleteQuadric(quadric)
            glPopMatrix()
            
            glPushMatrix()
            glTranslatef(0.15, 0.9, 0.3)
            quadric = gluNewQuadric()
            gluSphere(quadric, 0.05, 6, 6)
            gluDeleteQuadric(quadric)
            glPopMatrix()
            
            glPopMatrix()
        
        glPopMatrix()
        
        # Debug: Draw path if in debug mode
        if hasattr(self, 'debug') and self.debug and self.path:
            self.draw_debug_path()
    
    def draw_debug_path(self):
        """Draw the current path for debugging"""
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.0, 1.0)  # Magenta color for path
        glLineWidth(3.0)
        
        glBegin(GL_LINE_STRIP)
        glVertex3f(self.x, self.y + 0.5, self.z)  # Start from monster position
        
        for waypoint in self.path:
            glVertex3f(waypoint[0], self.y + 0.5, waypoint[1])
        
        glEnd()
        
        # Draw waypoint markers
        for i, waypoint in enumerate(self.path):
            glPushMatrix()
            glTranslatef(waypoint[0], self.y + 0.5, waypoint[1])
            
            if i == self.current_path_index:
                glColor3f(1.0, 1.0, 0.0)  # Yellow for current target
            else:
                glColor3f(0.0, 1.0, 0.0)  # Green for other waypoints
            
            quadric = gluNewQuadric()
            gluSphere(quadric, 0.1, 6, 6)
            gluDeleteQuadric(quadric)
            glPopMatrix()
        
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
    
    def enable_debug(self):
        self.debug = True
    
    def disable_debug(self):
        self.debug = False
    
    def get_state_info(self):
        """Get current state information for debugging"""
        return {
            'position': (self.x, self.z),
            'state': self.state,
            'path_length': len(self.path),
            'current_waypoint': self.current_path_index,
            'patrol_target': self.current_patrol_index
        }