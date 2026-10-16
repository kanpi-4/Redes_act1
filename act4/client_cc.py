import SocketTCP
import time

address = ("127.0.0.1", 8000)

client = SocketTCP.SocketTCP()
client.debug = False
client.set_congestion_control(True)  # CON Control de Congestión (TCP Tahoe)

print("[CLIENTE CON CC] Conectando...")
client.connect(address)

data = b"x" * 1000

t0 = time.time()
client.send(data, mode="go_back_n")
t_total = time.time() - t0

sent_segs = getattr(client, 'number_of_sent_segments', 0)
client.close()

print(f"\n>> RESULTADO CON CC: Tiempo = {t_total:.3f} s | Segmentos = {sent_segs}\n")