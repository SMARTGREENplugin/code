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

def formOpen(dialog,layerid,featureid):
	global myDialog
	myDialog = dialog
	global layer
	layer = layerid
	global feature
	feature = featureid
	
	# hide dummy QLineBox
	nodeIdFld = dialog.findChild(QLineEdit,'NODE_ID')
	nodeIdFld.setHidden(True)
	maFld = dialog.findChild(QLineEdit,'MA')
	maFld.setHidden(True)
	mfFld = dialog.findChild(QLineEdit,'MF')
	mfFld.setHidden(True)
	
	# set fixed size
	# TODO
	
	#~ # polupate combos with value
	nodeIdCB = dialog.findChild(QComboBox,'NODE_ID_CB')
	updateNodeItems(nodeIdCB, nodeIdFld)
	nodeIdCB.currentIndexChanged[str].connect(nodeIdFld.setText)
	
	maCB = dialog.findChild(QComboBox,'MA_CB')
	updateYesNoItems(maCB, maFld)
	maCB.currentIndexChanged[str].connect(maFld.setText)
	
	mfCB = dialog.findChild(QComboBox,'MF_CB')
	updateYesNoItems(mfCB, mfFld)
	mfCB.currentIndexChanged[str].connect(mfFld.setText)
	
	flag = layer.isEditable()
	nodeIdCB.setEnabled(flag)
	maCB.setEnabled(flag)
	mfCB.setEnabled(flag)
		
	buttonBox = dialog.findChild(QDialogButtonBox,'buttonBox')

	# Disconnect the signal that QGIS has wired up for the dialog to the button box.
	buttonBox.accepted.disconnect(myDialog.accept)

	# Wire up our own signals.
	buttonBox.accepted.connect(validate)
	buttonBox.rejected.connect(myDialog.reject)
	
 
def validate():
	# Make sure that the name field isn't empty.
	myDialog.accept()
	
def updateNodeItems(comboBox, lineEdit):
	# get unique value list from nodes --> obj_id
	DBM = qgis.utils.plugins['SMARTGREEN'].DBM
	lay = qgis.utils.plugins['SMARTGREEN'].getLayerBySource(DBM.getDefault('qgis.nodeslayer'))
	idx = lay.fieldNameIndex(DBM.getDefault('qgis.nodeslayer.field.obj_id'))
	values = lay.uniqueValues(idx)
	values = ['NULL']+values
	comboBox.addItems(['']+values)
	val = lineEdit.text()
	if type(val) == QPyNullVariant:
		val = ''
				
	index = comboBox.findText(val, QtCore.Qt.MatchFixedString)
	if index >= 0:
		comboBox.setCurrentIndex(index)
	
def updateYesNoItems(comboBox, lineEdit):
	comboBox.addItems(['0','1'])
	val = lineEdit.text()
	
	if type(val) == QPyNullVariant:
		val = ''	
		
	index = comboBox.findText(val, QtCore.Qt.MatchFixedString)
	if index >= 0:
		comboBox.setCurrentIndex(index)