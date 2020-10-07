from scapy.all import *
import random
import sys
#change ip length (16,17) , UDP length ( 38, 39 ) , in dns layer - 54(length of name) followed by the name, followed by null byte, then concat rest of bytes
#also change the . in .com to 0x03
def patch_domain( dns_frame , psuedo_hdr , domain ):
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


#1) change any app/transport layer, ip layer
#2) recalculate transport layer checksum then recalculate ip checksum
def patch(dns_frame: bytearray, pseudo_hdr: bytearray, dns_id: int , ):#destination: bytes):
    """Adjust the DNS id and patch the UDP checksum within the given Ethernet frame"""
    #change source ip
    #dns_frame[26]=192
    #dns_frame[27]=168
    #dns_frame[28]=0
    #dns_frame[29]=7

    #pseudo_hdr[0] = 192
    #pseudo_hdr[1] = 168
    #pseudo_hdr[2] = 0
    #pseudo_hdr[3] = 7
    #dns_frame[30:34] = destination
    #pseudo_hdr[4:8] = destination

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

server = sys.argv[1]
site1 = sys.argv[2]


ether=Ether()
ip = IP( dst=server)
udp = UDP(dport=53,sport=53)
dns = DNS( cd=1 ,  ad=1 ,  rd=1 ,
        qd=DNSQR(qtype=255 , qname=site1 ) ,  ar=DNSRROPT() )

response = ether/ip/udp/dns
print( response.show(dump=True) )
dns_frame = bytearray(raw(response))

pseudo_hdr = ( dns_frame[26:30] + #ip src
			dns_frame[30:34] + #ip dst
			bytes([0]) + #one byte of zeroes
			bytes([dns_frame[23]]) + #the upper layer protocol
			len( dns_frame[34:] ).to_bytes( 2 , byteorder="big") #udp length
	     )

s = conf.L2socket()

start_time = time.time()
domains = [ site1 , "facebook.com" , "bing.com" , "google.com" ]
for domain in domains:
    dns_frame , pseudo_hdr = patch_domain( dns_frame , pseudo_hdr , domain )
    patch(dns_frame, pseudo_hdr, (1024 + 0) % 65535 , )
    s.send( dns_frame )
end_time = time.time()

