
import sys
from PyQt5.QtWidgets import * #QLabel , QFileDialog , QApplication, QMainWindow , QWidget , QVBoxLayout, QPushButton, QFrame, QLayout, QGraphicsScene , QGraphicsView
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import time
from multiprocessing import Value, Process
from ctypes import c_long



def set_background(widget , path, fit=False , window_size=None):
        palet = widget.palette()
        image = QImage( path )
        if fit == True:
                image = image.scaled( QSize(window_size[0] , window_size[1]) , aspectRatioMode=Qt.KeepAspectRatio )
        palet.setBrush( QPalette.Window , QBrush(image) )
        widget.setPalette( palet )

class PacketCounter(QObject):

	finished = pyqtSignal()
	value_signal = pyqtSignal(int)

	def __init__( self , packet_value ):
		super().__init__()
		self.packet_value = packet_value

	@pyqtSlot()
	def counting(self):
		print( "started qthread" )
		last_value = self.packet_value.value
		while self.packet_value.value <= 100:
			if self.packet_value.value != last_value:
				self.value_signal.emit( self.packet_value.value )
				last_value = self.packet_value.value
			time.sleep( .5 )
		print( "finished reading values in qthread" )
		self.finished.emit()

def count_method( value ):
    for x in range( 1 , 101 ):
        value.value += 1
        if x % 10 == 0:
            print( "Current val: "+ str(value.value) )
        time.sleep( 1 )


class App(QGraphicsView):

    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 simple window - pythonspot.com'
        self.left = 0
        self.top = 0
        self.width = 640
        self.height = 480
        self.initUI()

    def incremented( self, count ):
        print( "Received count in incremented function: " + str(count) )
        self.my_label.setText( str(count) )

    def clean(self):
        self.count_process.terminate()

    def initUI(self):
        self.my_label = QLabel("0")
        self.my_label.setGeometry( 100 , 100 , 100 , 100 )
        self.my_label.setParent( self ) 

        self.show()
        count = Value( c_long , 0 )
        self.count_process = Process( target=count_method , args=(count,) )
        self.packet_counter = PacketCounter( count )
        self.qthread = QThread()

        self.packet_counter.moveToThread( self.qthread )

        self.qthread.started.connect( self.packet_counter.counting )
        self.packet_counter.value_signal.connect( self.incremented )
        self.packet_counter.finished.connect( self.qthread.quit )

        self.qthread.start()
        self.count_process.start()
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    app.exec_()
    ex.clean()
    #sys.exit(app.exec_())
