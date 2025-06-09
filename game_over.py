import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

class GameOverScreen:
    def __init__(self):
        self.font = None
        self.init_font()
    
    def init_font(self):
        """Inicializar fuente para texto"""
        try:
            pygame.font.init()
            self.font = pygame.font.Font(None, 74)
        except Exception as e:
            print(f"Error inicializando fuente: {e}")
    
    def render_text_to_texture(self, text, color=(255, 0, 0)):
        """Convertir texto a textura OpenGL"""
        if not self.font:
            return None
        
        # Renderizar texto en superficie
        text_surface = self.font.render(text, True, color)
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        
        text_width = text_surface.get_width()
        text_height = text_surface.get_height()
        
        # Crear textura OpenGL
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_width, text_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        return texture_id, text_width, text_height
    
    def draw_game_over(self):
        """Dibujar pantalla de Game Over"""
        # Guardar estado OpenGL actual
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glPushMatrix()
        
        # Configurar para renderizado 2D
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Cambiar a proyección ortográfica
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, 1200, 0, 800, -1, 1)  # Tamaño de pantalla
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Fondo semi-transparente
        glColor4f(0.0, 0.0, 0.0, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(1200, 0)
        glVertex2f(1200, 800)
        glVertex2f(0, 800)
        glEnd()
        
        # Dibujar texto simple usando OpenGL primitivas
        self.draw_simple_text()
        
        # Restaurar proyección
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        # Restaurar estado OpenGL
        glPopMatrix()
        glPopAttrib()
    
    def draw_simple_text(self):
        """Dibujar texto simple usando primitivas OpenGL"""
        glColor3f(1.0, 0.0, 0.0)  # Rojo
        glLineWidth(5.0)
        
        # Dibujar "GAME OVER" usando líneas
        # G
        glBegin(GL_LINES)
        # Letra G
        glVertex2f(450, 450)
        glVertex2f(450, 350)
        glVertex2f(450, 450)
        glVertex2f(500, 450)
        glVertex2f(450, 350)
        glVertex2f(500, 350)
        glVertex2f(500, 350)
        glVertex2f(500, 400)
        glVertex2f(475, 400)
        glVertex2f(500, 400)
        
        # A
        glVertex2f(520, 350)
        glVertex2f(520, 450)
        glVertex2f(520, 450)
        glVertex2f(570, 450)
        glVertex2f(570, 450)
        glVertex2f(570, 350)
        glVertex2f(520, 400)
        glVertex2f(570, 400)
        
        # M
        glVertex2f(590, 350)
        glVertex2f(590, 450)
        glVertex2f(590, 450)
        glVertex2f(615, 425)
        glVertex2f(615, 425)
        glVertex2f(640, 450)
        glVertex2f(640, 450)
        glVertex2f(640, 350)
        
        # E
        glVertex2f(660, 350)
        glVertex2f(660, 450)
        glVertex2f(660, 450)
        glVertex2f(710, 450)
        glVertex2f(660, 400)
        glVertex2f(700, 400)
        glVertex2f(660, 350)
        glVertex2f(710, 350)
        glEnd()
        
        # "OVER"
        glBegin(GL_LINES)
        # O
        glVertex2f(450, 300)
        glVertex2f(450, 200)
        glVertex2f(450, 300)
        glVertex2f(500, 300)
        glVertex2f(500, 300)
        glVertex2f(500, 200)
        glVertex2f(500, 200)
        glVertex2f(450, 200)
        
        # V
        glVertex2f(520, 300)
        glVertex2f(545, 200)
        glVertex2f(545, 200)
        glVertex2f(570, 300)
        
        # E
        glVertex2f(590, 200)
        glVertex2f(590, 300)
        glVertex2f(590, 300)
        glVertex2f(640, 300)
        glVertex2f(590, 250)
        glVertex2f(630, 250)
        glVertex2f(590, 200)
        glVertex2f(640, 200)
        
        # R
        glVertex2f(660, 200)
        glVertex2f(660, 300)
        glVertex2f(660, 300)
        glVertex2f(710, 300)
        glVertex2f(710, 300)
        glVertex2f(710, 250)
        glVertex2f(710, 250)
        glVertex2f(660, 250)
        glVertex2f(660, 250)
        glVertex2f(710, 200)
        glEnd()
        
        # Texto de instrucciones
        # glColor3f(1.0, 1.0, 1.0)  # Blanco
        # glLineWidth(2.0)
        
        # "Press ESC to exit" (simplificado)
        # glBegin(GL_LINES)
        # # P
        # glVertex2f(500, 150)
        # glVertex2f(500, 100)
        # glVertex2f(500, 150)
        # glVertex2f(530, 150)
        # glVertex2f(530, 150)
        # glVertex2f(530, 125)
        # glVertex2f(530, 125)
        # glVertex2f(500, 125)
        
        # # R
        # glVertex2f(540, 100)
        # glVertex2f(540, 150)
        # glVertex2f(540, 150)
        # glVertex2f(570, 150)
        # glVertex2f(570, 150)
        # glVertex2f(570, 125)
        # glVertex2f(570, 125)
        # glVertex2f(540, 125)
        # glVertex2f(540, 125)
        # glVertex2f(570, 100)
        
        # # E
        # glVertex2f(580, 100)
        # glVertex2f(580, 150)
        # glVertex2f(580, 150)
        # glVertex2f(610, 150)
        # glVertex2f(580, 125)
        # glVertex2f(605, 125)
        # glVertex2f(580, 100)
        # glVertex2f(610, 100)
        
        # # S (dos veces)
        # for offset in [20, 40]:
        #     x_off = 610 + offset
        #     glVertex2f(x_off, 150)
        #     glVertex2f(x_off + 20, 150)
        #     glVertex2f(x_off, 150)
        #     glVertex2f(x_off, 125)
        #     glVertex2f(x_off, 125)
        #     glVertex2f(x_off + 20, 125)
        #     glVertex2f(x_off + 20, 125)
        #     glVertex2f(x_off + 20, 100)
        #     glVertex2f(x_off + 20, 100)
        #     glVertex2f(x_off, 100)
        # glEnd()
        
        glLineWidth(1.0)
    
    def handle_game_over_input(self):
        """Manejar input durante Game Over"""
        keys = pygame.key.get_pressed()
        
        # ESC para salir
        if keys[pygame.K_ESCAPE]:
            return "exit"
        
        # R para reiniciar (opcional)
        if keys[pygame.K_r]:
            return "restart"
        
        return "continue"