class CamadaEnlace:
    def __init__(self, linhas_seriais):
        """
        Inicia uma camada de enlace com um ou mais enlaces, cada um conectado
        a uma linha serial distinta. O argumento linhas_seriais é um dicionário
        no formato {ip_outra_ponta: linha_serial}. O ip_outra_ponta é o IP do
        host ou roteador que se encontra na outra ponta do enlace, escrito como
        uma string no formato 'x.y.z.w'. A linha_serial é um objeto da classe
        PTY (vide camadafisica.py) ou de outra classe que implemente os métodos
        registrar_recebedor e enviar.
        """
        self.enlaces = {}
        # Constrói um Enlace para cada linha serial
        for ip_outra_ponta, linha_serial in linhas_seriais.items():
            enlace = Enlace(linha_serial)
            self.enlaces[ip_outra_ponta] = enlace
            enlace.registrar_recebedor(self.callback)

    def registrar_recebedor(self, callback):
        """
        Registra uma função para ser chamada quando dados vierem da camada de enlace
        """
        self.callback = callback

    def enviar(self, datagrama, next_hop):
        """
        Envia datagrama para next_hop, onde next_hop é um endereço IPv4
        fornecido como string (no formato x.y.z.w). A camada de enlace se
        responsabilizará por encontrar em qual enlace se encontra o next_hop.
        """
        # Encontra o Enlace capaz de alcançar next_hop e envia por ele
        self.enlaces[next_hop].enviar(datagrama)

    def callback(self, datagrama):
        if self.callback:
            self.callback(datagrama)


class Enlace:
    def __init__(self, linha_serial):
        self.linha_serial = linha_serial
        self.linha_serial.registrar_recebedor(self.__raw_recv)
        self.new_datagrama = bytearray(b'')
        self.marcado = False

    def registrar_recebedor(self, callback):
        self.callback = callback

    def enviar(self, datagrama):
        new_datagrama = bytearray(b'')
        for d in datagrama:
            if d == 192:
                new_datagrama.append(219)
                new_datagrama.append(220)
            elif d == 219:
                new_datagrama.append(219)
                new_datagrama.append(221)
            else:
                new_datagrama.append(d)
        self.linha_serial.enviar((192).to_bytes(1, 'big') + new_datagrama + (192).to_bytes(1, 'big'))
        # TODO: Preencha aqui com o código para enviar o datagrama pela linha
        # serial, fazendo corretamente a delimitação de quadros e o escape de
        # sequências especiais, de acordo com o protocolo SLIP (RFC 1055).
        pass

    def __raw_recv(self, dados):
        #self.new_datagrama = bytearray(b'')
        #for dado in dados:
        for d in dados:
            if d == 219:
                self.marcado = True
            elif self.marcado and d == 220:
                self.new_datagrama.append(192)
                self.marcado = False
            elif self.marcado and d == 221:
                self.new_datagrama.append(219)
                self.marcado = False
            elif d == 192:
                if len(self.new_datagrama) != 0:
                    self.callback(self.new_datagrama)
                    self.new_datagrama = bytearray(b'')
            else:
                self.new_datagrama.append(d)
        # TODO: Preencha aqui com o código para receber dados da linha serial.
        # Trate corretamente as sequências de escape. Quando ler um quadro
        # completo, repasse o datagrama contido nesse quadro para a camada
        # superior chamando self.callback. Cuidado pois o argumento dados pode
        # vir quebrado de várias formas diferentes - por exemplo, podem vir
        # apenas pedaços de um quadro, ou um pedaço de quadro seguido de um
        # pedaço de outro, ou vários quadros de uma vez só.
        pass
