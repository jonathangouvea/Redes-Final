#!/usr/bin/python3

# seu código aqui
import socket
import select

def recvline(conexao):
	dados = ''		
	while True:
		leitura = conexao.recv(1)
		dados += leitura.decode('utf-8')
		if leitura == b'\n' or leitura == b'':
			return dados

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 7000))
s.listen(5)

apelido = ''

# Cria lista vazia e coloca socket s na lista
lista = []
outputs = []
apelidos = ['']
lista.append(s)

message_queues = []

leituras = ['']

while True:

	# Seleciona lista de sockets prontos para serem lidos
	leitura_pendente, escrita_pendente, _ = select.select(lista, outputs, [])
	
	for sckt in leitura_pendente: # Para cada socket na lista de leuituras pendentes
		
		# Trata nova conexão recebida por meio do socket s
		if sckt == s:
			conexao, endereco = s.accept()
			lista.append(conexao)
			outputs.append(conexao)
			leituras.append('')
			if lista.index(conexao) >= len(apelidos):
				apelidos.append('')
			else:
				apelidos[lista.index(conexao)] = ''
		# Trata mensagem enviada por algum cliente
		else:
			indice = lista.index(sckt)
			lido = leituras[lista.index(sckt)]		
			leitura = b''
			try:
				leitura = sckt.recv(1)
			except:
				pass
				
			lido += leitura.decode('utf-8')
			leituras[lista.index(sckt)]	= lido
			if leitura == b'\n' or leitura == b'':
				apelido = apelidos[lista.index(sckt)]

				if lido == '':
					if apelido != '':
						message_queues.append(('/quit ' + apelido + '\n').encode('utf-8'))
					lista.remove(sckt)
					outputs.remove(sckt)
					escrita_pendente.remove(sckt)
					leituras.remove(leituras[indice])

				if lido[0:6] == "/nick ":
					nick = lido[6::]
					pode = 1
					
					for n in nick:
						if n == ' ' or n == ':':
							pode = 0
							
					for n in apelidos:
						if nick[:-1] == n:
							pode = 0
							
					if pode == 0:
						sckt.send(b"/error\n")
					else:
						if apelido == '':
							message_queues.append(('/joined ' + nick[:-1] + '\n').encode('utf-8'))
						else:
							message_queues.append(('/renamed ' + apelido + ' ' + nick[:-1] + '\n').encode('utf-8'))
						apelido = nick[:-1]
						apelidos[lista.index(sckt)] = apelido
						
				elif apelido == '':
					sckt.send('/error\n'.encode('utf-8'))
					
				else:
					message_queues.append((apelido + ': ' + lido).encode('utf-8'))
					
				if lido != '':
					leituras[indice] = ''
				
	for soc in escrita_pendente:
		for e in message_queues:
			soc.send(e)
	message_queues = []
	
	#Reflexão:
	#	Como não se estabelece um limite máximo de clientes, o servidor pode estar sujeito a um ataque do tipo DoS (Denial of Service),
	#que ocorre quando há invalidação do sistema por sobrecarga de recursos (memória, processamento) se determinado número de clientes tentarem
	#se conectar ao servidor simultaneamente. Além disso, não existe qualquer tipo de proteção das mensagens por criptografia, fazendo com que 
	#qualquer um possa ter acesso ao conteúdo de tudo que foi enviado pelos clientes no chat.
