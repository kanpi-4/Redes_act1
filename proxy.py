import socket
import json 
import sys




ruta_json = sys.argv[1]

with open(ruta_json, 'r', encoding='utf-8') as archivo:
        configuracion = json.load(archivo)
        nombre_usuario = configuracion["user"]
        








def parse_HTTP_message(http_message: bytes) -> dict:
  
    # convertimos de bytes a texto plano
    texto = http_message.decode('utf-8', errors='ignore')
    
    # separacion del encabezado del body
    partes = texto.split("\r\n\r\n", 1)
    encabezado_completo = partes[0]
    cuerpo = partes[1] if len(partes) > 1 else ""
    
    # separamos la info del encabezado
    lineas = encabezado_completo.split("\r\n")
    
    # primera linea dentro del header
    linea_inicio = lineas[0].split(" ")
    
    # estructura que devolveremos
    data = {
        "tipo": "",          # respuesta o peticion
        "metodo_o_version": "", # get post / HTTP/1.1
        "url_o_estado": "",     # /index.html / 200 OK
        "headers": {},       # diccionario con los encabezados
        "body": cuerpo       
    }
    # peticion o respuesta
    if linea_inicio[0].startswith("HTTP/"):
        data["tipo"] = "Respuesta"
        data["metodo_o_version"] = linea_inicio[0] 
        # unimos el codigo de estado y el texto  "200" + "OK" = "200 OK"
        data["url_o_estado"] = " ".join(linea_inicio[1:]) 
    else:
        data["tipo"] = "Peticion"
        data["metodo_o_version"] = linea_inicio[0]  
        data["url_o_estado"] = linea_inicio[1]     
    
    # procesar todos los headers
    for linea in lineas[1:]:
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            # strip quita los espacios en blanco rebeldes al inicio y final
            data["headers"][clave.strip()] = valor.strip()
            
    return data


def create_HTTP_message(http_data: dict) -> bytes:

    lineas = []
    
    # primera linea segun el tipo de mensaje
    if http_data["tipo"] == "Peticion":
        # get /index.html HTTP/1.1
        linea_inicio = f"{http_data['metodo_o_version']} {http_data['url_o_estado']} HTTP/1.1"
    else:
        # HTTP/1.1 200 OK
        linea_inicio = f"{http_data['metodo_o_version']} {http_data['url_o_estado']}"
        
    lineas.append(linea_inicio)
    
    # headers
    for clave, valor in http_data["headers"].items():
        lineas.append(f"{clave}: {valor}")
        
    # union datos del encabezado
    encabezado_str = "\r\n".join(lineas)
    
    # encabezado y cuerpo
    mensaje_completo_str = f"{encabezado_str}\r\n\r\n{http_data['body']}"
    
    # bytes
    return mensaje_completo_str.encode('utf-8')







# codigo html
html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Mi Servidor HTTP</title>
</head>
<body>
    <h1>lololol</h1>
    <p>lolol desde debian 13</p>
