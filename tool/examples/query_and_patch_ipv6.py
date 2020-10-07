from scapy.all import *
import random
import sys
from ipaddress import _BaseV6

#1) change any app/transport layer, ip layer
#2) recalculate transport layer checksum then recalculate ip checksum
def patch(dns_frame: bytearray, pseudo_hdr: bytearray, dns_id: int):
    """Adjust the DNS id and patch the UDP checksum within the given Ethernet frame"""
    #change source ipv6 22-37 inclusive
    #change destination ipv6 = 38-53 inclusive
    #destination = _BaseV6._ip_int_from_string( "2620:fe::9" ).to_bytes( 16 , "big")
    #dns_frame[38:54] = destination
    #pseudo_hdr[16:32] = destination

    # set dns id
    # the byte offsets can be found in Wireshark
    dns_frame[62] = (dns_id >> 8) & 0xFF
    dns_frame[63] = dns_id & 0xFF

    # reset checksum
    dns_frame[60] = 0x00
    dns_frame[61] = 0x00

    # calc new tcp/udp checksum
    ck = checksum(pseudo_hdr + dns_frame[54:] )
    if ck == 0:
        ck = 0xFFFF
    cs = struct.pack("!H", ck)
    dns_frame[60] = cs[0]
    dns_frame[61] = cs[1]

def patch_domain( dns_frame , psuedo_hdr , domain ):
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

	for byte in psuedo_hdr:
		print( hex(byte) + " " ,end="")
	print()

	#fix length of udp headers and app data
	psuedo_hdr[34:36] = dns_frame[18:20]

	for byte in psuedo_hdr:
		print( hex(byte) + " " ,end="")
	print()

	return dns_frame , psuedo_hdr

server = sys.argv[1]
site1 = sys.argv[2]
n_packets = int(sys.argv[3])

ether=Ether()
ip = IPv6(dst=server)
udp = UDP(dport=53,sport=53)
dns = DNS( cd=1 ,  ad=1 ,  rd=1 ,
        qd=DNSQR(qtype=255 , qname=site1 ) ,  ar=DNSRROPT() )

response = ether/ip/udp/dns
dns_frame = bytearray( raw(response) )

#udp is [54:] to rest (including data)
psuedo_hdr = bytearray(
                        dns_frame[22:38] + #ip.src
                        dns_frame[38:54] + #ip.dst
                        bytes([0,dns_frame[20]]) + #bytes([0]) + raw(response[IPv6].nh) +   #wireshark has next header( protocol) as just byte 20
                        dns_frame[58:60]   #length of udp headers and app data (should i exclude checksum? )
                      )

#x = 0
#for byte in pseudo_hdr:
#   print( str(x)+") "+ str(hex(byte)) )
#   x+=1
#exit(1)
s = conf.L2socket()
s.send( dns_frame )
print( Ether(dns_frame).show(dump=True) )

start_time = time.time()
domains = [ site1 , "isc.org" , "amazon.com" ]
for domain in domains:
    patch(dns_frame, psuedo_hdr, (1024) % 65535)
    s.send(dns_frame)
    dns_frame , psuedo_hdr = patch_domain( dns_frame , psuedo_hdr , domains[1] )
    patch( dns_frame, psuedo_hdr , 1025)
    s.send( dns_frame )
    break
    #print( Ether(dns_frame).show(dump=True) )

end_time = time.time()
print(f"sent {n_packets} responses in {end_time - start_time:.3f} seconds")
