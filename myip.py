from myiputils import *
import struct
import mytcputils


def create_ipv4_header(vihl, dscpecn, identification, flagsfrag, ttl, proto, checksum, src_addr, dest_addr):
    datagram = struct.pack('!BBHHHBBHII', vihl, dscpecn, total_len, identification, flagsfrag, ttl, proto, checksum, src_addr, dest_addr)
    return datagram
    
class CamadaRede:
    def __init__(self, enlace):
        """
        Inicia a camada de rede. Recebe como argumento uma implementação
        de camada de enlace capaz de localizar os next_hop (por exemplo,
        Ethernet com ARP).
        """
        self.callback = None
        self.enlace = enlace
        self.enlace.registrar_recebedor(self.__raw_recv)
        self.meu_endereco = None
        
        self.tabela = []

    def __raw_recv(self, datagrama):
        dscp, ecn, identification, flags, frag_offset, ttl, proto, \
           src_addr, dst_addr, payload = read_ipv4_header(datagrama)
        if dst_addr == self.meu_endereco:
            # atua como host
            if proto == IPPROTO_TCP and self.callback:
                self.callback(src_addr, dst_addr, payload)
        else:
            # atua como roteador
            next_hop = self._next_hop(dst_addr)
            # TODO: Trate corretamente o campo TTL do datagrama
            vihl, dscpecn, total_len, identification, flagsfrag, ttl, proto, \
                checksum, src_addr, dest_addr = \
                struct.unpack('!BBHHHBBHII', datagrama[:20])
            ttl -= 1
            
            datagrama2 = struct.pack('!BBHHHBBH', (4 << 4) + 5, 0, len(datagrama[20:]) + 20, 0, 0, ttl, 6, 0) + datagrama[12:16] + datagrama[16:20]
            data_checksum = mytcputils.calc_checksum(datagrama2)
            print(ttl)
            if ttl > 0:
            
                
                datagrama2 = struct.pack('!BBHHHBBH', (4 << 4) + 5, 0, len(datagrama[20:]) + 20, 0, 0, ttl, 6, data_checksum) + datagrama[12:16] + datagrama[16:20]
                
                self.enlace.enviar(datagrama2, next_hop)
                
            else:
                #print(self.meu_endereco)
                #print(addr2str(datagrama[12:16]))
                #print(addr2str(datagrama[16:20]))
                #mytcputils.str2addr(self.meu_endereco)
            
                datafake = struct.pack('!BBHHHBBH', (4 << 4) + 5, 0, 20 + 8 + max(28, len(datagrama[20:])), 0, 0, 64, 1, 0) + \
                    mytcputils.str2addr(self.meu_endereco) + datagrama[12:16]
                
                data_checksum = mytcputils.calc_checksum(datafake)
                
                outro_checksum = mytcputils.calc_checksum(struct.pack('BBHI', 11, 0, 0, 0) + datagrama[:28])
                print(outro_checksum)
                
                print(struct.pack('!BBHI', 11, 0, outro_checksum, 0))
                datafake = struct.pack('!BBHHHBBH',  (4 << 4) + 5, 0, 20 + 8 + max(28, len(datagrama[20:])), 0, 0, 64, 1, data_checksum) + \
                    mytcputils.str2addr(self.meu_endereco) + datagrama[12:16] + struct.pack('!BBHI', 11, 0, outro_checksum, 0) + datagrama[:28]
                print(len(datafake))
                self.enlace.enviar(datafake, next_hop)

    def _calc_dif(self, tabela, dest):
        calculo = []
        for t in tabela:
            ind = 0
            for i in range(len(t)):
                if t[i] == dest[i]: 
                    ind += 1
                else:
                    break
            calculo.append(ind)
        return calculo

    def _calc_dist(self, dest_addr):
        
        dest = dest_addr.split('.')
        dest_str = "{:0>8b}{:0>8b}{:0>8b}{:0>8b}".format(int(dest[0]), int(dest[1]), int(dest[2]), int(dest[3]))
        
        tabela = []
        val_matchs = []
        for t in self.tabela:
            _t = t[0].split('.')
            val_matchs.append(int(_t[3].split('/')[1]))
            _t[3] = _t[3].split('/')[0]
            tabela.append("{:0>8b}{:0>8b}{:0>8b}{:0>8b}".format(int(_t[0]), int(_t[1]), int(_t[2]), int(_t[3])))
        
        calculo = self._calc_dif(tabela, dest_str)
        print(calculo)
        val = max(calculo)
        
        
        for val2 in range(0, val + 1):
            trueVal = val - val2
            for i in range(len(calculo)):
            
                if(val_matchs[len(calculo) - i - 1] > calculo[len(calculo) - i - 1]):
                    print("SKIP {} -> {}/{}/{}".format(self.tabela[len(calculo) - i - 1], val_matchs[len(calculo) - i - 1], calculo[len(calculo) - i - 1], val))
                    continue
            
                print("{} -> {}/{}/{}".format(self.tabela[len(calculo) - i - 1], val_matchs[len(calculo) - i - 1], calculo[len(calculo) - i - 1], val))
                
                if tabela[len(calculo) - i - 1] == dest_str:
                    return self.tabela[len(calculo) - i - 1][1]
            
                '''for val2 in range(0, val + 1):
                    print("{}".format(val - val2), end=' ')
                print()'''
                
                if calculo[len(calculo) - i - 1] == trueVal:
                    print(self.tabela[len(calculo) - i - 1][0])
                    print("> {0}\n> {1}".format(dest_str, tabela[len(calculo) - i - 1]))
                    print("> ", end='')
                    print(" "*(calculo[len(calculo) - i - 1]) + "^")
                    print("> ", end='')
                    print(" "*(trueVal) + "*")
                    if val_matchs[len(calculo) - i - 1] > trueVal:
                        
                        print("--- MATCH NONE " + str(val) + " " + str(val_matchs[len(calculo) - i - 1]) + " " + str(calculo[len(calculo) - i - 1]))
                        continue
                    
                    #if dest_str[calculo[len(calculo) - i - 1]] == '1':
                    #    print("{0} -> *{1}*".format(len(calculo) - i - 1, dest_str[calculo[len(calculo) - i - 1]]))
                    #    return None
                    
                    print("MATCH {} [{}]".format(self.tabela[len(calculo) - i - 1], val) + " " + str(val_matchs[len(calculo) - i - 1]) + " " + str(calculo[len(calculo) - i - 1]))
                    return self.tabela[len(calculo) - i - 1][1]
        
        
        return None

    def _next_hop(self, dest_addr):
        # TODO: Use a tabela de encaminhamento para determinar o próximo salto
        # (next_hop) a partir do endereço de destino do datagrama (dest_addr).
        # Retorne o next_hop para o dest_addr fornecido.
        
        print('\n::: DEST_ADDR {}'.format(dest_addr))
        #print(self.tabela)
        return self._calc_dist(dest_addr)
        
        return None

    def definir_endereco_host(self, meu_endereco):
        """
        Define qual o endereço IPv4 (string no formato x.y.z.w) deste host.
        Se recebermos datagramas destinados a outros endereços em vez desse,
        atuaremos como roteador em vez de atuar como host.
        """
        self.meu_endereco = meu_endereco
        print("MEU_ENDERECO {0}".format(self.meu_endereco))

    def definir_tabela_encaminhamento(self, tabela):
        """
        Define a tabela de encaminhamento no formato
        [(cidr0, next_hop0), (cidr1, next_hop1), ...]

        Onde os CIDR são fornecidos no formato 'x.y.z.w/n', e os
        next_hop são fornecidos no formato 'x.y.z.w'.
        """
        self.tabela = []
        for t in tabela:
            self.tabela.append([t[0], t[1]])
        # TODO: Guarde a tabela de encaminhamento. Se julgar conveniente,
        # converta-a em uma estrutura de dados mais eficiente.
        pass

    def registrar_recebedor(self, callback):
        """
        Registra uma função para ser chamada quando dados vierem da camada de rede
        """
        self.callback = callback

    def enviar(self, segmento, dest_addr):
        """
        Envia segmento para dest_addr, onde dest_addr é um endereço IPv4
        (string no formato x.y.z.w).
        """
        
        
        next_hop = self._next_hop(dest_addr)        
        print("DEST_ADDR {0} NEXT_HOP {1} MEU_END {2}".format(dest_addr, next_hop, self.meu_endereco))
        
        dest = dest_addr.split('.')
        destino = [int(dest[0]), int(dest[1]), int(dest[2]), int(dest[3])]
        val = destino[3] << 24
        val += destino[2] << 16
        val += destino[1] << 8
        val += destino[0] << 0     
        val_dst = val
        
        val_dst = mytcputils.str2addr(dest_addr)
        
        dest = self.meu_endereco.split('.')
        destino = [int(dest[0]), int(dest[1]), int(dest[2]), int(dest[3])]
        val = destino[3] << 24
        val += destino[2] << 16
        val += destino[1] << 8
        val += destino[0] << 0
        val_src = val
        
        val_src = mytcputils.str2addr(self.meu_endereco)
        
        version = 4
        ihl = 5
            
        datagrama = struct.pack('!BBHHHBBH', (version << 4) + ihl, 0, len(segmento) + 20, 0, 0, 64, 6, 0) + val_src + val_dst
        data_checksum = mytcputils.calc_checksum(datagrama)
        datagrama = struct.pack('!BBHHHBBH', (version << 4) + ihl, 0, len(segmento) + 20, 0, 0, 64, 6, data_checksum) + val_src + val_dst + segmento
            
        #datagrama = ((4 << 4) + 5).to_bytes(1, 'little') + (0).to_bytes(7, 'little') + (64).to_bytes(1, 'little') + (0).to_bytes(7, 'little')  + datagrama
        # TODO: Assumindo que a camada superior é o protocolo TCP, monte o
        # datagrama com o cabeçalho IP, contendo como payload o segmento.
        self.enlace.enviar(datagrama, next_hop)
