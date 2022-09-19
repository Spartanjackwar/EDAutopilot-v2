import time
import cv2
import numpy as np
from datetime import datetime
from PySide2.QtCore import QThread
from dataclasses import dataclass
from collections import Counter
from utils.utils import sendHexKey,getKeys,Journal,ALIGN_DEAD_ZONE,ALIGN_KEY_DELAY,ALIGN_TRIMM_DELAY
from utils.keybinds import typewrite
from utils.image import Screen, Image
@dataclass
class ScriptInputMsg:
	isAligned: bool
	isFocused: bool
	stateList: list
	journal: Journal
	guiFocus: str
	offsetX: int
	offsetY: int
	windowLeftX: int
	windowTopY: int
class routeWorker(QThread):
	def __init__(self) -> None:
		super().__init__()
class ScriptSession: # will be initialized in ScriptThread
	# _inSignal = Signal(object)
	# _outSignal = Signal(object)
	version = ''
	offsetX = offsetY = 0
	isAligned = isFocused = False
	stateList = []
	journal = []
	missions = []
	guiFocus = 'NoFocus'
	status = ''
	shipLoc = ''
	shipTarget = ''
	windowCoord = (0,0)
	def __init__(self,logger=None,keysDict:dict=None,image:Image=None,screen:Screen=None) -> None:
		self.logger = logger
		self.keysDict = keysDict
		self.image = image
		self.screen = screen
	def _update(self,data:ScriptInputMsg) -> None:
		self.isAligned = data.isAligned
		self.isFocused = data.isFocused
		self.stateList = data.stateList
		self.journal = data.journal
		self.guiFocus = data.guiFocus
		self.offsetX = data.offsetX
		self.offsetY = data.offsetY
		self.windowCoord = (data.windowLeftX,data.windowTopY)
		self.status = self.journal.status
		self.shipLoc = self.journal.nav.location
		self.shipTarget = self.journal.nav.target
		self.version = self.journal.log.version
		self.missions = self.journal.missions
	def sendKey(self, key:str, hold:float=None, repeat:int=1, repeat_delay:float=None, state=None, sleep:float=None) -> None:
		"""
		@param sleep: the seconds you want to sleep after the given key is pressed
		"""
		sendHexKey(self.keysDict,key,hold=hold,repeat=repeat,repeat_delay=repeat_delay,state=state)
		if sleep: self.sleep(sleep)
	def sleep(self,delay:float) -> None:
		time.sleep(delay)
	detectionLossTimer = 0
	alignedTimer = 0
	def align(self) -> bool :
		quitAlign = False
		while not quitAlign:
			if self.isAligned:
				if self.alignedTimer==0: self.alignedTimer = int(datetime.utcnow().timestamp())
				elif int(datetime.utcnow().timestamp())-self.alignedTimer>=2: quitAlign = True
			elif self.alignedTimer!=0: self.alignedTimer = 0
			offsetX, offsetY = self.offsetX, self.offsetY
			if offsetX == offsetY == 0:
				if self.detectionLossTimer == 0: self.detectionLossTimer = int(datetime.utcnow().timestamp())
				else: 
					nowTime = int(datetime.utcnow().timestamp())
					if nowTime - self.detectionLossTimer >= 5: # loss for over than 5 seconds, applying random jitter
						self.sunAvoiding()
			else: 
				if self.detectionLossTimer != 0: self.detectionLossTimer = 0
				trimX = trimY = 0.0
				absX, absY = abs(offsetX), abs(offsetY)
				if absX<3: trimX = ALIGN_TRIMM_DELAY
				if absY<3: trimY = ALIGN_TRIMM_DELAY
				if absY>ALIGN_DEAD_ZONE: # align Y-Axis first
					if offsetY<0: self.sendKey('PitchUpButton',hold=ALIGN_KEY_DELAY-trimY)
					else: self.sendKey('PitchDownButton',hold=ALIGN_KEY_DELAY-trimY)
				elif absX>ALIGN_DEAD_ZONE: 
					# if absX>ROLL_YAW_DEAD_ZONE:
					#     if offsetX>0: self.sendKey('RollRightButton' if offsetY<0 else 'RollLeftButton',hold=0.1)
					#     else: self.sendKey('RollLeftButton' if offsetY<0 else 'RollRightButton',hold=0.1)
					# else:
					if offsetX>0: self.sendKey('YawRightButton',hold=ALIGN_KEY_DELAY-trimX)
					else : self.sendKey('YawLeftButton',hold=ALIGN_KEY_DELAY-trimX)
		self.detectionLossTimer = 0
		self.alignedTimer = 0
		return False
	def sunAvoiding(self,fwdDelay=18,turnDelay=12):
		self.sendKey('SpeedZero')
		self.sleep(2)
		self.sendKey('PitchUpButton',hold=turnDelay)
		self.sendKey('Speed100')
		self.sleep(fwdDelay)
		self.sendKey('SpeedZero')
	## Navigation
	def getRouteFromTo(self,start:str,to:str) -> list:
		pass
	def setRoute(self,dest:str) -> bool:
		pass
	def startRoute(self) -> bool: # start a new RouteAssist thread (using statemachine for multi-star route)
		pass
	def jump(self,estimatedTarget:str=None) -> bool: # if current target != estimated target then the jumping won't be performed
		pass
	def isEnRoute(self) -> bool:
		pass
	def stopRoute(self,force:bool=False) -> bool:
		pass
	def getRouteDetails(self) -> dict:
		pass
	def setTargetSystem(self,target:str) -> bool:
		if self.version == 'Odyssey': # Odyssey version
			self.sendKey('UI_Back',repeat=3,sleep=2)
			self.sendKey('UI_OpenGalaxyMap',sleep=3)
			if self.guiFocus == 'GalaxyMap':
				self.sendKey('UI_Up_Alt',sleep=1)
				self.sendKey('UI_Select')
				typewrite(target)
				self.sleep(2)
				self.sendKey('UI_Down_Alt',sleep=1)
				self.sendKey('UI_Select')
				self.sleep(7) # waiting to move to the target
				self.sendKey('UI_Right_Alt')
				self.sendKey('UI_Down_Alt',repeat=6)
				self.sendKey('UI_Select',sleep=3)
				self.sendKey('UI_Back',repeat=2)
				return True
		elif self.version == 'Horizons': # Horizons version
			self.sendKey('UI_Back',repeat=3,sleep=2)
			self.sendKey('UI_OpenGalaxyMap',sleep=3)
			if self.guiFocus == 'GalaxyMap':
				self.sendKey('UI_Select',sleep=1)
				self.sendKey('UI_NextTab',sleep=1)
				self.sendKey('UI_Select',sleep=1)
				typewrite(target)
				self.sendKey('enter')
				self.sleep(7) # waiting to move to the target
				self.sendKey('UI_Right_Alt')
				self.sendKey('UI_Select')
				self.sleep(2)
				self.sendKey('UI_Back')
				return True
		return False
	
	
	#Function to attempt to figure out if a given target name is in the list.
	def findNavTarget(self, targetName:str, useSCAssist:bool, navListSearchLimit:int = 30) -> bool:
		#Go back to the main panel before we start.
		if self.guiFocus != 'NoFocus':
			self.sendKey('esc')
			self.sleep(1)
		
		#Go to the left panel and find the nav page.
		if self.guiFocus != 'Panel_1':
			self.sendKey('UI_1')
			self.sleep(1)
		
		#Attempt to navigate the list of navigation targets.
		for i in range(navListSearchLimit):
			#Select each item to figure out what it is.
			self.sendKey('UI_Down')
			self.sendKey('UI_Select')
			self.sleep(0.1)
			
			self.logger.debug(self.shipTarget)
			
			if targetName in self.shipTarget:
				#Select supercruise assist if desired.
				if useSCAssist:
					self.sendKey('UI_Right')
					self.sendKey('UI_Select')
				else:
					self.sendKey('UI_Select')
				#We found the target!
				return True
		
		#Catch total miss as false.
		return False
	
	
	def clearRoute(self,target:str=None) -> bool: # For Horizons,we need to know the exact target to clear it
		if self.version == 'Odyssey': # Odyssey version
			self.sendKey('UI_Back',repeat=3,sleep=2)
			self.sendKey('UI_OpenGalaxyMap',sleep=3)
			if self.guiFocus == 'GalaxyMap':
				self.sendKey('UI_Left_Alt',sleep=1)
				self.sendKey('UI_Down_Alt',repeat=13,sleep=1) # to the bottom
				self.sendKey('UI_Up_Alt',repeat=2,sleep=1) # select route settings
				self.sendKey('UI_Select',sleep=1)
				self.sendKey('UI_Up_Alt',repeat=4,sleep=1) # to the top
				self.sendKey('UI_Down_Alt')
				# WIP
				return True
		elif self.version == 'Horizons' and target: # Horizons version, which needs a 'target' input
			pass
		return False
	## PIP Managements
	def pipReset(self):
		self.sendKey('PipDown')
	def pipSet(self,system,engine,weapon) -> bool:
		"""
		patterns: 

		4-2-0 (4 twice, 2 once, 4 once)

		4-1-1 (4 twice)

		3-0-3 (each 3 twice)

		3-1.5-1.5 (3 once)

		3.5-2-0.5 (3.5 twice, 2 once)

		2.5-2.5-1 (each 2.5 press once)

		"""
		if engine+system+weapon!=6 : return False # Illegal argument
		self.pipReset()
		pipDict = {"PipLeft": system, "PipUp": engine, "PipRight": weapon}
		c = Counter(pipDict.values())
		if c == Counter([4,2,0]): # pattern 1
			key_4 = getKeys(pipDict,4)[0] # key that need to be clicked 3 times
			self.sendKey(key_4,repeat=2)
			self.sendKey(getKeys(pipDict,2)[0])
			self.sendKey(key_4)
		elif c == Counter([4,1,1]): # pattern 2
			self.sendKey(getKeys(pipDict,4)[0],repeat=2)
		elif c == Counter([3,0,3]): # pattern 3
			for key in getKeys(pipDict,3): self.sendKey(key,repeat=2)
		elif c == Counter([3,1.5,1.5]): # pattern 4
			self.sendKey(getKeys(pipDict,3)[0])
		elif c == Counter([3.5,2,0.5]): # pattern 5
			self.sendKey(getKeys(pipDict,3.5)[0],repeat=2)
			self.sendKey(getKeys(pipDict,2)[0])
		elif c == Counter([2.5,2.5,1]): # pattern 6
			for key in getKeys(pipDict,2.5): self.sendKey(key)
		else: return False
		return True
	
	def screenCapture(self,imageName:str=None,grayscale:bool=False) -> cv2.Mat:
		img = self.screen.screenshot(grayscale=grayscale)
		if imageName is not None: cv2.imwrite(imageName,img)
		return img