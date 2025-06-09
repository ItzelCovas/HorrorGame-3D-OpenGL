# win_screen.py
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

class WinScreen:
    def __init__(self):
        self.font = None
        self.init_font()
    
    def init_font(self):
        """Initialize font for text"""
        try:
            pygame.font.init()
            self.font = pygame.font.Font(None, 74)
        except Exception as e:
            print(f"Error initializing font: {e}")
    
    def draw_win_screen(self):
        """Draw YOU WON screen"""
        # Save current OpenGL state
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glPushMatrix()
        
        # Configure for 2D rendering
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Switch to orthographic projection
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, 1200, 0, 800, -1, 1)  # Screen size
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Semi-transparent background (golden/yellow tint for victory)
        glColor4f(0.2, 0.2, 0.0, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(1200, 0)
        glVertex2f(1200, 800)
        glVertex2f(0, 800)
        glEnd()
        
        # Draw victory text
        self.draw_you_won_text()
        
        # Draw instructions
        #self.draw_instructions()
        
        # Restore projection
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        # Restore OpenGL state
        glPopMatrix()
        glPopAttrib()
    
    def draw_you_won_text(self):
        """Draw 'YOU WON' text using OpenGL primitives"""
        glColor3f(0.0, 1.0, 0.0)  # Green color for victory
        glLineWidth(6.0)
        
        # Draw "YOU WON" using lines
        glBegin(GL_LINES)
        
        # Y
        glVertex2f(350, 500)
        glVertex2f(375, 450)
        glVertex2f(375, 450)
        glVertex2f(400, 500)
        glVertex2f(375, 450)
        glVertex2f(375, 400)
        
        # O
        glVertex2f(420, 400)
        glVertex2f(420, 500)
        glVertex2f(420, 500)
        glVertex2f(470, 500)
        glVertex2f(470, 500)
        glVertex2f(470, 400)
        glVertex2f(470, 400)
        glVertex2f(420, 400)
        
        # U
        glVertex2f(490, 500)
        glVertex2f(490, 420)
        glVertex2f(490, 420)
        glVertex2f(490, 400)
        glVertex2f(490, 400)
        glVertex2f(540, 400)
        glVertex2f(540, 400)
        glVertex2f(540, 420)
        glVertex2f(540, 420)
        glVertex2f(540, 500)
        
        glEnd()
        
        # "WON" on second line
        glBegin(GL_LINES)
        
        # W
        glVertex2f(450, 350)
        glVertex2f(465, 250)
        glVertex2f(465, 250)
        glVertex2f(480, 300)
        glVertex2f(480, 300)
        glVertex2f(495, 250)
        glVertex2f(495, 250)
        glVertex2f(510, 350)
        
        # O
        glVertex2f(530, 250)
        glVertex2f(530, 350)
        glVertex2f(530, 350)
        glVertex2f(580, 350)
        glVertex2f(580, 350)
        glVertex2f(580, 250)
        glVertex2f(580, 250)
        glVertex2f(530, 250)
        
        # N
        glVertex2f(600, 250)
        glVertex2f(600, 350)
        glVertex2f(600, 350)
        glVertex2f(650, 250)
        glVertex2f(650, 250)
        glVertex2f(650, 350)
        
        glEnd()
        
        glLineWidth(1.0)
    
    # def draw_instructions(self):
    #     """Draw instruction text"""
    #     glColor3f(1.0, 1.0, 1.0)  # White
    #     glLineWidth(2.0)
        
    #     # Draw "Press R to play again" (simplified)
    #     glBegin(GL_LINES)
        
        # # P
        # glVertex2f(400, 180)
        # glVertex2f(400, 120)
        # glVertex2f(400, 180)
        # glVertex2f(430, 180)
        # glVertex2f(430, 180)
        # glVertex2f(430, 150)
        # glVertex2f(430, 150)
        # glVertex2f(400, 150)
        
        # # R
        # glVertex2f(440, 120)
        # glVertex2f(440, 180)
        # glVertex2f(440, 180)
        # glVertex2f(470, 180)
        # glVertex2f(470, 180)
        # glVertex2f(470, 150)
        # glVertex2f(470, 150)
        # glVertex2f(440, 150)
        # glVertex2f(440, 150)
        # glVertex2f(470, 120)
        
        # # E
        # glVertex2f(480, 120)
        # glVertex2f(480, 180)
        # glVertex2f(480, 180)
        # glVertex2f(510, 180)
        # glVertex2f(480, 150)
        # glVertex2f(505, 150)
        # glVertex2f(480, 120)
        # glVertex2f(510, 120)
        
        # # S (twice for "SS")
        # for offset in [20, 40]:
        #     x_off = 510 + offset
        #     glVertex2f(x_off, 180)
        #     glVertex2f(x_off + 20, 180)
        #     glVertex2f(x_off, 180)
        #     glVertex2f(x_off, 150)
        #     glVertex2f(x_off, 150)
        #     glVertex2f(x_off + 20, 150)
        #     glVertex2f(x_off + 20, 150)
        #     glVertex2f(x_off + 20, 120)
        #     glVertex2f(x_off + 20, 120)
        #     glVertex2f(x_off, 120)
        
        # glEnd()
        
        # # "R to play again" on next line
        # glBegin(GL_LINES)
        
        # # R
        # glVertex2f(450, 80)
        # glVertex2f(450, 40)
        # glVertex2f(450, 80)
        # glVertex2f(480, 80)
        # glVertex2f(480, 80)
        # glVertex2f(480, 60)
        # glVertex2f(480, 60)
        # glVertex2f(450, 60)
        # glVertex2f(450, 60)
        # glVertex2f(480, 40)
        
        # # T
        # glVertex2f(490, 80)
        # glVertex2f(520, 80)
        # glVertex2f(505, 80)
        # glVertex2f(505, 40)
        
        # # O
        # glVertex2f(530, 40)
        # glVertex2f(530, 80)
        # glVertex2f(530, 80)
        # glVertex2f(560, 80)
        # glVertex2f(560, 80)
        # glVertex2f(560, 40)
        # glVertex2f(560, 40)
        # glVertex2f(530, 40)
        
        # glEnd()
        
        glLineWidth(1.0)
    
    def handle_win_input(self):
        """Handle input during win screen"""
        keys = pygame.key.get_pressed()
        
        # ESC to exit
        if keys[pygame.K_ESCAPE]:
            return "exit"
        
        # R to restart
        if keys[pygame.K_r]:
            return "restart"
        
        return "continue"