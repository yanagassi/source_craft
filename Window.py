from __future__ import division
 
import math  
from pyglet.gl import * 
from pyglet.window import key, mouse
from settings import *
from Loads import *
from Model import Model
from Utils import *
import random


class Window(pyglet.window.Window):

    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.stars = self.generate_stars(NUM_STARS)

        # Variável booleana que indica se a janela captura exclusivamente o mouse.
        self.exclusive = False

        # Quando voando, a gravidade não tem efeito e a velocidade é aumentada.
        self.flying = False

        # Strafing é o movimento lateral em relação à direção em que o jogador está olhando,
        # por exemplo, mover para a esquerda ou direita enquanto continua a encarar para frente.
        #
        # O primeiro elemento é -1 quando se move para frente, 1 quando se move para trás e 0
        # caso contrário. O segundo elemento é -1 quando se move para a esquerda, 1 quando se move
        # para a direita e 0 caso contrário.
        self.strafe = [0, 0]

        # Posição atual (x, y, z) no mundo, especificada com números de ponto flutuante. Note que,
        # talvez diferentemente da aula de matemática, o eixo y é o eixo vertical.
        self.position = (0, 0, 0)

        # O primeiro elemento é a rotação do jogador no plano x-z (plano do chão) medida a partir do eixo z para baixo.
        # O segundo é o ângulo de rotação a partir do plano do chão para cima. A rotação é dada em graus.
        #
        # A rotação do plano vertical varia de -90 (olhando diretamente para baixo) a 90 (olhando diretamente para cima).
        # A rotação horizontal não possui limite.
        self.rotation = (0, 0)

        # Setor em que o jogador está atualmente.
        self.sector = None

        # O retículo no centro da tela.
        self.reticle = None

        # Velocidade na direção y (para cima).
        self.dy = 0

        # Uma lista de blocos que o jogador pode colocar. Pressione as teclas numéricas para alternar.
        self.inventory = [BRICK, GRASS, SAND]

        # O bloco atual que o usuário pode colocar. Pressione as teclas numéricas para alternar.
        self.block = self.inventory[0]

        # Lista conveniente das teclas numéricas.
        self.num_keys = [
            key._1, key._2, key._3, key._4, key._5,
            key._6, key._7, key._8, key._9, key._0]

        # Instância do modelo que lida com o mundo.
        self.model = Model()

        # O rótulo exibido no canto superior esquerdo do canvas.
        self.label = pyglet.text.Label('', font_name='Arial', font_size=18,
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
            color=(0, 0, 0, 255))

        # Esta chamada agenda o método `update()` para ser chamado a cada TICKS_PER_SEC.
        # Este é o loop principal do jogo.
        pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)



    def generate_stars(self, num_stars):
        """ Generate static star positions.
        """
        stars = []
        for _ in range(num_stars):
            x = random.uniform(-1.0, 1.0) * SCREEN_X  # Gerar coordenadas aleatórias no eixo X
            y = random.uniform(-1.0, 1.0) * SCREEN_Y  # Gerar coordenadas aleatórias no eixo Y
            stars.append((x, y))
        return stars

    def set_exclusive_mouse(self, exclusive):
        """ Se `exclusive` for True, o jogo irá capturar o mouse; se False,
        o jogo irá ignorar o mouse.

        """
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive

    def get_sight_vector(self):
        """ Retorna o vetor de linha de visão atual indicando a direção
        em que o jogador está olhando.

        """
        x, y = self.rotation
        # y varia de -90 a 90, ou de -pi/2 a pi/2, então m varia de 0 a 1 e
        # é 1 quando olhando à frente, paralelo ao chão, e 0 quando olhando
        # diretamente para cima ou para baixo.
        m = math.cos(math.radians(y))
        # dy varia de -1 a 1 e é -1 quando olhando diretamente para baixo e 1 quando
        # olhando diretamente para cima.
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)

    def get_motion_vector(self):
        """ Retorna o vetor de movimento atual indicando a velocidade do
        jogador.

        Returns
        -------
        vector : tupla de tamanho 3
            Tupla contendo a velocidade nas direções x, y e z, respectivamente.

        """
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle = math.radians(y)
            x_angle = math.radians(x + strafe)
            if self.flying:
                m = math.cos(y_angle)
                dy = math.sin(y_angle)
                if self.strafe[1]:
                    # Movendo para a esquerda ou direita.
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    # Movendo para trás.
                    dy *= -1
                # Quando você está voando para cima ou para baixo, você tem menos movimento
                # para a esquerda e para a direita.
                dx = math.cos(x_angle) * m
                dz = math.sin(x_angle) * m
            else:
                dy = 0.0
                dx = math.cos(x_angle)
                dz = math.sin(x_angle)
        else:
            dy = 0.0
            dx = 0.0
            dz = 0.0
        return (dx, dy, dz)

    def update(self, dt):
        """ Este método é agendado para ser chamado repetidamente pelo relógio do pyglet.

        Parameters
        ----------
        dt : float
            A mudança no tempo desde a última chamada.

        """
        self.model.process_queue()
        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)
            if self.sector is None:
                self.model.process_entire_queue()
            self.sector = sector
        m = 8
        dt = min(dt, 0.2)
        for _ in xrange(m):
            self._update(dt / m)
    def _update(self, dt):
        """ Implementação privada do método `update()`. Aqui é onde a maior parte
        da lógica de movimento está, juntamente com a gravidade e a detecção de colisão.

        Parameters
        ----------
        dt : float
            A mudança no tempo desde a última chamada.

        """
        # andando
        speed = FLYING_SPEED if self.flying else WALKING_SPEED
        d = dt * speed # distância percorrida nesta iteração.
        dx, dy, dz = self.get_motion_vector()
        # Nova posição no espaço, antes de levar em consideração a gravidade.
        dx, dy, dz = dx * d, dy * d, dz * d
        # gravidade
        if not self.flying:
            # Atualiza sua velocidade vertical: se você está caindo, acelera até atingir a velocidade terminal; se você está pulando, desacelera até começar a cair.
            self.dy -= dt * GRAVITY
            self.dy = max(self.dy, -TERMINAL_VELOCITY)
            dy += self.dy * dt
        # colisões
        x, y, z = self.position
        x, y, z = self.collide((x + dx, y + dy, z + dz), PLAYER_HEIGHT)
        self.position = (x, y, z)

    def collide(self, position, height):
        """ Verifica se o jogador na posição `position` e altura `height`
        está colidindo com algum bloco no mundo.

        Parameters
        ----------
        position : tuple de tamanho 3
            A posição (x, y, z) para verificar colisões.
        height : int ou float
            A altura do jogador.

        Returns
        -------
        position : tuple de tamanho 3
            A nova posição do jogador levando em consideração as colisões.

        """
        # Quanta sobreposição com uma dimensão de um bloco circundante é necessária para contar como uma colisão. Se for 0, tocar no terreno conta como uma colisão. Se for 0,49, você afunda no chão, como se estivesse andando por grama alta. Se for maior ou igual a 0,5, você vai cair pelo chão.
        pad = 0.25
        p = list(position)
        np = normalize(position)
        for face in FACES:  # verifica todos os blocos circundantes
            for i in xrange(3):  # verifica cada dimensão independentemente
                if not face[i]:
                    continue
                # Quanta sobreposição você tem com essa dimensão.
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue
                for dy in xrange(height):  # verifica cada altura
                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    if tuple(op) not in self.model.world:
                        continue
                    p[i] -= (d - pad) * face[i]
                    if face == (0, -1, 0) or face == (0, 1, 0):
                        # Você está colidindo com o chão ou o teto, então pare de cair / subir.
                        self.dy = 0
                    break
        return tuple(p)

    def on_mouse_press(self, x, y, button, modifiers):
        """ Chamado quando um botão do mouse é pressionado. Veja a documentação do pyglet para mapeamentos de botão e modificador.

        Parameters
        ----------
        x, y : int
            As coordenadas do clique do mouse. Sempre é o centro da tela se o mouse estiver capturado.
        button : int
            Número que representa o botão do mouse que foi clicado. 1 = botão esquerdo, 4 = botão direito.
        modifiers : int
            Número que representa quaisquer teclas modificadoras que foram pressionadas quando o botão do mouse foi clicado.

        """
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if (button == mouse.RIGHT) or \
                    ((button == mouse.LEFT) and (modifiers & key.MOD_CTRL)):
                # No OSX, control + clique esquerdo = clique direito.
                if previous:
                    self.model.add_block(previous, self.block)
            elif button == pyglet.window.mouse.LEFT and block:
                texture = self.model.world[block]
                if texture != STONE:
                    self.model.remove_block(block)
        else:
            self.set_exclusive_mouse(True)
    def on_mouse_press(self, x, y, button, modifiers):
        """ Chamado quando um botão do mouse é pressionado. Consulte a documentação do pyglet para mapeamentos de botões e modificadores.

        Parameters
        ----------
        x, y : int
            As coordenadas do clique do mouse. Sempre é o centro da tela se o mouse estiver capturado.
        button : int
            Número que representa o botão do mouse que foi clicado. 1 = botão esquerdo, 4 = botão direito.
        modifiers : int
            Número que representa quaisquer teclas modificadoras que foram pressionadas quando o botão do mouse foi clicado.

        """
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if (button == mouse.RIGHT) or \
                    ((button == mouse.LEFT) and (modifiers & key.MOD_CTRL)):
                # No OSX, control + clique esquerdo = clique direito.
                if previous:
                    self.model.add_block(previous, self.block)
            elif button == pyglet.window.mouse.LEFT and block:
                texture = self.model.world[block]
                if texture != STONE:
                    self.model.remove_block(block)
        else:
            self.set_exclusive_mouse(True)

    def on_mouse_motion(self, x, y, dx, dy):
        """ Chamado quando o jogador move o mouse.

        Parameters
        ----------
        x, y : int
            As coordenadas do clique do mouse. Sempre é o centro da tela se o mouse estiver capturado.
        dx, dy : float
            O movimento do mouse.

        """
        if self.exclusive:
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)

    def on_key_press(self, symbol, modifiers):
        """ Chamado quando o jogador pressiona uma tecla. Consulte a documentação do pyglet para mapeamentos de teclas.

        Parameters
        ----------
        symbol : int
            Número que representa a tecla que foi pressionada.
        modifiers : int
            Número que representa quaisquer teclas modificadoras que foram pressionadas.

        """
        if symbol == key.W:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.A:
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1
        elif symbol == key.SPACE:
            if self.dy == 0:
                self.dy = JUMP_SPEED
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol == key.TAB:
            self.flying = not self.flying
        elif symbol in self.num_keys:
            index = (symbol - self.num_keys[0]) % len(self.inventory)
            self.block = self.inventory[index]

    def on_key_release(self, symbol, modifiers):
        """ Chamado quando o jogador solta uma tecla. Consulte a documentação do pyglet para mapeamentos de teclas.

        Parameters
        ----------
        symbol : int
            Número que representa a tecla que foi pressionada.
        modifiers : int
            Número que representa quaisquer teclas modificadoras que foram pressionadas.

        """
        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1

    def on_resize(self, width, height):
        """ Chamado quando a janela é redimensionada para uma nova `largura` e `altura`.

        """
        # rótulo
        self.label.y = height - 10
        # retículo
        if self.reticle:
            self.reticle.delete()
        x, y = self.width // 2, self.height // 2
        n = 10
        self.reticle = pyglet.graphics.vertex_list(4,
            ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n))
        )

    def set_2d(self):
        """ Configura o OpenGL para desenhar em 2D.

        """
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, max(1, width), 0, max(1, height), -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
      
      

    def set_3d(self):
        """ Configura o OpenGL para desenhar em 3D.

        """
        # self.draw_stars()
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        glTranslatef(-x, -y, -z)

    def draw_stars(self):
        """ 
            Draw stars on the screen.
        """
        glPushMatrix()
        glColor4f(1.0, 1.0, 1.0, 1)  # Definir a cor das estrelas como branco e transparência de 0.5
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBegin(GL_POINTS)
        for star in self.stars:
            x, y = star
            glVertex2f(x, y)
        glEnd()
        glPopMatrix()


        
    def on_draw(self):
        """ Chamado pelo pyglet para desenhar o canvas.

        """
        self.clear()
        self.set_3d()
        glColor3d(1, 1, 1)
        
        self.model.batch.draw()

        self.draw_focused_block()
        self.set_2d()
        self.draw_label()
        self.draw_reticle()
       

    def draw_focused_block(self):
        """ Desenha bordas pretas ao redor do bloco que está atualmente sob a mira.

        """
        vector = self.get_sight_vector()
        block = self.model.hit_test(self.position, vector)[0]
        if block:
            x, y, z = block
            vertex_data = cube_vertices(x, y, z, 0.51)
            glColor3d(0, 0, 0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def draw_label(self):
        """ Desenha o rótulo no canto superior esquerdo da tela.

        """
        x, y, z = self.position
        self.label.text = '%02d (%.2f, %.2f, %.2f) %d / %d' % (
            pyglet.clock.get_fps(), x, y, z,
            len(self.model._shown), len(self.model.world))
        self.label.draw()

    def draw_reticle(self):
        """ Desenha o retículo no centro da tela.

        """
        glColor3d(0, 0, 0)
        self.reticle.draw(GL_LINES)

