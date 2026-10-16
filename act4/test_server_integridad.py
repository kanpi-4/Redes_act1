import SocketTCP

address = ("127.0.0.1", 8000)

server_socketTCP = SocketTCP.SocketTCP()
server_socketTCP.bind(address)
print("[SERVIDOR] Esperando conexión...")

connection_socketTCP, new_address = server_socketTCP.accept()
print("[SERVIDOR] Conexión aceptada desde:", new_address)

# bloque de datos de 2000 bytes
buff_size = 2000
mensaje = connection_socketTCP.recv(buff_size, mode="go_back_n")

print(f"[SERVIDOR] Bytes recibidos: {len(mensaje)}")

# verificación de integridad
if len(mensaje) == 2000 and mensaje == b"x" * 2000:
    print("[TEST 5 INTEGRIDAD]: PASSED (Los 2000 bytes llegaron 100% íntegros)")
else:
    print(f"[TEST 5 INTEGRIDAD]: FAILED (Se recibieron {len(mensaje)} bytes de 2000 esperados)")

try:
    connection_socketTCP.recv_close()
except Exception:
    pass

server_socketTCP.close()
print("[SERVIDOR] Proceso finalizado.")