from ipaddress import _BaseV6 , _BaseV4

def convert_IPv4_to_bytes( ip_string ):
	return _BaseV4._ip_int_from_string( ip_string ).to_bytes( 4 , "big")

def convert_IPv6_to_bytes( ip_string):
	return _BaseV6._ip_int_from_string( ip_string ).to_bytes( 16 , "big")

def is_v4( ip ):
	if "." in ip:
		return True
	return False

#better to iterate backwards and just remove from original list and plop into new list..... no need to create copies
def seperate_v4_v6( list_ips ):
	ipv4 = []
	ipv6 = []

	for ip in list_ips:
		v4 = is_v4( ip )
		if v4:
			ipv4.append( ip )
		else:
			ipv6.append( ip )

	return ( ipv4 , ipv6 )

def convert_addr_to_bytes( string , version ):
	if version == 4:
		return convert_IPv4_to_bytes( string )
	else:
		return convert_IPv6_to_bytes( string )

def convert_addresses_to_bytes( addresses , version ):
	for x in range( len(addresses) ):
		addresses[x] = convert_addr_to_bytes( addresses[x] , version )

if __name__ == "__main__":
	import sys
	if len( sys.argv) < 2:
		print( "Give a list of ipv4 and ipv6 addresses to test" )
		exit(1)

	list = open( sys.argv[1] , "r" ).read().splitlines()
	v4 , v6 = seperate_v4_v6( list )
	print( "Separated lists: \nIPv4:")
	print( v4 )
	print( "IPv6: ")
	print( v6 )

	convert_addresses_to_bytes( v4 , 4 )
	convert_addresses_to_bytes( v6 , 6 )
	#for x in range( len(v4) ):
	#	v4[x] = convert_IPv4_to_bytes( v4[x] ).hex()
	#for x in range( len(v6) ):
	#	v6[x] = convert_IPv6_to_bytes( v6[x] ).hex()

	print( "IPv4 as bytes:" )
	print( v4 )
	print( "IPv6 as bytes:" )
	print( v6 )
