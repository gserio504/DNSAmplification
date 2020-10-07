
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow , QWidget , QVBoxLayout, QPushButton, QFrame, QLayout, QGraphicsScene , QGraphicsView
from PyQt5.QtGui import QIcon, QImage, QPalette, QBrush
from PyQt5.QtCore import Qt , QSize




def set_background(widget , path, fit=False , window_size=None):
        palet = widget.palette()
        image = QImage( path )
        if fit == True:
                image = image.scaled( QSize(window_size[0] , window_size[1]) , aspectRatioMode=Qt.KeepAspectRatio )
        palet.setBrush( QPalette.Window , QBrush(image) )
        widget.setPalette( palet )

class OptionsScene(QGraphicsScene):

	def __init__(self,controller):
		super().__init__()
		self.controller = controller
		self.initUI()

	def getOnMousePressed( self , widget , option ):
		def mousePressEvent( event ):
			print("wow")
			self.controller.option_clicked( option )
		return mousePressEvent

	def initUI(self):
		widgets = [QWidget() for i in range(3)]
		print( widgets )
		x = 1
		for widget in widgets:
			widget.setGeometry( (x - 1 )*200 , 0 , 200 , 400 )
			set_background( widget , "/home/emogrrlxx/Desktop/gui/"+str(x)+".png" , fit=False , window_size=(200,400) )
			self.addWidget( widget )
			x += 1
		widgets[0].mousePressEvent = self.getOnMousePressed( widgets[0] , "1")
		widgets[1].mousePressEvent = self.getOnMousePressed( widgets[1] , "2")
		widgets[2].mousePressEvent = self.getOnMousePressed( widgets[2] , "3")


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
        self.initScenes()
        self.initUI()


    def initScenes(self):
        scan_scene = QGraphicsScene()
        widg = QWidget()
        widg.setGeometry( 0 , 0 , 400 , 400 )
        set_background( widg , "/home/emogrrlxx/Desktop/me.jpg" )
        scan_scene.addWidget( widg )
        self.controller.add_scene( scan_scene , "scan" )

    def initUI(self):
        self.scene = OptionsScene(self.controller)
        self.setScene( self.scene )
        self.show()

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
    background_img = sys.argv[1]
    controller = Controller()
    app = QApplication(sys.argv)
    ex = App(controller)
    sys.exit(app.exec_())