</body>
</html>"""



#largo del html en bytes
html_bytes_len = len(html_content.encode('utf-8'))









proxy_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

proxy_server_socket.bind(('0.0.0.0', 8000))
proxy_server_socket.listen(5)
    
    
print("Servidor HTTP corriendo y escuchando en el puerto 8000...")



while True:
    # aceptar al cliente y se crea socket2
    client_socket, client_address = proxy_server_socket.accept()
    
    
    # part5
    #bucle para recibir todo el mensaje
    request_bytes = b""
    BUFF_SIZE = 500
    
    while True:
        chunk = client_socket.recv(BUFF_SIZE)
        if not chunk:
            break
        request_bytes += chunk
        
        # \r\n\r\n indica el fin del encabezado
        if b"\r\n\r\n" in request_bytes:
            # revisamos si viene un body
            # vemos el content
            req_temporal = parse_HTTP_message(request_bytes)
            content_length = int(req_temporal["headers"].get("Content-Length", 0))
            
            # vemos cuantos bytes nos falta para terminar con el cuerpo
            bytes_headers_len = request_bytes.find(b"\r\n\r\n") + 4
            bytes_cuerpo_actuales = len(request_bytes) - bytes_headers_len
            
            # si terminamos lo que decia el content_lenght estamos listos
            if bytes_cuerpo_actuales >= content_length:
                break
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # parseamos peticion
    req_data = parse_HTTP_message(request_bytes)
        
    # extraemos host
    host_destino = req_data["headers"].get("Host")
    
    print(f"\npeticion capturada y con destino a {host_destino}")
    
    
    
    
    
    
    
    
    
    
    
    
    
    # VERIFICAR SI EL SITIO ESTA BLOQUEADO
    # Extraemos la ruta solicitada (
    ruta_solicitada = req_data.get("url_o_estado", "")
    
    # si la ruta empieza con http://, hay que quitarlo para qeu coincida con el json"
    if ruta_solicitada.startswith("http://"):
        url_completa = ruta_solicitada.replace("http://", "", 1)
    elif ruta_solicitada.startswith("https://"):
        url_completa = ruta_solicitada.replace("https://", "", 1)
    else:
        url_completa = f"{host_destino}{ruta_solicitada}"
        
    print(f"URL: {url_completa}")
    
    if url_completa in configuracion.get("blocked", []):
        print(f"trafico denegado hacia {host_destino}")
        

        html_bloqueo = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>no puedes estar aca bro</title>
        </head>
        <body>
            <h1>no puedes estar aca bro</h1>
            <br>
           
            <img src="gatobailando.png" alt="gato 403" style="border-radius: 10px; max-width: 500px;">
            <br><br>
            <p><em>X-ElQuePregunta: """ + nombre_usuario + """</em></p>
        </body>
        </html>"""
        datos_respuesta_bloqueo = {
            "tipo": "Respuesta",
            "metodo_o_version": "HTTP/1.1",
            "url_o_estado": "403 Forbidden",
            "headers": {
                "Content-Type": "text/html; charset=utf-8",
                "Content-Length": str(len(html_bloqueo.encode('utf-8'))),
                "Connection": "close",
                "X-ElQuePregunta": nombre_usuario
            },
            "body": html_bloqueo
        }
        bytes_respuesta = create_HTTP_message(datos_respuesta_bloqueo)
        client_socket.send(bytes_respuesta)
        client_socket.close()
        continue
    #cuando queramos subir la foto del gato
    if "gatobailando.png" in req_data.get("url_o_estado", ""):
        print("subiendo gatos bailando...")
        with open("gatobailando.png", "rb") as archivo_img:
                contenido_imagen_bytes = archivo_img.read()
        headers_img = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: image/png\r\n"
                f"Content-Length: {len(contenido_imagen_bytes)}\r\n"
                "Connection: close\r\n\r\n"
            ).encode('utf-8')

        respuesta_completa_img = headers_img + contenido_imagen_bytes
        client_socket.send(respuesta_completa_img)
        client_socket.close()

        continue
     
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # creacion socket3 para hablar con el servidor
    socket3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    

    socket3.connect((host_destino, 80))
    
    
    
    
    #parte3 actividad:
    #parseamos la peticion del cliente
    req_modificada_data = parse_HTTP_message(request_bytes)
    #añadimos el nuevo header
    req_modificada_data["headers"]["X-ElQuePregunta"] = nombre_usuario
    #lo pasamos denuevo a bytes
    request_modificada_bytes = create_HTTP_message(req_modificada_data)
    
    
    
    
    
    
    
    
    
    
    
    # envio de peticion al servidor
    socket3.send(request_modificada_bytes)
    
    
    # bucle por si la respuesta es mas grande que 4096 bytes
    response_bytes = b""
   
    
    while True:
        chunk = socket3.recv(500)
        #si el servidor cierra la conexion, se acabo
        if not chunk:
            break
        response_bytes += chunk
        
        
        #se hace lo mismo que se hizo con el cliente para recibir 
        #con un buffer pequeño
        if b"\r\n\r\n" in response_bytes:
            res_temporal = parse_HTTP_message(response_bytes)
            content_length = int(res_temporal["headers"].get("Content-Length", 0))
        
        if content_length > 0:
            bytes_headers_len = response_bytes.find(b"\r\n\r\n") + 4
            bytes_cuerpo_actuales = len(response_bytes) - bytes_headers_len
            
         
            if bytes_cuerpo_actuales >= content_length:
                break
    
        
    
    
    
    
    
    #accedemos a la respuesta del servidor
    res_data = parse_HTTP_message(response_bytes)
    #tomamos su html
    cuerpo_texto = res_data["body"]    
    #reemplazamos palabras
    for par_palabras in configuracion.get("forbidden_words", []):
            for palabra_original, palabra_reemplazo in par_palabras.items():
                cuerpo_texto = cuerpo_texto.replace(palabra_original,palabra_reemplazo)
                
    # actualizamos el html del response
    res_data["body"] = cuerpo_texto
    
    #actualizmaos el largo del content lenght
    
    nuevo_largo_bytes = len(cuerpo_texto.encode('utf-8', errors='ignore'))
    res_data["headers"]["Content-Length"] = str(nuevo_largo_bytes)
    
    #volvemos a los bytes
    response_bytes_censurado = create_HTTP_message(res_data)
    
        
        
        
        
        
        
        
     
        
        
        
        
    # responder al cliente
    client_socket.send(response_bytes_censurado)
    print(f"respuesta enviada al cliente.")
    
    
#cerramos sockets
    client_socket.close()
    socket3.close()
    
    
    
    
    
    
  



  