from scapy.all import Ether , IP , IPv6 , UDP , DNS, DNSQR
from multiprocessing import Process , Queue , Value
import time

class Packet_Consumer( Process ):

	def __init__( self , queue , min_pkt_size , terminate_value ):
		super().__init__()
		self.queue = queue
		self.min_pkt_size = min_pkt_size
		self.file = open( "scan_results" , "w" )
		self.terminate_value = terminate_value

	#might want to make this filter only for packets received for my ip or mac
	def run( self ):
		while True:
			raw_packet = self.queue.get( block=True )
			
			if raw_packet == "finished":
				print("Finished processing packets")
				break
				
			try:        		#this filters for unfragmented DNS responses      #this filters for fragmented DNS responses
				packet = Ether( raw_packet )


				if packet.haslayer( IPv6 ):
					ip_v = IPv6
				else:
					ip_v = IP
				
				if (packet.haslayer(DNS) and packet[DNS].qr == 1) or ( packet.haslayer(UDP) and ( packet[UDP].dport == 53  and packet[ip_v].flags == 1 )):
					if packet[UDP].len >= self.min_pkt_size and packet.haslayer( DNSQR ):
						print( "Received response:  writing to scan_results" )
						self.file.write( packet[ip_v].src + "\t" + packet[DNSQR].qname.decode("ascii").rstrip(".") +"\t" + str(packet[UDP].len ) + "\n")
						self.file.flush()
			except Exception as e:
				print( "Exception in Sniffer: " + str(e) )

		self.file.close()
