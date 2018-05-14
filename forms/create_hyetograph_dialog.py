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
from PyQt4 import QtCore, QtGui
from custom_input import NumericInput, StringInput, CheckInput,VectorLayerInput,FieldInput,ListInput


class CreateHyetographDialog(QtGui.QDialog):
	def __init__(self,tr = None):
		QtGui.QDialog.__init__(self) 
		
		if tr is None:
			self.tr = lambda x: x
		else:
			self.tr = tr
				
		self.setObjectName("CreateHyetograph")
		self.setWindowTitle(self.tr('Create hyetograph'))
		self.resize(400, 100)
		
		grid = QtGui.QGridLayout()
		grid.setSpacing(1)
		
		self.duration = NumericInput('Duration',60,'The duration time of the rain event in minutes')
		self.step = NumericInput('Step',5,'The time step in minutes')
		self.returnTime = NumericInput('Return time',10,'The return time period in years')
		self.method = ListInput('method',['uniform','chicago'],'The method to use to build the time serie')
		self.relativePeakTime = NumericInput('Relative time of peak',0.5,'The center of the rainfall event for Chicago method (0-1)')
		self.serieName = StringInput('Name','Something of meaningfull','The name to assign to the output serie',True)
		self.useSelection = CheckInput('Use selection',False,'Make a time series for all the selected features')
		self.updateLayer = CheckInput('Update layer',True,'Update table field in weather stations layer')
		
		#~ grid.addWidget(self.weatherStationslayer, 1, 0)
		grid.addWidget(self.duration, 2,0)
		grid.addWidget(self.step, 3,0)
		grid.addWidget(self.returnTime, 4,0)
		grid.addWidget(self.method, 5,0)
		grid.addWidget(self.relativePeakTime, 6,0)
		grid.addWidget(self.serieName, 7,0)
		#~ grid.addWidget(self.useSelection, 8,0)
		grid.addWidget(self.updateLayer, 9,0)
		
		self.buttonBox = QtGui.QDialogButtonBox(self)
		self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
		self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
		self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
		self.buttonBox.setObjectName("buttonBox")
		
		grid.addWidget(self.buttonBox,10,0)
		
		self.setLayout(grid)
		
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.accept)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), self.reject)
		QtCore.QMetaObject.connectSlotsByName(self)
	
	def getParameterValue(self):
		res = (self.duration.getValue(),self.step.getValue(),self.returnTime.getValue(),\
				self.method.getValue(),self.relativePeakTime.getValue(),\
				self.serieName.getValue(),self.useSelection.getValue(),self.updateLayer.getValue())
		return res