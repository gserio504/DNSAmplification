
import sys
from PyQt5.QtWidgets import * #QLabel , QFileDialog , QApplication, QMainWindow , QWidget , QVBoxLayout, QPushButton, QFrame, QLayout, QGraphicsScene , QGraphicsView
from PyQt5.QtGui import QIcon, QImage, QPalette, QBrush
from PyQt5.QtCore import Qt , QSize




def set_background(widget , path, fit=False , window_size=None):
        palet = widget.palette()
        image = QImage( path )
        if fit == True:
                image = image.scaled( QSize(window_size[0] , window_size[1]) , aspectRatioMode=Qt.KeepAspectRatio )
        palet.setBrush( QPalette.Window , QBrush(image) )
        widget.setPalette( palet )



class App(QGraphicsView):

    def __init__(self,controller):
        super().__init__()
        self.controller = controller
        self.controller.set_view( self )
        self.title = 'PyQt5 simple window - pythonspot.com'
        self.left = 0
        self.top = 0
        self.width = 640
        self.height = 480
        self.initUI()

    def getOnMousePressed(self):
    	def mousePressEvent(event):
    		print("hi_1")
    		self.get_dir()
    	return mousePressEvent

    def valueChanged(self):
    	self.thread_label.setText( str(self.slider.value()) )


    def initUI(self):
        self.slider = QSlider( Qt.Horizontal )
        self.slider.setMinimum( 1 )
        self.slider.setMaximum( 8 )
        self.slider.setValue( 1 )
        self.slider.valueChanged.connect( self.valueChanged ) 
        self.slider.setGeometry( 200 , 0 , 200 , 100 )
        self.slider.setTickInterval( 1 )
        self.slider.setTickPosition( QSlider.TicksBothSides )

        self.text_box = QTextEdit()
        self.text_box.setGeometry( 0 , 150 , 400 , 50 )

        self.thread_label = QLabel( str(self.slider.value()) )
        self.thread_label.setGeometry( 275 , 100 , 50 , 50 )
        self.thread_label.setAlignment( Qt.AlignHCenter | Qt.AlignVCenter )

        button = QPushButton("rawr")
        button.setGeometry( 0 , 0 , 100 , 100 )
        button.mousePressEvent = self.getOnMousePressed()
        scene = QGraphicsScene()
        scene.addWidget( button )
        scene.addWidget(self.text_box)
        scene.addWidget( self.slider )
        scene.addWidget( self.thread_label )
        self.setScene( scene )
        self.show()

    def get_dir(self):
    	print( "hi_2!")
    	dir = QFileDialog.getExistingDirectory(self, "Open Directory",
                                       "/home",
                                       QFileDialog.ShowDirsOnly
                                       | QFileDialog.DontResolveSymlinks)
    	self.text_box.setText( dir )

    #def mousePressEvent(self, event):
        #print( self.sender() )
class Controller:
	def __init__(self):
		self.view = None
		self.scenes = {}

	def add_scene(self, scene, name ):
		self.scenes[name] = scene

	def set_view(self, view):
		self.view = view

	def option_clicked( self , option ):
		print( option )
		if option=="1":
			self.change_scene( "scan" )

	def change_scene( self , option ):
		self.view.setScene( self.scenes.get(option) )

if __name__ == '__main__':
    controller = Controller()
    app = QApplication(sys.argv)
    ex = App(controller)
    sys.exit(app.exec_())
