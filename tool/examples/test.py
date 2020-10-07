import sys
sys.path.append( "./Amplifier" )
from Amplifier.Argument_Processor import Argument_Processor

args_proc = Argument_Processor()
args_proc.get_starter_pack( "~/Desktop" )
