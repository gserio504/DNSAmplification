import socket, struct, os, array
from scapy.all import ETH_P_ALL
from scapy.all import select
from scapy.all import MTU
from scapy.all import Ether, IP , TCP, UDP, DNS, Raw
from scapy.all import Packet
from multiprocessing import Process , Queue , Value
import time
class IPSniff( Process ):
 
    def __init__(self, interface_name , queue , terminate_value ):
        super().__init__()

        self.interface_name = interface_name
        self.queue = queue
        self.terminate_value = terminate_value
        # The raw in (listen) socket is a L2 raw socket that listens
        # for all packets going through a specific interface.
        self.ins = socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL)) #can manipulate ETH_P_ALL to dns packets? https://man7.org/linux/man-pages/man7/packet.7.html
        self.ins.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF , 2**30)
        self.ins.bind((self.interface_name, ETH_P_ALL))

        self.received_packets = []

    def run(self):
        print( "Sniffer started")
        time_terminated = None

        while True: 
            pkt, sa_ll = self.ins.recvfrom(MTU)
            self.queue.put_nowait( pkt )

            if self.terminate_value.value == True:
            
                 if time_terminated is None:
                     time_terminated = time.time()
            
                 elif time.time() - time_terminated >= 5:
                    self.queue.put_nowait( "finished" )
                    print( "Packet sniffer terminated" )
                    break

