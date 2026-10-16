import SocketTCP

address = ("127.0.0.1", 8000)

server = SocketTCP.SocketTCP()
server.bind(address)
print("[SERVIDOR] Esperando conexión...")

connection, client_addr = server.accept()
print("[SERVIDOR] Conexión aceptada. Recibiendo datos...")

data = connection.recv(1000, mode="go_back_n")
print(f"[SERVIDOR] Recibidos {len(data)} bytes. Cerrando conexión.")

try:
    connection.recv_close()
except Exception:
    pass

server.close()