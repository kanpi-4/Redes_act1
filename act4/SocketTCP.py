import socket
import random
import time

from CongestionControl import CongestionControl
from socketUDP import SocketUDP
from slidingWindowCC import SlidingWindowCC

class SocketTCP:
    TIMEOUT = 0.2
    MAX_DATA_SIZE = 16
    HEADER_SIZE = 7
    SEGMENT_SIZE = HEADER_SIZE + MAX_DATA_SIZE

    def __init__(self):
        self.number_of_sent_segments = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(self.TIMEOUT)

        self.my_address = None 
        self.remote_address = None 

        self.conected = False
        
        self.seq = 0
        self.ack = 0

        self.remaining_bytes = None
        self.recv_buffer = b''

        self.role = None 
        self.debug = True
        self.congestion_control_on = False

    def set_congestion_control(self, enabled: bool):
        self.congestion_control_on = enabled

    def bind(self, address):
        self.role = 'server'
        self.socket.bind(address)
        self.my_address = self.socket.getsockname()

    def connect(self, address):
        self.role = 'client'
        self.remote_address = address
        x = random.randint(0, 100)

        self.socket.settimeout(self.TIMEOUT)
        syn = {'syn': True, 'seq': x}

        attempts = 0
        max_attempts = 20

        while attempts < max_attempts:
            self._tx(address, syn)

            try:
                syn_ack, receive_address = self._rx(get_address=True)
                
                if SocketTCP._match_flags(syn_ack, syn=True, ack=True) and syn_ack['seq'] == (x + 1) and not syn_ack['data']:
                    self.remote_address = receive_address  
                    ack = {'ack': True, 'seq': x + 2}
                    self.seq = ack['seq']
                    # enviamos el ack final 3 veces seguidas para asegurar llegada con 20% de prdidas
                    for _ in range(3):
                        self._tx(self.remote_address, ack)
                    self.conected = True
                    return
            except socket.timeout:
                attempts += 1

        # si agoto intentos, asignamos seq para evitar el crash con Nonetype
        self.seq = x + 2
        if self.debug:
            self._log("ERROR No se pudo conectar con el servidor.")

    def accept(self):
        while True:
            try:
                syn, receiver_address = self._rx(get_address=True)
                if SocketTCP._match_flags(syn, syn=True) and not syn['data']:
                    break
            except socket.timeout:
                continue
        x = syn['seq']

        new_socket = SocketTCP()
        host = self.my_address[0]
        new_socket.bind((host, 0))
        new_socket.remote_address = receiver_address

        syn_ack = {'syn': True, 'ack': True, 'seq': x + 1}

        while True:
            new_socket._tx(receiver_address, syn_ack)

            try:
                while True:
                    segment = new_socket._rx()
                    if SocketTCP._match_flags(segment, ack=True) and segment['seq'] == (x + 2) and not segment['data']:
                        new_socket.conected = True
                        new_socket.seq = segment['seq']
                        return new_socket, new_socket.my_address
                    elif new_socket._match_flags(segment) and segment['seq'] == (x + 2) and segment['data']:
                        new_socket.seq = segment['seq']
                        message_length = new_socket._receive_message_length(segment)
                        new_socket.remaining_bytes = message_length 
                        new_socket.conected = True
                        return new_socket, new_socket.my_address
            except socket.timeout:
                continue

    def send_using_stop_and_wait(self, message: bytes):
        self._send_message_length(message)

        for i in range(0, len(message), self.MAX_DATA_SIZE):
            data = message[i:i + self.MAX_DATA_SIZE]
            segment = {'seq': self.seq, 'data': data}
            expected_ack = self.seq + len(data)

            while True:
                self._tx(self.remote_address, segment)
                try:
                    while True:
                        ack = self._rx()
                        if (self._match_flags(ack, ack=True) and ack['seq'] == expected_ack and not ack['data']):
                            self.seq = expected_ack
                            break
                    break  
                except socket.timeout:
                    continue  

    def recv_using_stop_and_wait(self, buff_size: int) -> bytes:
        if buff_size < 0:
            raise ValueError("buff_size no puede ser negativo")
        if buff_size == 0:
            return b''
        
        if self.remaining_bytes is None:
            message_length = self._receive_message_length()
            if message_length is None:
                return b''
            self.remaining_bytes = message_length

        target = min(self.remaining_bytes, buff_size)
        timeouts_count = 0
        max_timeouts = 15

        while len(self.recv_buffer) < target and timeouts_count < max_timeouts:
            try:
                segment = self._rx()
                timeouts_count = 0  # reiniciamos contador si llega algo

                if not self._match_flags(segment) or not segment['data']:
                    continue

                if segment['seq'] < self.seq:
                    ack = {'ack': True, 'seq': self.seq}
                    self._tx(self.remote_address, ack)
                    continue
                elif segment['seq'] == self.seq:
                    data = segment['data']

                    if len(data) > self.remaining_bytes - len(self.recv_buffer):
                        continue

                    self.recv_buffer += data
                    self.seq += len(data)

                    ack = {'ack': True, 'seq': self.seq}
                    self._tx(self.remote_address, ack)
            except socket.timeout:
                timeouts_count += 1
                # volver a pedir retrnasmision confirmando el ultimo ack procesado
                if self.seq is not None:
                    ack = {'ack': True, 'seq': self.seq}
                    self._tx(self.remote_address, ack)

        message_received = self.recv_buffer[:target]
        self.recv_buffer = self.recv_buffer[target:]
        self.remaining_bytes -= len(message_received)

        if self.remaining_bytes == 0:
            self.remaining_bytes = None

        return message_received
    def send(self, message: bytes, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            self.send_using_stop_and_wait(message)
        elif mode == "go_back_n":
            self.send_using_go_back_n(message)

    def recv(self, buff_size: int, mode="stop_and_wait") -> bytes:
        if mode == "stop_and_wait":
            return self.recv_using_stop_and_wait(buff_size)
        elif mode == "go_back_n":
            return self.recv_using_go_back_n(buff_size)

    def close(self):
        # si no hay socket o no hay direccion remota (ej: socket pasivo del servidor), cerramos directo
        if self.socket is None or self.remote_address is None:
            if self.socket:
                try:
                    self.socket.close()
                except Exception:
                    pass
            self.conected = False
            return

        # resiliencia contra valores NoneType en seq y ack
        if getattr(self, 'seq', None) is None:
            self.seq = 0
        if getattr(self, 'ack', None) is None:
            self.ack = 0

        z = self.seq
        fin = {
            'seq': z,
            'ack': self.ack,
            'flags': {'SYN': 0, 'ACK': 0, 'FIN': 1},
            'data': b""
        }

        n_timeout = 0
        max_timeouts = 2

        # intentamos el cierre ordenado con reintentos
        while n_timeout < max_timeouts:
            try:
                self._tx(self.remote_address, fin)
                segment = self._rx()
                if segment and self._match_flags(segment, ack=True) and segment.get('seq') == z + 1:
                    ack_pkt = {
                        'seq': z + 1,
                        'ack': z + 2,
                        'flags': {'SYN': 0, 'ACK': 1, 'FIN': 0},
                        'data': b""
                    }
                    self._tx(self.remote_address, ack_pkt)
                    break
            except Exception:
                n_timeout += 1

        # cerramos el socket físicamente de forma segura
        self.conected = False
        try:
            self.socket.close()
        except Exception:
            pass

    def recv_close(self):
        z = self.seq
        waiting_ack = False
        n_timeout = 0
        
        while n_timeout < 2:
            try:
                segment = self._rx()

                if (self._match_flags(segment, fin=True) and segment['seq'] == z and not segment['data']):
                    waiting_ack = True
                    fin_ack = {'ack': True, 'fin': True, 'seq': z + 1}
                    self._tx(self.remote_address, fin_ack)
                elif (waiting_ack and self._match_flags(segment, ack=True) and segment['seq'] == z + 2 and not segment['data']):   
                    break
                elif (self._match_flags(segment) and segment['seq'] < z and segment['data']):
                    ack = {'ack': True, 'seq': z}
                    self._tx(self.remote_address, ack)

            except socket.timeout:
                if waiting_ack:
                    n_timeout += 1
                    
        self.conected = False
        try:
            self.socket.close()
        except Exception:
            pass

    def _send_message_length(self, message: bytes):
        message_length = len(message).to_bytes(16, 'big') 
        segment = {'seq': self.seq, 'data': message_length}
        expected_seq = self.seq + len(message_length)
        
        max_attempts = 30
        attempts = 0

        while attempts < max_attempts:
            self._tx(self.remote_address, segment)
            try:
                while True:
                    ack = self._rx()
                    if SocketTCP._match_flags(ack, ack=True) and ack['seq'] == expected_seq and not ack['data']:
                        self.seq = expected_seq
                        return
            except socket.timeout:
                attempts += 1
                
        if self.debug:
            self._log("ERROR: No se pudo enviar el tamaño del mensaje tras varios intentos.")

    def _receive_message_length(self, segment=None) -> int:
        while True:
            try:
                if segment is None:
                    segment = self._rx()

                if self._match_flags(segment) and segment['seq'] < self.seq:
                    ack = {'ack': True, 'seq': self.seq}
                    self._tx(self.remote_address, ack)
                    segment = None
                    continue

                if self._match_flags(segment) and segment['seq'] == self.seq and segment['data']:
                    new_seq = segment['seq'] + len(segment['data'])
                    ack = {'ack': True, 'seq': new_seq}
                    self._tx(self.remote_address, ack)
                    
                    message_length = int.from_bytes(segment['data'], 'big')
                    self.seq = new_seq
                    return message_length

                segment = None
            except socket.timeout:
                continue

    def _tx(self, address, segment: dict):
        segment_byte = SocketTCP.create_segment(**segment)
        self.number_of_sent_segments += 1
        self.socket.sendto(segment_byte, address)

    def _rx(self, get_address=False):
        segment_byte, address = self.socket.recvfrom(self.SEGMENT_SIZE)
        segment_dict = SocketTCP.parse_segment(segment_byte)
        if get_address:
            return segment_dict, address
        return segment_dict

    def _log(self, msg: str):
        if self.debug:
            print(f"[{self.role}] {msg}")

    @staticmethod
    def create_segment(syn: bool = False, ack: bool = False, fin: bool = False, seq=0, data: bytes = b'') -> bytes:
        header = bytes([int(syn), int(ack), int(fin)])
        header += seq.to_bytes(4, 'big')
        return header + bytes(data[:SocketTCP.MAX_DATA_SIZE])

    @staticmethod
    def parse_segment(segment: bytes) -> dict:
        return {
            'syn': bool(segment[0]),
            'ack': bool(segment[1]),
            'fin': bool(segment[2]),
            'seq': int.from_bytes(segment[3:SocketTCP.HEADER_SIZE], 'big'),
            'data': segment[SocketTCP.HEADER_SIZE:SocketTCP.SEGMENT_SIZE],
        }

    @staticmethod
    def _match_flags(segment_dict: dict, syn=False, ack=False, fin=False) -> bool:
        return (
            segment_dict['syn'] == syn and
            segment_dict['ack'] == ack and
            segment_dict['fin'] == fin
        )




    def send_using_go_back_n(self, message: bytes):
        self._send_message_length(message)

        mss = 8
        segments_data = [message[i:i + mss] for i in range(0, len(message), mss)]
        if not segments_data:
            return

        if self.congestion_control_on:
            congestion_controller = CongestionControl(MSS=mss)
            window_size = int(congestion_controller.get_cwnd())
            if self.debug:
                state = getattr(congestion_controller, 'state', 'N/A')
                ssthresh = getattr(congestion_controller, 'ssthresh', 'N/A')
                self._log(f"(debug cc) [INICIO] Estado: {state} | cwnd: {window_size} bytes ({window_size//mss} MSS) | ssthresh: {ssthresh}")
        else:
            congestion_controller = None
            window_size = 8
            if self.debug:
                self._log(f"(debug cc) [OFF] Ventana fija N={window_size}")

        base_seq = self.seq
        window = SlidingWindowCC(window_size, segments_data, base_seq)
        sent_count = 0

        def send_window_slot(idx):
            seq = window.get_sequence_number(idx)
            data = window.get_data(idx)
            if seq is not None and data is not None:
                segment = {'seq': seq, 'data': data}
                self._tx(self.remote_address, segment) # <- Esto suma +1 al contador

        consecutive_timeouts = 0
        max_timeouts = 10

        while window.get_sequence_number(0) is not None:
            curr_win_size = window.window_size

            for i in range(curr_win_size):
                if window.get_data(i) is not None and i >= sent_count:
                    send_window_slot(i)
                    sent_count += 1

            try:
                ack = self._rx()
                if self._match_flags(ack, ack=True) and not ack['data']:
                    ack_seq = ack['seq']
                    base_seq_current = window.get_sequence_number(0)

                    if base_seq_current is not None and ack_seq > base_seq_current:
                        # si llega un ack valido, reiniciamos los timeouts consecutivos
                        consecutive_timeouts = 0

                        while True:
                            steps = 0
                            for i in range(window.window_size):
                                seq_i = window.get_sequence_number(i)
                                data_i = window.get_data(i)
                                if seq_i is not None and data_i is not None:
                                    if seq_i + len(data_i) <= ack_seq:
                                        steps += 1

                            if ack_seq > (window.get_sequence_number(0) or 0) and steps > 0:
                                window.move_window(steps)
                                sent_count = max(0, sent_count - steps)
                                new_base = window.get_sequence_number(0)
                                if new_base is None or new_base >= ack_seq:
                                    break
                            else:
                                break

                        self.seq = ack_seq

                        if self.congestion_control_on and congestion_controller:
                            congestion_controller.event_ack_received()
                            window_size = int(congestion_controller.get_cwnd())
                            window.update_window_size(window_size)
                            if self.debug:
                                state = getattr(congestion_controller, 'state', 'N/A')
                                ssthresh = getattr(congestion_controller, 'ssthresh', 'N/A')
                                base_actual = window.get_sequence_number(0)
                                self._log(f"(debug cc) [ACK {ack_seq}] Estado: {state} | cwnd: {window_size} bytes | ssthresh: {ssthresh} | Base Seq: {base_actual}")

            except socket.timeout:
                consecutive_timeouts += 1

                if self.congestion_control_on and congestion_controller:
                    congestion_controller.event_timeout()
                    window_size = int(congestion_controller.get_cwnd())
                    window.update_window_size(window_size)
                    if self.debug:
                        state = getattr(congestion_controller, 'state', 'N/A')
                        ssthresh = getattr(congestion_controller, 'ssthresh', 'N/A')
                        base_actual = window.get_sequence_number(0)
                        self._log(f"(debug cc) [TIMEOUT] Estado: {state} | cwnd caen a: {window_size} bytes | ssthresh: {ssthresh} | Base Seq: {base_actual}")

                self._log(f"RX: TIMEOUT ({consecutive_timeouts}/{max_timeouts})")
                
                # si se supera el limite de reintentos consecutivos, salimos del bucle para no congelar la ejecucion
                if consecutive_timeouts >= max_timeouts:
                    self._log("ERROR: Se alcanzó el número máximo de reintentos. Abortando transmisión.")
                    break

                sent_count = 0

    def recv_using_go_back_n(self, buff_size: int) -> bytes:
        return self.recv_using_stop_and_wait(buff_size)