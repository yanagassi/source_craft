
from __future__ import division 
import random
import time

from collections import deque
from pyglet import image
from pyglet.gl import *
from pyglet.graphics import TextureGroup 
from settings import *
from Loads import *
from Window import *
from Utils import *

class Model:
    def __init__(self):
        
        # Um Batch é uma coleção de listas de vértices para renderização em lote.
        self.batch = pyglet.graphics.Batch()

        # Um TextureGroup gerencia uma textura OpenGL.
        self.group = TextureGroup(image.load(TEXTURE_PATH).get_texture())

        # Um mapeamento de posição para a textura do bloco naquela posição.
        # Isso define todos os blocos que estão atualmente no mundo.
        self.world = {}

        # O mesmo mapeamento que `world`, mas contém apenas blocos que estão sendo mostrados.
        self.shown = {}

        # Mapeamento de posição para um pyglet `VertexList` para todos os blocos mostrados.
        self._shown = {}

        # Mapeamento de setor para uma lista de posições dentro desse setor.
        self.sectors = {}

        # Implementação simples de fila de funções. A fila é preenchida com
        # chamadas de _show_block() e _hide_block()
        self.queue = deque()

        self._initialize()

    def _initialize(self):
        """ Inicializa o mundo colocando todos os blocos.

        """
        n = CHUNK_LENGHT  # 1/2 largura e altura do mundo TAMANHO DA CUNK 
        s = 1  # tamanho do passo
        y = 0  # altura y inicial
        for x in xrange(-n, n + 1, s):
            for z in xrange(-n, n + 1, s): 
                self.add_block((x, y - 2, z), GRASS, immediate=False)
                
                for nzs in range(CHUNK_LENGHT):
                    if(nzs > 1):
                        self.add_block((x, y - nzs, z), GRASS, immediate=False)

                self.add_block((x, y - CHUNK_LENGHT, z), STONE, immediate=False) #bedrock
                self.add_block((x, y + CHUNK_LENGHT, z), STONE, immediate=False) #bedrock

                if x in (-n, n) or z in (-n, n):
                    # criar paredes externas.
                    for dy in xrange(-CHUNK_LENGHT, CHUNK_LENGHT):
                        self.add_block((x, y + dy, z), STONE, immediate=False)
                        

        # gerar as colinas aleatoriamente
        o = n - 10
        for _ in xrange(120):
            a = random.randint(-o, o)  # posição x da colina
            b = random.randint(-o, o)  # posição z da colina
            c = -1  # base da colina
            h = random.randint(1, 6)  # altura da colina
            s = random.randint(4, 8)  # 2 * s é o comprimento lateral da colina
            d = 1  # rapidez com que as colinas diminuem
            t = random.choice([GRASS])
            for y in xrange(c, c + h):
                for x in xrange(a - s, a + s + 1):
                    for z in xrange(b - s, b + s + 1):
                        if (x - a) ** 2 + (z - b) ** 2 > (s + 1) ** 2:
                            continue
                        if (x - 0) ** 2 + (z - 0) ** 2 < 5 ** 2:
                            continue
                        self.add_block((x, y, z), t, immediate=False)
                s -= d  # diminuir o comprimento lateral para que as colinas diminuam

    def hit_test(self, position, vector, max_distance=8):
        """ Pesquisa de linha de visão a partir da posição atual. Se um bloco for
        intersectado, ele é retornado, juntamente com o bloco anterior na linha
        de visão. Se nenhum bloco for encontrado, retorna None, None.

        Parameters
        ----------
        position : tuple de tamanho 3
            A posição (x, y, z) para verificar a visibilidade.
        vector : tuple de tamanho 3
            O vetor de linha de visão.
        max_distance : int
            Quantos blocos de distância procurar uma intersecção.

        """
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in xrange(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None

    def exposed(self, position):
        """ Retorna False se a posição dada estiver cercada em todos os 6 lados por
        blocos, True caso contrário.

        """
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False

    def add_block(self, position, texture, immediate=True):
        """ Adiciona um bloco com a textura e posição dadas ao mundo.

        Parameters
        ----------
        position : tuple de tamanho 3
            A posição (x, y, z) do bloco a ser adicionado.
        texture : lista de tamanho 3
            As coordenadas dos quadrados de textura.
        immediate : bool
            Se o bloco deve ser desenhado imediatamente.

        """
        if position in self.world:
            self.remove_block(position, immediate)
        self.world[position] = texture
        self.sectors.setdefault(sectorize(position), []).append(position)
        if immediate:
            if self.exposed(position):
                self.show_block(position)
            self.check_neighbors(position)
            
        

    def remove_block(self, position, immediate=True):
        """ Remove o bloco na posição dada.

        Parameters
        ----------
        position : tuple de tamanho 3
            A posição (x, y, z) do bloco a ser removido.
        immediate : bool
            Se o bloco deve ser removido imediatamente do canvas.

        """
        del self.world[position]
        self.sectors[sectorize(position)].remove(position)
        if immediate:
            if position in self.shown:
                self.hide_block(position) 
            self.check_neighbors(position)

    def check_neighbors(self, position):
        """ Verifica todos os blocos ao redor da posição e garante que seu estado visual
        esteja atualizado. Isso significa ocultar blocos que não estão expostos e
        garantir que todos os blocos expostos estejam sendo mostrados. Geralmente usado
        depois que um bloco é adicionado ou removido.

        """
        x, y, z = position
        for dx, dy, dz in FACES:
            key = (x + dx, y + dy, z + dz)
            if key not in self.world:
                continue
            if self.exposed(key):
                if key not in self.shown:
                    self.show_block(key)
            else:
                if key in self.shown:
                    self.hide_block(key)

    def show_block(self, position, immediate=True):
        """ Mostra o bloco na posição dada.

        Parameters
        ----------
        position : tuple de tamanho 3
            A posição (x, y, z) do bloco a ser mostrado.
        immediate : bool
            Se o bloco deve ser mostrado imediatamente.

        """
        texture = self.world[position]
        self.shown[position] = texture
        if immediate:
            self._show_block(position, texture)
        else:
            self._enqueue(self._show_block, position, texture)

    def _show_block(self, position, texture):
        """ Implementação privada do método 'show_block()`.

        Parameters
        ----------
        position : tuple de tamanho 3
            A posição (x, y, z) do bloco a ser mostrado.
        texture : lista de tamanho 3
            As coordenadas dos quadrados de textura.

        """
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(texture)
        # criar lista de vértices
        # FIXME Talvez seja melhor usar `add_indexed()`
        self._shown[position] = self.batch.add(24, GL_QUADS, self.group,
            ('v3f/static', vertex_data),
            ('t2f/static', texture_data))

    def hide_block(self, position, immediate=True):
        """ Oculta o bloco na posição dada.

        Parameters
        ----------
        position : tuple de tamanho 3
            A posição (x, y, z) do bloco a ser ocultado.
        immediate : bool
            Se o bloco deve ser removido imediatamente do canvas.

        """
        self.shown.pop(position)
        if immediate:
            self._hide_block(position)
        else:
            self._enqueue(self._hide_block, position)

    def _hide_block(self, position):
        """ Implementação privada do método 'hide_block()`.

        """
        self._shown.pop(position).delete()

    def show_sector(self, sector):
        """ Garante que todos os blocos no setor dado que devem ser mostrados
        sejam desenhados no canvas.

        """
        for position in self.sectors.get(sector, []):
            if position not in self.shown and self.exposed(position):
                self.show_block(position, False)

    def hide_sector(self, sector):
        """ Garante que todos os blocos no setor dado que devem ser ocultados
        sejam removidos do canvas.

        """
        for position in self.sectors.get(sector, []):
            if position in self.shown:
                self.hide_block(position, False)

    def change_sectors(self, before, after):
        """ Move-se do setor `before` para o setor `after`. Um setor é uma
        sub-região x, y contígua do mundo. Setores são usados para acelerar
        a renderização do mundo.

        """
        before_set = set()
        after_set = set()
        pad = 4
        for dx in xrange(-pad, pad + 1):
            for dy in [0]:  # xrange(-pad, pad + 1):
                for dz in xrange(-pad, pad + 1):
                    if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2:
                        continue
                    if before:
                        x, y, z = before
                        before_set.add((x + dx, y + dy, z + dz))
                    if after:
                        x, y, z = after
                        after_set.add((x + dx, y + dy, z + dz))
        show = after_set - before_set
        hide = before_set - after_set
        for sector in show:
            self.show_sector(sector)
        for sector in hide:
            self.hide_sector(sector)

    def _enqueue(self, func, *args):
        """ Adiciona `func` à fila interna.

        """
        self.queue.append((func, args))

    def _dequeue(self):
        """ Remove a função do topo da fila interna e a chama.

        """
        func, args = self.queue.popleft()
        func(*args)

    def process_queue(self):
        """ Processa toda a fila enquanto faz pausas periódicas. Isso permite
        que o loop do jogo seja executado suavemente. A fila contém chamadas para
        _show_block() e _hide_block(), portanto, este método deve ser chamado se
        add_block() ou remove_block() foram chamados com immediate=False.

        """
        start = time.perf_counter()
        while self.queue and time.perf_counter() - start < 1.0 / TICKS_PER_SEC:
            self._dequeue()

    def process_entire_queue(self):
        """ Processa toda a fila sem pausas.

        """
        while self.queue:
            self._dequeue()
