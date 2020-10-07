from PyQt5.QtCore import QObject , QThread , pyqtSignal , pyqtSlot
from PyQt5.QtWidgets import QGraphicsScene , QFileDialog , QPushButton , QTextEdit , QLabel
import os
import sys
import time
from threading import Thread , Semaphore
sys.path.append( ".." )
sys.path.append( os.path.realpath("../Amplifier") )
from Amplifier.Argument_Processor import Argument_Processor


#runs in a QThread to check the status of downloading the starter pack with Arguments_Processor
class Status_Checker(QObject):

	changed = pyqtSignal(str)
	finished = pyqtSignal()

	def __init__( self , status , producer_thread , semaphore):
		super().__init__()
		self.status = status
		self.producer_thread = producer_thread
		self.semmy = semaphore

	@pyqtSlot()
	def check(self):
		self.semmy.acquire()#block until the producer thread starts
		last_status = self.status.value

		while self.producer_thread.is_alive():
			if self.status.value != last_status:
				last_status = self.status.value
				self.changed.emit( last_status.decode("ascii") )
			time.sleep( .2 )

		self.changed.emit("Finished\n---------------------------------------")
		self.finished.emit()

class StarterScene(QGraphicsScene):

	def __init__(self):
		super().__init__()
		self.args_proc = Argument_Processor()
		self.initUI()

	def locate_dir(self):
		dir = QFileDialog.getExistingDirectory( None , "Open Directory", "/home", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
		self.text_box.setText( dir )

	def enable_buttons(self):
		self.download_button.setDisabled(False)
		self.push_button.setDisabled(False)
		self.text_box.setDisabled(False)

		#self.download_button.clicked.connect( self.status_text.clear )
		self.download_button.clicked.connect( self.get_starter_pack )

		self.push_button.clicked.connect( self.locate_dir  )

	def disable_buttons(self):
		self.download_button.setEnabled(False)
		self.push_button.setEnabled(False)
		self.text_box.setEnabled(False)

		self.download_button.disconnect()
		self.push_button.disconnect()

	def get_starter_pack(self):
		self.disable_buttons()
		
		self.status_thread = QThread()
		self.retriever_thread = Thread( target=self.args_proc.get_starter_pack , args=(self.text_box.toPlainText(),)) #the thread that actually does thw rok
		semmy = Semaphore( value = 0 )

		#for some reason not making the status checker an instance variable causes the  qthread to randomly not start.
		self.status_checker = Status_Checker( self.args_proc.start_pack_status , self.retriever_thread , semmy)
		self.status_checker.moveToThread( self.status_thread )

		self.status_thread.started.connect( self.status_checker.check )

		self.status_checker.changed.connect( self.status_text.append )
		self.status_checker.finished.connect( self.status_thread.quit )
		self.status_checker.finished.connect( self.enable_buttons )

		self.status_thread.start()
		self.retriever_thread.start()
		semmy.release() #allow status checking thread to start since producer( retriever ) started


	def initUI(self):
		self.directions_label = QLabel("Choose a directory to save the starter pack and click \"Download\"" )
		self.text_box = QTextEdit("rawr :3 mew mew")
		self.status_text = QTextEdit("")
		self.push_button = QPushButton("Choose Directory")
		self.download_button = QPushButton("Download")
		self.back_button = QPushButton( "Back" )

		self.directions_label.move( 0 , 100 )
		self.text_box.setGeometry( 0 , 150 , 400 , 25 )
		self.push_button.setGeometry( 400 , 150 , 200 , 25 )
		self.download_button.setGeometry( 400 , 175  , 200 , 25 )
		self.back_button.setGeometry( 400 , 200 , 200 , 25 )
		self.status_text.setGeometry( 0 , 225 , 600 , 200 )

		self.enable_buttons() #connect their signals to shit

		#extraneous shit
		#self.status_text.setReadOnly(True)

		self.addWidget( self.directions_label )
		self.addWidget( self.text_box )
		self.addWidget( self.push_button )
		self.addWidget( self.download_button )
		self.addWidget( self.back_button )
		self.addWidget( self.status_text )