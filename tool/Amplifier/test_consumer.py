from multiprocessing import Process, Queue, Value
from packet_consumer import Packet_Consumer
from sniffer import IPSniff
from ctypes import c_bool
import sys

output = sys.argv[1]

queue = Queue()
terminate_value = Value( c_bool , False , lock=False )

sniff_process = IPSniff( "wlan0" , queue, terminate_value )
consumer_process = Packet_Consumer( queue , output , terminate_value)

sniff_process.start()
consumer_process.start()

print( terminate_value )
while True:
	msg = input("Terminate? y/n \n")
	if msg == "y":
		print("Setting terminate_value to True" )
		terminate_value.value = True
		print( terminate_value )
		break
