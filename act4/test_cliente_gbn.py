import SocketTCP

address = ("127.0.0.1", 8000)

client = SocketTCP.SocketTCP()
client.debug = True                          
client.set_congestion_control(True)         
client.connect(address)

mensaje_prueba = b"prueba de envio de datos usando Go-Back-N con ventana de tamano 8"
print("Cliente enviando mensaje...")
client.send(mensaje_prueba, mode="go_back_n")

client.close()
print("Cliente finalizo transmision.")