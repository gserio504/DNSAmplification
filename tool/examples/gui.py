import sys
from PyQt5.QtWidgets import QApplication, QMainWindow , QPushButton , QLayout , QWidget
from PyQt5.QtGui import QBitmap ,  QImage , QPalette, QBrush
from PyQt5.QtCore import Qt , QSize
import time

def set_background( window , path, fit=False , window_size=None):
	palet = window.palette()
	image = QImage( path )
	if fit == True:
		image = image.scaled( QSize(window_size[0] , window_size[1]) , aspectRatioMode=Qt.KeepAspectRatio )
	palet.setBrush( QPalette.Window , QBrush(image) )
	window.setPalette( palet )

def do_stuff(event):
	print( "wow" )
	global state1
	global state2
	global current_state
	global window
	if current_state == 2:
		window.restoreState( state1 )
	else:
		window.restoreState( state2 )
	window.show()
background_img = sys.argv[1]
background_img2 = sys.argv[2]
global current_state
current_state = 2
window_size = ( 500 , 500 )

app = QApplication(sys.argv)
global window
window = QWidget()
window.mousePressEvent=do_stuff
window.setGeometry( 0 , 0 , window_size[0] , window_size[1] )
set_background( window , background_img , fit=True , window_size=window_size )
global state1
state1 =  window.saveState()
set_background( window , background_img2 , fit=True, window_size=window_size )
global state2
state2 = window.saveState()
window.show()
button = QPushButton()
button.height=10
button.width=10
window.addWidget( button )

sys.exit(app.exec_())
