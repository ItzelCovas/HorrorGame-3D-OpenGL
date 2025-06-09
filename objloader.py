import os
import pygame
from OpenGL.GL import *

class OBJ:
    """Enhanced OBJ loader for the Backrooms game"""
    generate_on_init = True
    
    @classmethod
    def loadTexture(cls, imagefile):
        """Load texture from image file"""
        try:
            surf = pygame.image.load(imagefile)
            image = pygame.image.tostring(surf, 'RGBA', 1)
            ix, iy = surf.get_rect().size
            texid = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texid)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
            return texid
        except Exception as e:
            return None

    @classmethod
    def loadMaterial(cls, filename):
        """Load material file (.mtl)"""
        contents = {}
        mtl = None
        dirname = os.path.dirname(filename)

        try:
            for line in open(filename, "r"):
                if line.startswith('#'): continue
                values = line.split()
                if not values: continue
                
                if values[0] == 'newmtl':
                    mtl = contents[values[1]] = {}
                elif mtl is None:
                    raise ValueError("mtl file doesn't start with newmtl stmt")
                elif values[0] == 'map_Kd':
                    # load the texture referred to by this declaration
                    mtl[values[0]] = values[1]
                    imagefile = os.path.join(dirname, mtl['map_Kd'])
                    if os.path.exists(imagefile):
                        mtl['texture_Kd'] = cls.loadTexture(imagefile)
                    else:
                        mtl['texture_Kd'] = None
                else:
                    try:
                        mtl[values[0]] = list(map(float, values[1:]))
                    except ValueError:
                        mtl[values[0]] = values[1:]
        except Exception as e:
            print(f"Error loading material file {filename}: {e}")
            return {}
        
        return contents

    def __init__(self, filename, swapyz=False):
        """Load a Wavefront OBJ file"""
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.mtl = {}
        self.gl_list = 0
        
        dirname = os.path.dirname(filename)
        material = None
        
        try:
            print(f"Loading OBJ file: {filename}")
            
            for line in open(filename, "r"):
                if line.startswith('#'): continue
                values = line.split()
                if not values: continue
                
                if values[0] == 'v':
                    # Vertex coordinates
                    v = list(map(float, values[1:4]))
                    if swapyz:
                        v = v[0], v[2], v[1]
                    self.vertices.append(v)
                    
                elif values[0] == 'vn':
                    # Vertex normals
                    v = list(map(float, values[1:4]))
                    if swapyz:
                        v = v[0], v[2], v[1]
                    self.normals.append(v)
                    
                elif values[0] == 'vt':
                    # Texture coordinates
                    self.texcoords.append(list(map(float, values[1:3])))
                    
                elif values[0] in ('usemtl', 'usemat'):
                    # Material usage
                    material = values[1]
                    
                elif values[0] == 'mtllib':
                    # Material library
                    mtl_file = os.path.join(dirname, values[1])
                    if os.path.exists(mtl_file):
                        self.mtl = self.loadMaterial(mtl_file)
                    else:
                        print(f"--")
                        
                elif values[0] == 'f':
                    # Face definition
                    face = []
                    texcoords = []
                    norms = []
                    
                    for v in values[1:]:
                        w = v.split('/')
                        face.append(int(w[0]))
                        
                        # Texture coordinates
                        if len(w) >= 2 and len(w[1]) > 0:
                            texcoords.append(int(w[1]))
                        else:
                            texcoords.append(0)
                            
                        # Normals
                        if len(w) >= 3 and len(w[2]) > 0:
                            norms.append(int(w[2]))
                        else:
                            norms.append(0)
                            
                    self.faces.append((face, norms, texcoords, material))
            
            print(f"Loaded: {len(self.vertices)} vertices, {len(self.faces)} faces")
            
        except Exception as e:
            print(f"Error loading OBJ file {filename}: {e}")
            raise
        
        if self.generate_on_init:
            self.generate()

    def generate(self):
        """Generate OpenGL display list"""
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        
        glEnable(GL_TEXTURE_2D)
        glFrontFace(GL_CCW)
        
        for face in self.faces:
            vertices, normals, texture_coords, material = face
            
            # Set material properties
            if material and material in self.mtl:
                mtl = self.mtl[material]
                
                if 'texture_Kd' in mtl and mtl['texture_Kd']:
                    # Use diffuse texture
                    glBindTexture(GL_TEXTURE_2D, mtl['texture_Kd'])
                else:
                    # Use diffuse color or default
                    if 'Kd' in mtl:
                        glColor3f(*mtl['Kd'][:3])
                    else:
                        glColor3f(0.8, 0.8, 0.6)  # Default backrooms color
            else:
                # Default material
                glColor3f(0.8, 0.8, 0.6)  # Backrooms yellowish color
            
            # Draw the face
            if len(vertices) == 3:
                glBegin(GL_TRIANGLES)
            elif len(vertices) == 4:
                glBegin(GL_QUADS)
            else:
                glBegin(GL_POLYGON)
            
            for i in range(len(vertices)):
                # Normal
                if i < len(normals) and normals[i] > 0 and normals[i] <= len(self.normals):
                    glNormal3fv(self.normals[normals[i] - 1])
                
                # Texture coordinate
                if i < len(texture_coords) and texture_coords[i] > 0 and texture_coords[i] <= len(self.texcoords):
                    glTexCoord2fv(self.texcoords[texture_coords[i] - 1])
                
                # Vertex
                if vertices[i] <= len(self.vertices):
                    glVertex3fv(self.vertices[vertices[i] - 1])
            
            glEnd()
        
        glDisable(GL_TEXTURE_2D)
        glEndList()

    def render(self):
        """Render the OBJ model"""
        if self.gl_list:
            glCallList(self.gl_list)

    def free(self):
        """Free OpenGL resources"""
        if self.gl_list:
            glDeleteLists(self.gl_list, 1)
            self.gl_list = 0