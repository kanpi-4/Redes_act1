import SocketTCP

address = ("127.0.0.1", 8000)

client = SocketTCP.SocketTCP()
client.debug = True
client.set_congestion_control(True)

print("[CLIENTE] Conectando...")
client.connect(address)

data = b"x" * 2000
print("[CLIENTE] Enviando 2000 bytes...")
client.send(data, mode="go_back_n")

print(f"[CLIENTE] Transmisión finalizada. Segmentos totales enviados: {client.number_of_sent_segments}")
client.close()