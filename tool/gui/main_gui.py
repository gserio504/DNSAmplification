import sys
from PyQt5.QtWidgets import * #QApplication, QMainWindow , QWidget , QVBoxLayout, QPushButton, QFrame, QLayout, QGraphicsScene , QGraphicsView
from PyQt5.QtGui import * #QIcon, QImage, QPalette, QBrush
from PyQt5.QtCore import *  #Qt , QSize
from MenuScene import MenuScene
from StarterScene import StarterScene


def set_background(widget , path, fit=False , window_size=None):
	palet = widget.palette()
	image = QImage( path )
	if fit == True:
		image = image.scaled( QSize(window_size[0] , window_size[1]) , aspectRatioMode=Qt.KeepAspectRatio )
	palet.setBrush( QPalette.Window , QBrush(image) )
	widget.setPalette( palet )

class App(QGraphicsView):

	def __init__(self):
		super().__init__()
		self.title = 'PyQt5 simple window - pythonspot.com'
		self.left = 0
		self.top = 0
		self.width = 640
		self.height = 480
		self.setSizePolicy( QSizePolicy.Maximum , QSizePolicy.Maximum )
		self.initUI()

	def sceneChange( self , scene ):
		def func(rawr):
			self.setScene( scene )
			self.setFixedSize(  int(scene.width() + 2) , int(scene.height() + 2) ) #resizes window the scene size (+2 needed or else the window has 1 pixel of scrollable area)
		return func

	def initMenuScene(self):
		self.menu_scene.button_map[ "Get Starter Pack" ].clicked.connect( self.sceneChange( self.starter_pack_scene ) )

	def initStarterPackScene(self):
		self.starter_pack_scene.back_button.clicked.connect( self.sceneChange( self.menu_scene) )

	def initScenes(self):
		self.menu_scene = MenuScene()
		self.starter_pack_scene = StarterScene()

		self.initMenuScene()
		self.initStarterPackScene()

	def initUI(self):
		self.initScenes()
		self.setFixedSize(  int(self.menu_scene.width() + 2) , int(self.menu_scene.height() + 2) )
		self.setScene( self.menu_scene )
		self.show()


if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = App()
	sys.exit(app.exec_())
