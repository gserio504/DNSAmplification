from PyQt5.QtWidgets import QGraphicsScene , QPushButton

class MenuScene(QGraphicsScene):

	def __init__(self):
		super().__init__()
		self.button_map = {}
		self.initUI()

	def initUI(self):
		self.option_buttons = [QPushButton() for i in range(3) ]
		button_texts = [ "Get Starter Pack" , "Scan" , "Flood" ]
		for x in range( len(self.option_buttons) ):
			button = self.option_buttons[x]
			button.setText( button_texts[x] )
			button.setGeometry( 0 , x*100 , 200 , 100 )
			self.addWidget( button )
			self.button_map[ button.text() ] = button