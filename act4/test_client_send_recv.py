import SocketTCP

address = ("127.0.0.1", 8000)

client_socketTCP = SocketTCP.SocketTCP()
client_socketTCP.connect(address)

# test 1
message = "Mensje de len=16".encode()
client_socketTCP.send(message, mode="go_back_n")

# test 2
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message, mode="go_back_n")

# test 3
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message, mode="go_back_n")

client_socketTCP.close()
print("[CLIENTE] Mensajes enviados y conexión cerrada.")