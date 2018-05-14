# -*- coding: utf-8 -*-

"""
/***************************************************************************
 SMARTGREEN
 A QGIS plugin to support water managers in the process
 of building and simulating different land uses scenarios and LIDs planning.
 -------------------
		begin				: 2017-04-21
		copyright			: (C) 2017 by UNIMI
		email				: enrico.chiaradia@unimi.it
 ***************************************************************************/

/***************************************************************************
 *																		 *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or	 *
 *   (at your option) any later version.								   *
 *																		 *
 ***************************************************************************/
"""

__author__ = 'UNIMI'
__date__ = '2017-04-21'
__copyright__ = '(C) 2017 by UNIMI'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from PyQt4 import QtGui, uic
	
#qgis import
from qgis.core import *
from qgis.gui import *
#other
import os
import sys

import GdalTools_utils as Utils

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
	sys.path.insert(0, cmd_folder)


uiFilePath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'common_settings.ui'))
FormClass = uic.loadUiType(uiFilePath)[0]

class CommonSettings(QDialog,FormClass):

	TITLE = "SMARTGREEN"
	TYPE = None
	
	closed = pyqtSignal()
	
	def __init__(self, parent=None, title = 'SMARTGREEN'):
		QDialog.__init__(self, parent)
		self.setupUi(self)
		self.setWindowTitle(title)
		self.initValues()
		
		QObject.connect(self.buttonBox, SIGNAL("accepted()"), self.accept)
		QObject.connect(self.buttonBox, SIGNAL("rejected()"), self.reject)
		QMetaObject.connectSlotsByName(self)
		
	def closeEvent(self, event):
		self.closed.emit()
	
	def initValues(self):
		s = QSettings()
		pathToMOBIDIC = s.value('SMARTGREEN/pathToMOBIDIC', '')
		pathToMATLAB = s.value('SMARTGREEN/pathToMATLAB', '')
		pathToLinks = s.value('SMARTGREEN/pathToLinks', '')
		pathToNodes = s.value('SMARTGREEN/pathToNodes', '')
		pathToLanduses = s.value('SMARTGREEN/pathToLanduses', '')
		pathToSoils = s.value('SMARTGREEN/pathToSoils', '')
		pathToWheatherStations = s.value('SMARTGREEN/pathToWheatherStations', '')
		pathToAcquifers = s.value('SMARTGREEN/pathToAcquifers', '')
		debugMode = s.value('SMARTGREEN/debugMode', False)
		#print 'debugMode:',debugMode
		if debugMode == 'False':
			debugMode = False
		else:
			debugMode = True
		
		
		self.EXE.setText(pathToMOBIDIC)
		self.MATLAB.setText(pathToMATLAB)
		self.LINKS.setText(pathToLinks)
		self.NODES.setText(pathToNodes)
		self.LANDUSES.setText(pathToLanduses)
		self.SOILS.setText(pathToSoils)
		self.WHEATHERSTATIONS.setText(pathToWheatherStations)
		self.ACQUIFERS.setText(pathToAcquifers)

		self.DEBUGMODE.setChecked(debugMode)
		
		# connect buttons
		self.EXE_BTN.clicked.connect(lambda: self.selectExefile(self.EXE))
		self.MATLAB_BTN.clicked.connect(lambda: self.selectFolder(self.MATLAB))
		self.LINKS_BTN.clicked.connect(lambda: self.selectShapefile(self.LINKS))
		self.NODES_BTN.clicked.connect(lambda: self.selectShapefile(self.NODES))
		self.LANDUSES_BTN.clicked.connect(lambda: self.selectShapefile(self.LANDUSES))
		self.SOILS_BTN.clicked.connect(lambda: self.selectShapefile(self.SOILS))
		self.WHEATHERSTATIONS_BTN.clicked.connect(lambda: self.selectShapefile(self.WHEATHERSTATIONS))
		self.ACQUIFERS_BTN.clicked.connect(lambda: self.selectShapefile(self.ACQUIFERS))
		
	def setSettings(self):
		s = QSettings()
		pathToMOBIDIC = s.setValue('SMARTGREEN/pathToMOBIDIC', self.EXE.text())
		pathToMATLAB = s.setValue('SMARTGREEN/pathToMATLAB', self.MATLAB.text())
		pathToLinks = s.setValue('SMARTGREEN/pathToLinks', self.LINKS.text())
		pathToNodes = s.setValue('SMARTGREEN/pathToNodes', self.NODES.text())
		pathToLanduses = s.setValue('SMARTGREEN/pathToLanduses', self.LANDUSES.text())
		pathToSoils = s.setValue('SMARTGREEN/pathToSoils', self.SOILS.text())
		pathToWheatherStations = s.setValue('SMARTGREEN/pathToWheatherStations', self.WHEATHERSTATIONS.text())
		pathToAcquifers = s.setValue('SMARTGREEN/pathToAcquifers', self.ACQUIFERS.text())
		if self.DEBUGMODE.isChecked():
			debugMode = s.setValue('SMARTGREEN/debugMode', 'True')
		else:
			debugMode = s.setValue('SMARTGREEN/debugMode', 'False')
		
		
	def selectShapefile(self,destFld):
		# open qgis file browser
		lastUsedFilter = Utils.FileFilter.lastUsedVectorFilter()
		#print Utils.FileFilter.allVectorsFilter()
		inputFile = Utils.FileDialog.getOpenFileName( self, self.tr('Select a valid vector file'), Utils.FileFilter.allVectorsFilter(), lastUsedFilter )
		if not inputFile:
			return
		Utils.FileFilter.setLastUsedVectorFilter( lastUsedFilter )
		destFld.setText(inputFile)
		
	def selectExefile(self,destFld):
		# open qgis file browser
		inputFile = Utils.FileDialog.getOpenFileName( self, self.tr('Select a valid executable file'),\
																				self.tr('All files (*);;Windows executable file (*.exe)'),\
																				[self.tr('Windows executable file (*.exe)')])
		if not inputFile:
			return
		destFld.setText(inputFile)
		
	def selectFolder(self,destFld):
		# open qgis file browser
		inputFile = Utils.FileDialog.getExistingDirectory( self, self.tr('Select the folder that contains the MATLAB runtime'))
		if not inputFile:
			return
		destFld.setText(inputFile)