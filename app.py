from __future__ import division
from pyglet.gl import * 
from settings import *
from Window import Window
import random
  



def setup_fog():
    """ Configure the OpenGL fog properties.

    """
    # Habilitar o nevoeiro. O nevoeiro 
    # "mistura uma cor de nevoeiro com a cor pós-texturização de cada fragmento de pixel rasterizado."
    glEnable(GL_FOG)
    # Definir a cor do nevoeiro.
    glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.0, 0.0, 0.1, 1.0))  # Definir a cor do nevoeiro como um tom notuno
    
    # Indicar que não temos preferência entre velocidade de renderização e qualidade.
    glHint(GL_FOG_HINT, GL_DONT_CARE)

    # Especificar a equação usada para calcular o fator de mistura.
    glFogi(GL_FOG_MODE, GL_LINEAR)
    
    # A que distância o nevoeiro começa e termina. Quanto mais próximos o início e o fim,
    # mais denso será o nevoeiro na faixa de nevoeiro.
    glFogf(GL_FOG_START, 20.0)
    glFogf(GL_FOG_END, 60.0)
    


def setup():
    """ Basic OpenGL configuration.

    """
   # Definir a cor de "limpar", ou seja, do céu, em rgba.
    glClearColor(0.0, 0.0, 0.0, 1.0)  
    glEnable(GL_POINT_SMOOTH)  # Habilitar antialiasing para pontos
    glEnable(GL_BLEND)  # Habilitar blending para transparência
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # Função de blending para transparência
    glPointSize(2.0)  # Define o tamanho padrão para pontos

    # Habilitar o descarte (não renderização) de faces voltadas para trás - faces que não estão
    # visíveis para você.
    glEnable(GL_CULL_FACE)
    # Definir a função de minificação/magnificação da textura como GL_NEAREST (o mais próximo
    # na distância de Manhattan) para as coordenadas de textura especificadas. GL_NEAREST
    # "geralmente é mais rápido que o GL_LINEAR, mas pode produzir imagens texturizadas
    # com bordas mais nítidas porque a transição entre os elementos da textura não é
    # tão suave."
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
 
    setup_fog()
    
    

def main():
    window = Window(width=SCREEN_X, height=SCREEN_Y, caption='Pyglet', resizable=True)
    # Hide the mouse cursor and prevent the mouse from leaving the window.
    window.set_exclusive_mouse(True)
    setup()
    pyglet.app.run()


if __name__ == '__main__':
    main()

