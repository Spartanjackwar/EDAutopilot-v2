# An script example
from gameui import Logger, ScriptSession 
from scripts.ScriptBase import ScriptBase
from utils.utils import *
from utils.image import Image
from PySide2.QtWidgets import QGridLayout, QVBoxLayout, QLabel, QPushButton, QGroupBox # import widgets you want to add to 'Script' box here

class stateMachine(object):
	pass #filled by later code.

class example(ScriptBase): # class name must be same with filename
	def __init__(self,logger:Logger=None,layout:QGridLayout=None,session:ScriptSession=None,templates:Image=None): 
		super().__init__(logger,layout,session,templates)
		# Initialize scripts and layout here

		### Example groupbox_1
		groupbox_1 = QGroupBox('Description')
		label1 = QLabel('Example')
		layout_1 = QVBoxLayout()
		layout_1.addWidget(label1)
		groupbox_1.setLayout(layout_1)

		### Example groupbox_2
		groupbox_2 = QGroupBox('Controls')
		button1 = QPushButton('test')
		layout_2 = QVBoxLayout()
		layout_2.addWidget(button1)
		groupbox_2.setLayout(layout_2)

		self.layout.addWidget(groupbox_1,0,0,-1,1)
		self.layout.addWidget(groupbox_2,0,1,-1,1)
		button1.pressed.connect(self._onClickButton) # you can connect signals

		#Machine setup:
		self.progress = stateMachine()
		self.machine = transitions.Machine(model=self.progress, states=self.states, initial=self.initialState)

		self.logger.info('example: __init__ is loaded')

	states = [
		'Initial',
		
		#Route planning.
		'FindingNextRouteSystem',
		'BuyingNextRouteItems',
		
		#Leaving dock
		'Undock',
		'LeaveMassLock',
		'JumpAlign',
		'Jump',
		
		#Flying to next dock.
		'Supercruise-up',
		'Supercruise-findRouteTarget', #Target with SCAssist
		'Supercruise-align',
		'Arrival',
		'RequestDocking',
		'Dock',
		
		#Finish route
		'BuyFuel',
		'SellItems',
		
		'Finished'
	]
	
	def onChangeStatus(self, status:str):
		self.machine.set_state(status)

	
	def run(self): # Program entrance, you can use infinite loop or anything here
		align = False
		
		elapsedTime = datetime.now()-startTime
		while not keyboard.is_pressed('end'):
			if keyboard.is_pressed('o'): 
				align = True
			if align: 
				align = session.align()
			session.sleep(0.01)
	
	
	def _onClickButton(self):
		self.logger.info('clicked')
	
	
	def State_LeaveMassLock(self):
		if 'FSDMassLocked' in session.stateList:
			self.session.sendKey('ThrustUp',hold=3)
			self.session.sendKey('SpeedZero')
			self.session.sleep(1)
		else:
			self.machine.set_state('JumpAlign')
	
	
	#Star avoidance state.
	def State_SC_Up(self):
		pitchUpTime = 18
		speedDelay = 20
		self.session.sunAvoiding(speedDelay, pitchUpTime)
		self.machine.set_state('Supercruise-findRouteTarget')
	
	
	#Destination target state.
	def State_SC_FindRouteTarget(self, targetName:str):
		#TODO: Get target
		self.machine.set_state('Supercruise-align')
	
	
	#Align to destination.
	def State_SC_Align(self):
		if self.session.align():
			#TODO: Check arrived.
			self.machine.set_state('Arrival')
	
	
	
	
	