import socket
import sys
from dnslib import DNSRecord, QTYPE
from collections import deque,Counter

# Configuración del servidor Resolver DNS
IP_ESCUCHA = '192.168.1.81' 
PUERTO_ESCUCHA = 8000
tamanobuffer=4096


#estructura para el cache
#guarda maximo las 20 ultimas consultas
historial_consultas=deque(maxlen=20)
#diccionario donde guardaremos los datos en cache
cache={}

def parsear_mensaje_dns(datos_bytes):
    #usamos dnslib
    return DNSRecord.parse(datos_bytes)
  




def resolver(mensaje_consulta, ip_addr='198.41.0.4',nombre_ns="servidor raiz"):
    #parsemas consulta cliente
    consulta_parseada=parsear_mensaje_dns(mensaje_consulta)
    dominio_buscado=str(consulta_parseada.q.qname)
    print(f" dominio consultado: {dominio_buscado}")
    print(f"al Name Server:      {nombre_ns}")
    print(f"A la Dirección IP:   {ip_addr}")
    
   
   
   
   
    #paso a: enviar query a la ip indicada
    #es udp, asi que creamo otro socket
    socket_externo=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    socket_externo.sendto(mensaje_consulta, (ip_addr,53))
    datos_respuesta,_=socket_externo.recvfrom(tamanobuffer)
    socket_externo.close
    
    #parseamos
    respuesta_par=parsear_mensaje_dns(datos_respuesta)
    
    #paso b
    if respuesta_par.rr:
        for registro in respuesta_par.rr:
            if registro.rtype == QTYPE.A:
                print("respuesta tipo A encontrada")
                return datos_respuesta
                
    # paso c, si noy answer revisamos seccion autority
    if respuesta_par.auth:
        # revisar si viene alguna respuesta tipo A en la sección Additional
        if respuesta_par.ar:
            for registro in respuesta_par.ar:
                if registro.rtype == QTYPE.A:
               
                    ip_siguiente = str(registro.rdata)
                    ns_siguente="siguente delegacion TDL"
                    for aut in respuesta_par.auth:
                        if aut.rtype == QTYPE.NS:
                            nombre_siguiente_ns = str(aut.rdata)
                            break
                    
                    #llamada recursiva con la neuva ip encontrada
                    return resolver(mensaje_consulta, ip_addr=ip_siguiente,nombre_ns=ns_siguente)
                
    #si no hoy ips en additional, tomamos el nombre de un name serve
    #de autorithy y usamo recursividad para descurbir primero esa ip
    for registro in respuesta_par.auth:
        if registro.rtype == QTYPE.NS:
            nombre_ns_sub = str(registro.rdata)
            nombre_ns=str(registro.rdata)
            print(f" sin ip en additional, resolviendo recursivamente la ip del NS:{nombre_ns}")
            #mini query dns tipo a para el nombre del nameserver
            query_ns=DNSRecord.question(nombre_ns)
            bytes_query_ns=query_ns.pack()
            
            #llamada recursiva desde la raiz
            bytes_respuesta_ns=resolver(bytes_query_ns,ip_addr='198.41.0.4',nombre_ns="servidor raiz")
            if bytes_respuesta_ns:
                respuesta_ns_parseada=parsear_mensaje_dns(bytes_respuesta_ns)
                for reg in respuesta_ns_parseada.rr:
                    if reg.rtype==QTYPE.A:
                        ip_ns_resuelta=str(reg.rdata)
                        
                    return resolver(mensaje_consulta,ip_addr=ip_ns_resuelta,nombre_ns=nombre_ns_sub)
                    
    #ignoramos si encontramos otra respuesta
    return
            
       
def actualizar_cache(dominio_resuelto,respuesta_bytes):
    historial_consultas.append(dominio_resuelto)
    #contamos la frecuencia
    conteo=Counter(historial_consultas)
    top3tuplas=conteo.most_common(3)
    # extraemos solo los nombres de los dominios
    top3dominios = []
    for tupla in top3tuplas:
        dominio = tupla[0]  
        top3dominios.append(dominio)
        
        
    #si el dominio resuleto es de los 3 mas frecuentes lo guardo
    if dominio_resuelto in top3dominios:
        cache[dominio_resuelto]=respuesta_bytes
    #elimianmos si alguen salio del top3
    
    dominios_en_cache = list(cache.keys())
    for dom in dominios_en_cache:
        if dom not in top3dominios:
            del cache[dom]
            print(f"El dominio {dom} salió del cache")
        
        
       
    
    
    
    
    

#creacion socket udp
resolver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
resolver_socket.bind((IP_ESCUCHA, PUERTO_ESCUCHA))

print(f" resolver dns corriendo y escuchando en {IP_ESCUCHA}:{PUERTO_ESCUCHA}...")


    
# bucle para recibir consultas dns
while True:
   
    # recvfrom da los bytes del mensaje y la dirección del cliente (dig)
    datos_recibidos, direccion_cliente = resolver_socket.recvfrom(tamanobuffer)
    
    #vemos que es lo que pide el cleinte
    consulta_cliente=parsear_mensaje_dns(datos_recibidos)
    dominio_buscado=str(consulta_cliente.q.qname)
    
    # OBTENEMOS EL ID UNICO DE ESTA CONSULTA
    id_consulta_cliente = consulta_cliente.header.id
        
    print(f" consulta recibida de {direccion_cliente[0]}:{direccion_cliente[1]}")
    
    respuesta_final_bytes=None
    
    
    #bsucamos primero en el cache
    if dominio_buscado in cache:
        print(f"respuesta encontrada en el cache")
        respuesta_final_bytes=cache[dominio_buscado]
        
        
        # SOLUCIÓN AL ID MISMATCH Parseamos la respuesta guardada y le ponemos el ID actual del cliente
        respuesta_guardada_bytes = cache[dominio_buscado]
        respuesta_objeto = parsear_mensaje_dns(respuesta_guardada_bytes)
        respuesta_objeto.header.id = id_consulta_cliente # Actualizamos el ID
        
        respuesta_final_bytes = respuesta_objeto.pack() # reempaquetamos los bytes con el id correcto
        
        
        
        
        #refrescamos la frecuencia
        historial_consultas.append(dominio_buscado)
        
    else:
               
         #pasamos los bytes a la funcion resolver
        respuesta_final_bytes=resolver(datos_recibidos,ip_addr='198.41.0.4',nombre_ns="servidor raiz")
        actualizar_cache(dominio_buscado,respuesta_final_bytes)
    
    
    
    
    
    
    
    
   
    
    #enviamos respuesta
    resolver_socket.sendto(respuesta_final_bytes,direccion_cliente)
    
    print(" respuesta DNS enviada con exito")
    
    
        
resolver_socket.close()

