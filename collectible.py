# collectible.py
import math
import random
from OpenGL.GL import *

class CollectibleItem:
    def __init__(self, x, z, item_id):
        """Initialize a collectible item"""
        self.x = x
        self.y = 0.6  # Height above ground (más alto para mejor visibilidad)
        self.z = z
        self.item_id = item_id
        self.collected = False
        
        # Visual properties
        self.size = 0.2 # Más grande para mejor visibilidad
        self.rotation = 0.0
        self.bob_offset = 0.0
        self.base_y = self.y
        
        # Animation properties
        self.rotation_speed = 1.5  # Rotación más rápida
        self.bob_speed = 3.0       # Bob más rápido
        self.bob_amplitude = 0.3   # Mayor amplitud de movimiento vertical
        
        # Collection properties
        self.collection_radius = 1.8  # Radio de colección más amplio
        
        # Color based on ID
        self.color = self.get_color_for_id(item_id)
    
    def get_color_for_id(self, item_id):
        """Get color based on item ID - colores más brillantes"""
        colors = [
            (1.0, 0.2, 0.2),  # Rojo brillante
            (0.2, 1.0, 0.2),  # Verde brillante
            (0.2, 0.2, 1.0),  # Azul brillante
            (1.0, 1.0, 0.2),  # Amarillo brillante
            (1.0, 0.2, 1.0),  # Magenta brillante
            (0.2, 1.0, 1.0),  # Cyan brillante
        ]
        return colors[item_id % len(colors)]
    
    def update(self, current_time):
        #update de animación del item
        if self.collected:
            return
            
        # Rotate the item
        self.rotation += self.rotation_speed
        if self.rotation >= 360:
            self.rotation = 0
        
        # Bob up and down
        self.bob_offset = math.sin(current_time * self.bob_speed) * self.bob_amplitude
        self.y = self.base_y + self.bob_offset
    
    def check_collection(self, player_x, player_z):
        """Check if player is close enough to collect this item"""
        if self.collected:
            return False
            
        distance = math.sqrt((self.x - player_x)**2 + (self.z - player_z)**2)
        return distance < self.collection_radius
    
    def collect(self):
        """Mark item as collected"""
        self.collected = True
    
    def render(self):
        """Render the collectible item with better visibility"""
        if self.collected:
            return
            
        # Disable lighting for bright, glowing effect
        glDisable(GL_LIGHTING)
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation, 0, 1, 0)  # Rotate around Y axis
        glRotatef(self.rotation * 0.7, 1, 0, 0)  # Also rotate around X for more dynamic movement
        
        # Draw main cube with bright color
        glColor3f(*self.color)
        self.draw_cube()
        
        # Add outer glow effect
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glColor4f(self.color[0], self.color[1], self.color[2], 0.3)
        glScalef(1.3, 1.3, 1.3)
        self.draw_cube()
        glDisable(GL_BLEND)
        
        glPopMatrix()
        
        # Re-enable lighting
        glEnable(GL_LIGHTING)
    
    def draw_cube(self):
        """Draw a simple cube"""
        size = self.size
        
        glBegin(GL_QUADS)
        
        # Front face
        glVertex3f(-size, -size, size)
        glVertex3f(size, -size, size)
        glVertex3f(size, size, size)
        glVertex3f(-size, size, size)
        
        # Back face
        glVertex3f(-size, -size, -size)
        glVertex3f(-size, size, -size)
        glVertex3f(size, size, -size)
        glVertex3f(size, -size, -size)
        
        # Top face
        glVertex3f(-size, size, -size)
        glVertex3f(-size, size, size)
        glVertex3f(size, size, size)
        glVertex3f(size, size, -size)
        
        # Bottom face
        glVertex3f(-size, -size, -size)
        glVertex3f(size, -size, -size)
        glVertex3f(size, -size, size)
        glVertex3f(-size, -size, size)
        
        # Right face
        glVertex3f(size, -size, -size)
        glVertex3f(size, size, -size)
        glVertex3f(size, size, size)
        glVertex3f(size, -size, size)
        
        # Left face
        glVertex3f(-size, -size, -size)
        glVertex3f(-size, -size, size)
        glVertex3f(-size, size, size)
        glVertex3f(-size, size, -size)
        
        glEnd()


class CollectibleManager:
    def __init__(self, num_items=3):
        """Initialize collectible manager"""
        self.items = []
        self.num_items = num_items
        self.collected_count = 0
        self.spawn_items()
    
    def spawn_items(self):
        """Spawn collectible items in safe, visible positions"""
        # NUEVAS POSICIONES MEJORADAS - más centrales y visibles
        # Basadas en tu mapa que va de -15 a 15
        safe_spawn_positions = [
            (-7.0, -7.0),   # Esquina inferior izquierda
            (6.0, -6.0),    # Esquina inferior derecha
            (-8.0, 8.0),    # Esquina superior izquierda
            (8.0, 8.0),     # Esquina superior derecha
            (0.0, 0.0),     # Centro del mapa
            (-7.0, 0.0),   # Centro izquierdo
            (8.0, 0.0),    # Centro derecho
            (0.0, -6.0),   # Centro inferior
            (0.0, 7.0),    # Centro superior
            (-5.0, -5.0),   # Cuadrante inferior izquierdo
            (5.0, -5.0),    # Cuadrante inferior derecho
            (-5.0, 5.0),    # Cuadrante superior izquierdo
            (5.0, 5.0),     # Cuadrante superior derecho
        ]
        
        # Randomly select positions for items
        selected_positions = random.sample(safe_spawn_positions, min(self.num_items, len(safe_spawn_positions)))
        
        for i, (x, z) in enumerate(selected_positions):
            item = CollectibleItem(x, z, i)
            self.items.append(item)
            print(f"Cubo {i + 1} spawneado en ({x}, {z})")
    
    def update(self, current_time, player_x, player_z):
        """Update all collectible items"""
        for item in self.items:
            item.update(current_time)
            
            # Check for collection
            if not item.collected and item.check_collection(player_x, player_z):
                item.collect()
                self.collected_count += 1
                
    
    def render(self):
        """Render all collectible items"""
        for item in self.items:
            item.render()
    
    def all_collected(self):
        """Check if all items have been collected"""
        return self.collected_count >= self.num_items
    
    def get_collected_count(self):
        """Get number of collected items"""
        return self.collected_count
    
    def get_nearest_item_info(self, player_x, player_z):
        """Get info about the nearest uncollected item"""
        nearest_item = None
        nearest_distance = float('inf')
        
        for item in self.items:
            if not item.collected:
                distance = math.sqrt((item.x - player_x)**2 + (item.z - player_z)**2)
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_item = item
        
        if nearest_item:
            return {
                'distance': nearest_distance,
                'position': (nearest_item.x, nearest_item.z),
                'id': nearest_item.item_id
            }
        return None
    
    def reset(self):
        """Reset all collectibles"""
        self.items.clear()
        self.collected_count = 0
        self.spawn_items()
