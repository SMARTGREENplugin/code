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
from custom_input import NumericInput, CheckInput,LayerInput,StringInput

from qgis.core import *
from qgis.gui import *

import os


class SimulationInfoDialog(QtGui.QDialog):
	def __init__(self,tr = None):
		QtGui.QDialog.__init__(self) 
		
		if tr is None:
			self.tr = lambda x: x
		else:
			self.tr = tr
				
		self.setObjectName("NewProject")
		self.resize(400, 300)
		self.setWindowTitle(self.tr("SMARTGREEN - new simulation"))
		
		# create input box
		self.prjName = StringInput(self.tr('Project name:'),self.tr('Something of meaningful'),self.tr('Write here the name of the project'))
		self.descrName = StringInput(self.tr('Project description:'),self.tr('Something of meaningful'),self.tr('Write here the description of the project'),False)
		
		self.buttonBox = QtGui.QDialogButtonBox(self)
		self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
		self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
		self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
		self.buttonBox.setObjectName("buttonBox")
		
		grid = QtGui.QGridLayout()
		grid.setSpacing(1)

		grid.addWidget(self.prjName, 1, 0)
		grid.addWidget(self.descrName, 2,0)
		grid.addWidget(self.buttonBox,3,0)
		
		self.setLayout(grid)

		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.accept)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), self.reject)
		QtCore.QMetaObject.connectSlotsByName(self)
		
	def getValues(self):
		prjName = unicode(self.prjName.getValue())
		descrName = unicode(self.descrName.getValue())
		
		return prjName,descrName
