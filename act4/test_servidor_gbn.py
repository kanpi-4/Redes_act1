import SocketTCP

address = ("127.0.0.1", 8000)

server_socketTCP = SocketTCP.SocketTCP()
server_socketTCP.bind(address)
print("Servidor esperando conexión...")
connection_socketTCP, new_address = server_socketTCP.accept()

# recibir mensaje de prueba en modo Go-Back-N
buff_size = 100
mensaje = connection_socketTCP.recv(buff_size, mode="go_back_n")
print("Servidor recibió:", mensaje.decode(errors='ignore'))

connection_socketTCP.recv_close()
server_socketTCP.socket.close()
print("Servidor finalizado con éxito.")