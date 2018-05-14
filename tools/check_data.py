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
from qgis.core import *
import os.path
from time import gmtime, strftime
import logging
import math
 


class MyProgress():
	def setInfo(self,text, error=False):
		if error:
			print 'ERROR: %s' %text
		else:
			print 'INFO:  %s' %text
	
	def setPercentage(self,val):
		nblock = int(val/10)
		blocks = ['#']*nblock
		lines = ['_']*(10-nblock)
		bar = blocks+lines
		#print ''.join(bar)+'%s'%int(val)+'%'


class CheckData():
	
	def __init__(self, linksLayer, nodesLayer, progress = None):
		### Message code ###
		# 1 = new node
		# 2  = new id
		# 3 = edit node reference in link table
		# 4 = EMPTY
		# 5 = add default value
		# 6 = set elevation to node
		# 7 = set bottom elevation
		# 8 = set link elevation at start and end point
		# 9 = set depth = elevation top - elevation bottom
		# 10 = fix botton elevation of node
		# 11 = fix top elevation of node
		# 12 = empty value
		# 13 = too small value
		# 14 = too big value
		# 15 = unexpeted value
		
		# set links and nodes
		self.linksLayer = linksLayer
		self.nodesLayer = nodesLayer
		
		# set up tolerance, etc, ...
		crs = self.linksLayer.crs().authid()
		if crs == 'EPSG:4269':
			self.rec = .0001
			self.tol = .0001
		else:
			self.rec = 0.1
			self.tol = 0.1

		if progress is None:
			self.progress = MyProgress()
		else:
			self.progress = progress
		
		#self.progress.setInfo('test message', error = False)
		self.maxWalk = 0
	
	def appendMessage(self,layer,feature,idx,text):
		if isinstance(feature, QgsFeature):
			fid = feature.id()
		else:
			fid = feature
			allfeatures = {feature.id(): feature for (feature) in layer.getFeatures()}
			feature = allfeatures[fid]
		
		if isinstance(feature.attributes()[idx], QPyNullVariant): text = text
		else: text = feature.attributes()[idx]+', '+text
		
		layer.changeAttributeValue(fid,idx,text,True)
		
	def calculateLinksAngle(self, link,direction = 1):
		vtx = link.geometry().asPolyline()
		#~ print 'nodes:',nodes
		if len(vtx) ==  0:
			vtx = link.geometry().asMultiPolyline()
			vtx = vtx[0]
		
		if direction ==1:
			vtxStart = vtx[0]
			vtxEnd = vtx[1]
		else:
			vtxStart = vtx[len(vtx)-1]
			vtxEnd = vtx[len(vtx)-2]
			
		dx = vtxStart.x()-vtxEnd.x()
		
		if dx == 0.0:
			angle = 0.0 # N-S
		else:
			dy = vtxStart.y()-vtxEnd.y()
			angle = math.atan(dy/dx)
		
		return angle
		
	def getExtremeLinks(self,direction = 1,startNodeFld = 'NODE_START',endNodeFld= 'NODE_END'):
		# get the list of links that have no inlet or outlet
		if direction!=1:
			# flip search direction
			dummy = startNodeFld
			startNodeFld = endNodeFld
			endNodeFld = dummy
			
		linkList = []
		linkIds = []
		for link in self.linksLayer.getFeatures():
			# get following links
			node = self.getNodeByLink(link,endNodeFld)
			nodeId = node['OBJ_ID']
			# get the link that start/end
			expr = QgsExpression( "\"%s\" = '%s'"%(startNodeFld,nodeId))
			toLinks = self.linksLayer.getFeatures(QgsFeatureRequest( expr ))
			newLink = None
			for toLink in toLinks:
				# calculate toLink angle
				newLink = toLink
			
			if newLink is None:
				linkList.append(link)
				linkIds.append(link.id())
				
		return linkIds
	
	def getSortedLinks(self,startLink,direction=1,startNodeFld = 'NODE_START',endNodeFld= 'NODE_END'):
		# get the list of chained links based on object id and link direction
		if direction!=1:
			# flip search direction
			dummy = startNodeFld
			startNodeFld = endNodeFld
			endNodeFld = dummy
		
		linkList = [startLink]
		linkIds = [startLink.id()]
		
		for link in linkList:
			# get following links
			node = self.getNodeByLink(link,endNodeFld)
			nodeId = node['OBJ_ID']
			# get the link that start/end
			expr = QgsExpression( "\"%s\" = '%s'"%(startNodeFld,nodeId))
			toLinks = self.linksLayer.getFeatures(QgsFeatureRequest( expr ))
			newLink = None
			newAngleDiff = 10 # maximum angle diff is 2*pi
			for toLink in toLinks:
				linkList.append(toLink)
				linkIds.append(toLink.id())
				
		return linkIds
	
		
	def getChainedLinks(self,startLink,direction=1,startNodeFld = 'NODE_START',endNodeFld= 'NODE_END'):
		# get the list of chained links based on object id and link direction
		if direction!=1:
			# flip search direction
			dummy = startNodeFld
			startNodeFld = endNodeFld
			endNodeFld = dummy
		
		linkList = [startLink]
		linkIds = [startLink.id()]
		
		for link in linkList:
			angle1 = self.calculateLinksAngle(link,direction)
			# get following links
			node = self.getNodeByLink(link,endNodeFld)
			nodeId = node['OBJ_ID']
			# get the link that start/end
			expr = QgsExpression( "\"%s\" = '%s'"%(startNodeFld,nodeId))
			toLinks = self.linksLayer.getFeatures(QgsFeatureRequest( expr ))
			newLink = None
			newAngleDiff = 10 # maximum angle diff is 2*pi
			for toLink in toLinks:
				# calculate toLink angle
				angle2 = self.calculateLinksAngle(toLink,direction)
				absAngleDiff = math.fabs(angle1-angle2)
				if absAngleDiff < newAngleDiff:
					newLink = toLink
					newAngleDiff = absAngleDiff
			
			if newLink is not None:
				linkList.append(newLink)
				linkIds.append(newLink.id())
				
		return linkIds
		
	def getIntersectionByPoint(self,point,layer):
		searchRect = QgsRectangle(point.x() - self.rec, point.y() - self.rec, point.x() + self.rec, point.y() + self.rec)
		request = QgsFeatureRequest().setFilterRect(searchRect)
		features = layer.getFeatures(request)
		return features
		
	def getFeatureCount(self,features):
		i = 0
		for f in features:
			i+=1
		
		return i
		
	def addNode(self,point):
		with edit(self.nodesLayer):
			pr = self.nodesLayer.dataProvider()
			#~ self.nodesLayer.startEditing()
			feat = QgsFeature(self.nodesLayer.pendingFields())
			feat.setGeometry(QgsGeometry.fromPoint(point))
			idx = self.nodesLayer.fieldNameIndex('MSG')
			print 'idx:',idx
			#feat.attributes()[idx] = '1'
			pr.addFeatures( [ feat ] )
			#~ self.appendMessage(self.nodesLayer,feat,idx,'1')
			
			#save and update layer
			#~ self.nodesLayer.commitChanges()
			self.nodesLayer.updateExtents()
		
		#~ with edit(self.nodesLayer):
			#~ self.nodesLayer.changeAttributeValue(fid, attr_index, new_value)
			
	def addNodes(self,pointList):
		#with edit(self.nodesLayer):
		pr = self.nodesLayer.dataProvider()
		#~ self.nodesLayer.startEditing()
		for point in pointList:
			feat = QgsFeature(self.nodesLayer.pendingFields())
			feat.setGeometry(QgsGeometry.fromPoint(point))
			idx = self.nodesLayer.fieldNameIndex('MSG')
			feat.setAttribute(idx, '1')
			pr.addFeatures( [ feat ] )
			self.progress.setInfo('Added new point', error = False)
				
			#save and update layer
		self.nodesLayer.updateExtents()
		self.nodesLayer.triggerRepaint()
		
	def addToList(self,aList,a):
		aExist = False
		for aa in aList:
			if aa == a:
				aExist = True
				break
				
		if not aExist:
			aList.append(a)
		
	def checkNumberNodes(self, fix = False):
		f = -1.0
		nfeat = self.linksLayer.featureCount() 
		nodeList = []
		for feature in self.linksLayer.getFeatures():
			f+=1.0
			#self.progress.setPercentage(100*f/nfeat)
			link = feature.geometry().asMultiPolyline()
			nOfLinks = len(link)
			if nOfLinks >1:
				self.progress.setInfo('number of links %s at link <a href="find;%s;%s">%s</a> (row id: %s) is greater than 1. Only first link will be used!'%(nOfLinks,self.linksLayer.id(),feature.id(),feature.id(),f))
						
			link = link[0]
			# get upstream node
			selNodes = self.getIntersectionByPoint(link[0],self.nodesLayer)
			nSelNodes = self.getFeatureCount(selNodes)
			if nSelNodes==0:
				self.progress.setInfo('No nodes found at link <a href="find;%s;%s">%s</a> (row id: %s), upstream'%(self.linksLayer.id(),feature.id(),feature.id(),f), error = True)
				#self.addNode(link[0])
				#nodeList.append(link[0])
				self.addToList(nodeList,link[0])
			if nSelNodes==1:
				#self.progress.setInfo('One selected node at link %s, upstream'%f, error = False)
				pass
			if nSelNodes>1:
				self.progress.setInfo('More than one (%s) nodes was selected at link <a href="find;%s;%s">%s</a> (row id: %s), upstream'%(nSelNodes,self.linksLayer.id(),feature.id(),feature.id(),f), error = True)
				
			selNodes = self.getIntersectionByPoint(link[-1],self.nodesLayer)
			nSelNodes = self.getFeatureCount(selNodes)
			if nSelNodes==0:
				self.progress.setInfo('No nodes found at link <a href="find;%s;%s">%s</a> (row id: %s), downstream'%(self.linksLayer.id(),feature.id(),feature.id(),f), error = True)
				#self.addNode(link[1])
				#nodeList.append(link[len(link)-1])
				self.addToList(nodeList,link[len(link)-1])
			if nSelNodes==1:
				#self.progress.setInfo('One selected node at link %s, downstream'%f, error = False)
				pass
			if nSelNodes>1:
				self.progress.setInfo('More than one (%s) nodes was selected at link <a href="find;%s;%s">%s</a> (row id: %s), downstream'%(nSelNodes,self.linksLayer.id(),feature.id(),feature.id(),f), error = True)
		
		if fix: self.nodesLayer.startEditing()
		
		# add new nodes ...
		if self.nodesLayer.isEditable(): self.addNodes(nodeList)
		
		if fix:
			self.nodesLayer.commitChanges()
			self.nodesLayer.updateExtents()
		
		self.progress.setInfo('Finished! n. of missing node: %s'%len(nodeList), error = False)
		
	def checkId(self,layer,fieldName,root = 'SG', fix = False):
		
		idx = layer.fieldNameIndex(fieldName)
		msgIdx = layer.fieldNameIndex('MSG')
		# select all feture that have id that starts with SG
		expr = QgsExpression( "\"%s\" like '%s"%(fieldName,root)+"%'")
		features = layer.getFeatures( QgsFeatureRequest( expr ) )
		maxVal = 0
		for feat in features:
			try:
				val = feat.attributes()[idx]
				val = int(val[len(root):])
			except: val = 0
			
			if val>maxVal: maxVal = val
			
		expr = QgsExpression( "\"%s\" is Null"%fieldName)
		features = layer.getFeatures( QgsFeatureRequest( expr ) )
		idList = []
		nameList = []
		msgList = []
		
		for feat in features:
			maxVal+=1
			self.progress.setInfo('In %s,<a href="find;%s;%s"> feature %s</a> has no id. Suggested is "%s%s"'%(layer.name(),layer.id(),feat.id(),feat.id(),root,maxVal), error = True)
			idList.append(feat.id())
			nameList.append('%s%s'%(root,maxVal))
			msgList.append('2(%s)'%(fieldName))
			
		if fix: layer.startEditing()
			
		if layer.isEditable():
			for i,id in enumerate(idList):
				self.progress.setInfo('%s replaced in <a href="find;%s;%s"> feature %s</a>'%(nameList[i],layer.id(),feat.id(),feat.id()),False)
				layer.changeAttributeValue(id,idx,nameList[i],True)
				self.appendMessage(layer,id,msgIdx,msgList[i])
				
		if fix:
			layer.commitChanges()
			layer.updateExtents()
	
	def linkNodesConnectionList(self, startIdFld, endIdFld, objIdFld):
		# update nodes id (start and end node) in link table
		startIdIdx = self.linksLayer.fieldNameIndex(startIdFld)
		endIdIdx = self.linksLayer.fieldNameIndex(endIdFld)
		objIdIdx = self.nodesLayer.fieldNameIndex(objIdFld)
		
		#self.progress.setInfo('Start Id (%s), End id (%s) and obj Id (%s)'%(startIdFld,endIdFld,objIdFld))
		#self.progress.setInfo('Start Id index (%s), End id index (%s) and obj Id index (%s)'%(startIdIdx,endIdIdx,objIdIdx))
		
		msgLinkIdx = self.linksLayer.fieldNameIndex('MSG')
		
		#self.linksLayer.startEditing()
		
		nfeat = self.linksLayer.featureCount() 
		
		idList = []
		destIdxList = []
		objIdList = []
		msgList = []
		
		for feature in self.linksLayer.getFeatures():
			f =feature.id()-1
			self.progress.setPercentage(100*f/nfeat)
			link = feature.geometry().asMultiPolyline()
			nOfLinks = len(link)
			if nOfLinks >1:
				self.progress.setInfo('number of links (%s) is greater than 1. Only first link will be used!'%(nOfLinks))
						
			link = link[0]
			# process upstream node
			selNodes = self.getIntersectionByPoint(link[0],self.nodesLayer)
			# get node id
			startId = feature.attributes()[startIdIdx]
			objId = startId
			for selNode in selNodes:
				objId = selNode.attributes()[objIdIdx]
				#self.progress.setInfo('Node Id: %s at the start of link %s'%(objId,f))
				break
			
			#self.progress.setInfo('Start Id (%s) and obj Id (%s) ad feature %s'%(startId,objId,f))
			
			if startId != objId:
				self.progress.setInfo('Start node Id (%s) differs from obj Id (%s) at <a href="find;%s;%s">link %s</a>'%(startId,objId,self.linksLayer.id(),feature.id(),feature.id()),True)
				idList.append(feature.id())
				destIdxList.append(startIdIdx)
				objIdList.append(objId)
				msgList.append('3(%s)'%startIdFld)
				#~ self.linksLayer.changeAttributeValue(feature.id(),startIdIdx,objId,True)
				#~ self.appendMessage(self.linksLayer,feature,msgLinkIdx,'3')
			else:
				pass
				#self.progress.setInfo('Node Id and geometry match',False)
				
			# process downstream node
			selNodes = self.getIntersectionByPoint(link[-1],self.nodesLayer)
			# get node id
			endId = feature.attributes()[endIdIdx]
			objId = endId
			for selNode in selNodes:
				objId = selNode.attributes()[objIdIdx]
				#self.progress.setInfo('Node Id: %s at the end of link %s'%(objId,f))
				break
			
			#self.progress.setInfo('End Id (%s) and obj Id (%s) ad feature %s'%(endId,objId,f))
			
			if endId != objId:
				self.progress.setInfo('End node Id (%s) differs from obj Id (%s) at <a href="find;%s;%s">link %s</a>'%(endId,objId,self.linksLayer.id(),feature.id(),feature.id()),True)
				idList.append(feature.id())
				destIdxList.append(endIdIdx)
				objIdList.append(objId)
				msgList.append('3(%s)'%endIdFld)
				#~ self.linksLayer.changeAttributeValue(feature.id(),endIdIdx,objId,True)
				#~ self.appendMessage(self.linksLayer,feature,msgLinkIdx,'4')
			else:
				pass
				#self.progress.setInfo('Node Id and geometry match',False)
				
		return idList,destIdxList,objIdList,msgList
		
	def checkLinkNodesConnection(self, startIdFld, endIdFld, objIdFld,fix=False):
		
		idList,destIdxList,objIdList,msgList = self.linkNodesConnectionList(startIdFld, endIdFld, objIdFld)
		
		msgIdx = self.linksLayer.fieldNameIndex('MSG')
		#self.linksLayer.rollBack()
		#self.nodesLayer.rollBack()
		
		if fix: self.linksLayer.startEditing()
		
		if self.linksLayer.isEditable():
			for i,id in enumerate(idList):
				self.progress.setInfo('%s replaced in <a href="find;%s;%s">link %s</a>'%(objIdList[i],self.linksLayer.id(),id,id),False)
				self.linksLayer.changeAttributeValue(id,destIdxList[i],objIdList[i],True)
				self.appendMessage(self.linksLayer,id,msgIdx,msgList[i])
				
		if fix:
			self.linksLayer.commitChanges()
			self.linksLayer.updateExtents()
		
	def replaceNull(self,layer,fieldName, newValue = 0.0, fix = False):
		idx = layer.fieldNameIndex(fieldName)
		msgIdx = layer.fieldNameIndex('MSG')
		idList = []
		msgList = []
		
		expr = QgsExpression( "\"%s\" is Null"%fieldName)
		features = layer.getFeatures( QgsFeatureRequest( expr ) )
		for feat in features:
			idList.append(feat.id())
			msgList.append('5(%s)'%fieldName)
			
		self.progress.setInfo('A total of %s NULL values should be replaced with %s in %s field of %s'%(len(idList),newValue,fieldName,layer.name()),False)
		
		if fix: layer.startEditing()
		
		if layer.isEditable():
			for i,id in enumerate(idList):
				layer.changeAttributeValue(id,idx,newValue,True)
				self.appendMessage(layer,id,msgIdx,msgList[i])
				
		if fix:
			layer.commitChanges()
			layer.updateExtents()

				
	def replaceValue(self,layer,fieldName, newValue = 0.0,oldValue = "NULL"):
		self.progress.setInfo('field name: %s, new value: %s, old value: %s'%(fieldName,newValue,oldValue),False)
		# select features with attribute equal to "oldvalue"
		layer.startEditing()
		idx = layer.fieldNameIndex(fieldName)
		msgIdx = layer.fieldNameIndex('MSG')
			
		if oldValue == 'NULL': expr = QgsExpression( "\"%s\" is Null"%fieldName)
		elif isinstance(oldValue, (int, float, complex)): expr = QgsExpression( "\"%s\" == %s"%(fieldName,oldValue))
		elif isinstance(oldValue, str): expr = QgsExpression( "\"%s\" == '%s'"%(fieldName,oldValue))
		else:
			self.progress.setInfo('Unmanaged old value: %s'%(fieldName,newValue,oldValue),True)
			return
		
		features = layer.getFeatures( QgsFeatureRequest( expr ) )
		for feat in features:
			layer.changeAttributeValue(feat.id(),idx,newValue,True)
			self.appendMessage(layer,feat,msgIdx,'5(%s)'%fieldName)
			
		#save and update layer
		layer.commitChanges()
		layer.updateExtents()
	
	def fixNodeDepth(self,layer,depthFld, elevBotFld, elevTopFld, defDepth):
		#self.progress.setInfo('field name: %s, new value: %s, old value: %s'%(fieldName,newValue,oldValue),False)
		# select features with attribute equal to "oldvalue"
		layer.startEditing()
		depthIdx = layer.fieldNameIndex(depthFld)
		elevBotIdx = layer.fieldNameIndex(elevBotFld)
		elevTopIdx = layer.fieldNameIndex(elevTopFld)
		msgIdx = layer.fieldNameIndex('MSG')
		
		expr = QgsExpression( "\"%s\" is Null"%depthFld)
		features = layer.getFeatures( QgsFeatureRequest( expr ) )
		for feat in features:
			# get attribute
			attrs = feat.attributes()
			elevBot = attrs[elevBotIdx]
			elevTop = attrs[elevTopIdx]
			depth = attrs[depthIdx]
			if isinstance(depth, QPyNullVariant):
				if isinstance(elevBot, QPyNullVariant) or isinstance(elevTop, QPyNullVariant):
					# use default depth
					layer.changeAttributeValue(feat.id(),depthIdx,defDepth,True)
					self.appendMessage(layer,feat,msgIdx,'5(%s)'%depthFld)
				else:
					# assign elevation difference
					layer.changeAttributeValue(feat.id(),depthIdx,elevTop-elevBot,True)
					self.appendMessage(layer,feat,msgIdx,'9(%s)'%depthFld)

		#save and update layer
		layer.commitChanges()
		layer.updateExtents()
		
	def checkFullEmptyField(self,checkLayer,checkField):
		elevIdx = checkLayer.fieldNameIndex(checkField)
		allCount = 0
		for feat in checkLayer.getFeatures():
			allCount+=1
			
		expr = QgsExpression( "\"%s\" is Null"%checkField)
		features = self.nodesLayer.getFeatures( QgsFeatureRequest( expr ) )
		emptyCount = 0
		for feat in features:
			emptyCount+=1
		
		if allCount == emptyCount:
			return True
		else:
			return False

	
	def fillEmptyElevation(self, elevField,idPtField,fromPtField,toPtField, defaultSlope = 0.01,defaultElev = 100):
		self.nodesLayer.startEditing()
		# set field index
		elevIdx = self.nodesLayer.fieldNameIndex(elevField)
		idIdx = self.nodesLayer.fieldNameIndex(idPtField)
		msgIdx = self.nodesLayer.fieldNameIndex('MSG')
		
		# select points with empty elevation
		expr = QgsExpression( "\"%s\" is Null"%elevField)
		features = self.nodesLayer.getFeatures( QgsFeatureRequest( expr ) )
		# loop in selection
		for feat in features:
			# for each point get id
			ptId = feat.attributes()[idIdx]
			self.progress.setInfo('Processing point %s'%ptId,False)
			# go upstream and stop when you find a value (store path length)
			self.maxWalk = 0
			upElev, upDist = self.walk(ptId, idPtField, elevField,fromPtField,toPtField,-1)
			self.progress.setInfo('Upstream valid point elevation %s at distance %s'%(upElev, upDist),False)
			# go downstream and stop when you find a value (store path length)
			self.maxWalk = 0
			dwnElev, dwnDist = self.walk(ptId,idPtField, elevField,fromPtField,toPtField,1)
			self.progress.setInfo('Downstream valid point elevation %s at distance %s'%(dwnElev, dwnDist),False)
			if (upElev is not None) and (dwnElev is not None):
				# calculate estimated elevation by linear interpolation (proportion)
				deltaTot = upElev-dwnElev
				deltaUp = deltaTot*upDist/(upDist+dwnDist)
				estElev= upElev-deltaUp
			elif (upElev is None) and ((dwnElev is not None)):
				estElev = dwnElev+defaultSlope*dwnDist
			elif (upElev is not None) and ((dwnElev is None)):
				estElev = upElev-defaultSlope*upDist
			else:
				# if both end points in the list (upstream and downstream) are None, assign the default elevation to the "feat" point
				# following point will start from that elevation
				estElev = defaultElev
				
			
			self.progress.setInfo('Assigned elevation at point %s is %s'%(ptId, estElev),False)
			# assign estimated elevation to point
			self.nodesLayer.changeAttributeValue(feat.id(),elevIdx,estElev,True)
			self.appendMessage(self.nodesLayer,feat,msgIdx,'6(%s)'%elevField)
		
		#save and update layer
		self.nodesLayer.commitChanges()
		self.nodesLayer.updateExtents()
		
	def walk(self,startId,idFld,elevFld,fromFld,toFld,direction = 1):
		#print startId,idFld,elevFld,fromFld,toFld,direction
		if direction == -1:
			#flip table fields
			dummy = fromFld
			fromFld = toFld 
			toFld = dummy
			
		elevIdx = self.nodesLayer.fieldNameIndex(elevFld)
		toIdx = self.linksLayer.fieldNameIndex(toFld)
		
		idList = [startId]
		
		elev = None
		totDist = 0
		lastSlope = 0.01
		
		while idList:
			startId = idList[0]
			query = "\"%s\" LIKE '%s'"%(fromFld,startId)
			#print query
			expr = QgsExpression(query)
			links = self.linksLayer.getFeatures( QgsFeatureRequest( expr ) )
			dist = 0
			
			idList.pop(0) # remove the last processed
			
			#~ if self.maxWalk > 10:
				#~ self.progress.setInfo('Too much point!',True)
				#~ return elev,totDist
			
			for link in links:
				self.progress.setInfo('Processing link %s '%link.attributes()[0],False)
				# add length
				dist = link.geometry().length()
				totDist+=dist
				# calculate slope if possible
				
				# get following point id
				toId = link.attributes()[toIdx]
				# select nodes with the same id
				query =  "\"%s\" LIKE '%s'"%(idFld,toId)
				#print query
				expr = QgsExpression(query)
				nodes = self.nodesLayer.getFeatures( QgsFeatureRequest( expr ) )
				for node in nodes:
					self.progress.setInfo('Processing node %s '%node.attributes()[0],False)
					elev = node.attributes()[elevIdx]
					if isinstance(elev, QPyNullVariant):
						elev = None
						self.maxWalk+=1
						#print 'walk again ... %s'%(self.maxWalk)
						# append new point to list
						idList.append(toId)
						
					# get only the first node
					break

				# get only the first link
				break
		
		return elev,totDist
		
	def getRefDimension(self,link, diamFld = 'DIAM', dimFld = 'DIM1', shapeFld = 'S_SHAPE'):
		linkShape = link[shapeFld]
		# get the main dimension (diameter or heigth of the conduit)
		if linkShape == 'C':
			dim = link[diamFld]
		else:
			dim = link[dimFld]
			
		if isinstance(dim, QPyNullVariant):
			dim = None
		
		return dim
		
	def getDSMaxDiam(self,link,startNodeFld,endNodeFld):
		node = self.getNodeByLink(link,endNodeFld)
		nodeId = node['OBJ_ID']
		# get the link that start/end
		expr = QgsExpression( "\"%s\" = '%s'"%(startNodeFld,nodeId))
		toLinks = self.linksLayer.getFeatures(QgsFeatureRequest( expr ))
		toDims = []
		for toLink in toLinks:
			toDim = self.getRefDimension(toLink)
			if toDim is not None:
				toDims.append(toDim)
			
		if len(toDims)>0:
			maxDim = max(toDims)
		else:
			maxDim=None
		
		return maxDim
		
	def checkLinkDiam(self,diamFld,dim1Fld,shapeFld,startNodeFld,endNodeFld,minDiam = 0.1,maxDiam = 2, fix = False):
		idList = []
		nameList = []
		unresolved = []
		dimList = []
		msgList = []
		# create a list of links with NULL elevation values
		links = self.linksLayer.getFeatures()
		
		# loop in the list of links		
		for link in links:
			linkName = link['OBJ_ID']
			linkId = link.id()
			dim = self.getRefDimension(link)

			if dim is None:
				newDiam = self.getDSMaxDiam(link,startNodeFld,endNodeFld)
				
				if (newDiam is None) or (newDiam<minDiam) or (newDiam>maxDiam):
					# try with upstream selection
					newDiam=self.getDSMaxDiam(link,endNodeFld,startNodeFld) # get upstream
					
				if newDiam is None:
					self.progress.setInfo('Unable to find a correct value for <a href="find;%s;%s">link %s</a>'%( self.linksLayer.id(),linkId,linkName),True)
				else:
					self.progress.setInfo('<a href="find;%s;%s">link %s</a> has NULL dimension: suggested value is %s'%(self.linksLayer.id(),linkId,linkName,newDiam),True)
					idList.append(linkId)
					nameList.append(linkName)
					dimList.append(newDiam)
					msgList.append('12(%s)'%diamFld)
				
			elif dim < minDiam:
				newDiam = self.getDSMaxDiam(link,startNodeFld,endNodeFld)
				if (newDiam is None) or (newDiam<minDiam) or (newDiam>maxDiam):
					# try with upstream selection
					newDiam=self.getDSMaxDiam(link,endNodeFld,startNodeFld) # get upstream
					
					
				if newDiam is None:
					self.progress.setInfo('Unable to find a correct value for <a href="find;%s;%s">link %s</a>'%( self.linksLayer.id(),linkId,linkName),True)
				else:
					if newDiam<minDiam:
						newDiam = minDiam
					
					self.progress.setInfo('<a href="find;%s;%s">link %s</a> has too small dimension: suggested value is %s'%(self.linksLayer.id(),linkId,linkName,newDiam),True)
					idList.append(linkId)
					nameList.append(linkName)
					dimList.append(newDiam)
					msgList.append('13(%s)'%diamFld)
					
			elif dim > maxDiam:
				newDiam = self.getDSMaxDiam(link,startNodeFld,endNodeFld)
				if (newDiam is None) or (newDiam<minDiam) or (newDiam>maxDiam):
					# try with upstream selection
					newDiam=self.getDSMaxDiam(link,endNodeFld,startNodeFld) # get upstream
				
				if newDiam is None:
					self.progress.setInfo('Unable to find a correct value for <a href="find;%s;%s">link %s</a>'%( self.linksLayer.id(),linkId,linkName),True)
				else:
					if newDiam>maxDiam:
						newDiam = maxDiam
					
					self.progress.setInfo('<a href="find;%s;%s">link %s</a> has too big dimension: suggested value is %s'%(self.linksLayer.id(),linkId,linkName,newDiam),True)
					idList.append(linkId)
					nameList.append(linkName)
					dimList.append(newDiam)
					msgList.append('14(%s)'%diamFld)
			else:
				# compare with the following, downstream, link diameter
				newDiam = self.getDSMaxDiam(link,startNodeFld,endNodeFld)
				if newDiam is None:
					#do nothing
					pass
				else:
					if (newDiam>=minDiam) and (newDiam<=maxDiam):
						if newDiam<dim:
							# something of wrong here in the network!
							self.progress.setInfo('<a href="find;%s;%s">link %s</a> has unexpected dimension: suggested value is %s'%(self.linksLayer.id(),linkId,linkName,newDiam),True)
							idList.append(linkId)
							nameList.append(linkName)
							dimList.append(newDiam)
							msgList.append('15(%s)'%diamFld)
		
		#~ for i,id in enumerate(idList):
			#~ self.progress.setInfo('%s for link %s should be %s'%(msgList[i],nameList[i],dimList[i]),False)
			
		# select unresolved features
		#self.linksLayer.setSelectedFeatures(idList)
		self.linksLayer.select(idList)
		
		if fix: self.linksLayer.startEditing()
		
		if self.linksLayer.isEditable():
			diamIdx = self.linksLayer.fieldNameIndex(diamFld)
			msgIdx = self.linksLayer.fieldNameIndex('MSG')
			for i, id in enumerate(idList):
				# update attributes
				#print 'set link %s elev to %s'%(id,elevList[i])
				self.linksLayer.changeAttributeValue(id,diamIdx,dimList[i],True)
				self.appendMessage(self.linksLayer,id,msgIdx,msgList[i])
				
		if fix:
			self.linksLayer.commitChanges()
			self.linksLayer.updateExtents()
			
	def fixLinkElevs(self,startElevFld,endElevFld,startNodeFld,endNodeFld,nodeElevFld,lengthFld,slope, fix = False):
		#print 'slope:',slope
		idList = []
		startElevList = []
		endElevList = []
		startNodeList = []
		endNodeList = []
		lengthList = []
		msgList = []
		# loop in the list of links and populate variable list		
		for link in self.linksLayer.getFeatures():
			idList.append(link.id())
			startElevList.append(link[startElevFld])
			endElevList.append(link[endElevFld])
			startNodeList.append(link[startNodeFld])
			endNodeList.append(link[endNodeFld])
			lengthList.append(link[lengthFld])
			msgList.append('')
			
		#loop in the list of variable and get NULL value
		for i,link in enumerate(self.linksLayer.getFeatures()):
			# check downstream
			upElev = startElevList[i]
			newUpLinkIds = []
			upIsEnd = False
			feat = self.linksLayer.getFeatures(QgsFeatureRequest().setFilterFid(idList[i])).next()
			
			if isinstance(upElev, QPyNullVariant):
				#walk downstream and return a list of links to the first valid value
				upLinkIds = self.getChainedLinks(startLink= feat,direction=-1)
				upLinkIds.pop(0)
				for dId in upLinkIds:
					dIdx = idList.index(dId)
					endElev = endElevList[dIdx]
					if not isinstance(endElev, QPyNullVariant):
						#stop loop and store the elevation value and part of the list
						upElev = endElev
						upIsEnd = False
						break
					
					startElev = startElevList[dIdx]
					if not isinstance(startElev, QPyNullVariant):
						#stop loop and store the elevation value and part of the list
						upElev = startElev
						upIsEnd = True
						newUpLinkIds.append(dId)
						break
					else:
						# append a new link with empty elevations
						newUpLinkIds.append(dId)
			
			# check downstream
			downElev = endElevList[i]
			newDownLinkIds = [feat.id()]
			downIsEnd = False
			if isinstance(downElev, QPyNullVariant):
				#walk downstream and return a list of links to the first valid value					
				downLinkIds = self.getChainedLinks(startLink= feat,direction=1)
				downLinkIds.pop(0)
				for dId in downLinkIds:
					dIdx = idList.index(dId)
					startElev = startElevList[dIdx]
					if not isinstance(startElev, QPyNullVariant):
						#stop loop and store the elevation value and part of the list
						downElev = startElev
						downIsEnd = False
						break
					
					endElev = endElevList[dIdx]
					if not isinstance(endElev, QPyNullVariant):
						#stop loop and store the elevation value and part of the list
						downElev = endElev
						downIsEnd = True
						newDownLinkIds.append(dId)
						break
					else:
						# append a new link with empty elevations
						newDownLinkIds.append(dId)
			
			# merge the two list
			mergedIds = newUpLinkIds+newDownLinkIds
			
			totLength = 0.0
			for id in mergedIds:
				i = idList.index(id)
				totLength+= lengthList[i]
			
			# check is upElev is valid
			if isinstance(upElev, QPyNullVariant) and isinstance(downElev, QPyNullVariant):
				# undetermined condition, exiting ...
				self.progress.setInfo('undetermined condition, exiting ...', True)
				return mergedIds
				
			if isinstance(upElev, QPyNullVariant) and not isinstance(downElev, QPyNullVariant):
				upElev = downElev+totLength*slope
			
			if isinstance(downElev, QPyNullVariant) and not isinstance(upElev, QPyNullVariant):
				downElev = upElev+totLength*-slope
			
			# calculate total slope
			totSlope = (upElev-downElev)/totLength
			
			#~ print 'upElev:',upElev
			#~ print 'downElev:',downElev
			#~ print 'totLength:',totLength
			#~ print 'totSlope:',totSlope
				
			# apply the new total slope to the missing values
			upLength = 0.0
			for id in mergedIds:
				i = idList.index(id)
				# get start value
				startElev = startElevList[i]
				if isinstance(startElev, QPyNullVariant):
					startElevList[i] = upElev-upLength*totSlope
					msgList[i] += '8 (%s)'%(startElevFld)
				
				upLength+= lengthList[i]
				
				endElev = endElevList[i]
				if isinstance(endElev, QPyNullVariant):
					endElevList[i] = upElev-upLength*totSlope
					msgList[i] += '8 (%s)'%(endElevFld)
			
			
		# now you can save the results ...
		if fix: self.linksLayer.startEditing()
		
		if self.linksLayer.isEditable():
			startElevIdx = self.linksLayer.fieldNameIndex(startElevFld)
			endElevIdx = self.linksLayer.fieldNameIndex(endElevFld)
			msgIdx = self.linksLayer.fieldNameIndex('MSG')
			for i, id in enumerate(idList):
				# update attributes
				#print 'set link %s elev to %s'%(id,elevList[i])
				self.linksLayer.changeAttributeValue(id,startElevIdx,startElevList[i],True)
				self.linksLayer.changeAttributeValue(id,endElevIdx,endElevList[i],True)
				self.appendMessage(self.linksLayer,id,msgIdx,msgList[i])
				
		if fix:
			self.linksLayer.commitChanges()
			self.linksLayer.updateExtents()
			
		return []
		
	def replaceBottomElev(self,botFld,topFld,depthFld):
		self.nodesLayer.startEditing()
		
		botIdx = self.nodesLayer.fieldNameIndex(botFld)
		topIdx = self.nodesLayer.fieldNameIndex(topFld)
		depthIdx = self.nodesLayer.fieldNameIndex(depthFld)
		msgIdx = self.nodesLayer.fieldNameIndex('MSG')
		
		expr = QgsExpression( "\"%s\" is Null"%botFld)
		features = self.nodesLayer.getFeatures( QgsFeatureRequest( expr ) )
		# loop in selection
		for feat in features:
			# for each point top elevation and depth
			elev = feat.attributes()[topIdx]
			depth = feat.attributes()[depthIdx]
			# assign estimated elevation to point
			self.nodesLayer.changeAttributeValue(feat.id(),botIdx,elev-depth,True)
			self.appendMessage(self.nodesLayer,feat,msgIdx,'7')
		
		#save and update layer
		self.nodesLayer.commitChanges()
		self.nodesLayer.updateExtents()
		
	
	def getElevValues(self,linkElevFld,linknodeFld,nodeElevFld,nodeFld):
		#print linkElevFld,linknodeFld,nodeElevFld,nodeFld
		linkElevIdx = self.linksLayer.fieldNameIndex(linkElevFld)
		linknodeIdx = self.linksLayer.fieldNameIndex(linknodeFld)
		nodeElevIdx = self.nodesLayer.fieldNameIndex(nodeElevFld)
		nodeIdx = self.nodesLayer.fieldNameIndex(nodeFld)
		
		#print 'linknodeIdx:',linknodeIdx
		
		# select links with empty elevation values
		query =  "\"%s\" is Null"%linkElevFld
		#print query
		expr = QgsExpression(query)
		links = self.linksLayer.getFeatures( QgsFeatureRequest( expr ) )
		linkIds = []
		linknodeIds = []
		# loop in selection and make link id list
		for link in links:
			# get the link id
			linkIds.append(link)
			# get link node id
			linknodeIds.append(link.attributes()[linknodeIdx])
			
		# loop in the list and get node value
		nodeElevs =[]
		
		for i, linknodeId in enumerate(linknodeIds):
			# select node in node layer
			query = "\"%s\" LIKE '%s'"%(nodeFld,linknodeId)
			#print query
			expr = QgsExpression(query)
			nodes = self.nodesLayer.getFeatures( QgsFeatureRequest( expr ) )
			for node in nodes:
				# get elevation for node
				nodeElevs.append(node.attributes()[nodeElevIdx])
				break
			
			
		#linkIds = [5]
		#nodeElevs = [-9999]
		
		return linkIds,nodeElevs
		
	def replaceLinkElevations(self,linkElevFld,linkIds,nodeElevs):
		linkElevIdx = self.linksLayer.fieldNameIndex(linkElevFld)
		
		msgIdx = self.linksLayer.fieldNameIndex('MSG')
		
		self.linksLayer.startEditing()
		# now update the value in the link table
		for i, linkId in enumerate(linkIds):
			# update elevation for the link
			self.linksLayer.changeAttributeValue(linkId.id(),linkElevIdx,nodeElevs[i],True)
			self.appendMessage(self.linksLayer,linkId,msgIdx,'8(%s)'%linkElevFld)
			pass
			
		#save and update layer
		self.linksLayer.commitChanges()
		self.linksLayer.updateExtents()
	
	def findDuplicates(self,layer, fix = False):
		self.progress.setInfo('Processing layer %s ...'%(layer.name()), error = False)
		geomList = []
		idList = []
		rowList = []
		i = 0
		nfeat = layer.featureCount() 
		for feature in layer.getFeatures():
			geomList.append(feature.geometry().exportToWkt())
			idList.append(feature.id())
			rowList.append(i)
			i+=1
		
		elemsToRemove = []
		for i,geom1 in enumerate(geomList):
			for j in range(i+1,len(geomList)):
				geom2 = geomList[j]
				if geom1 == geom2:
					self.progress.setInfo('<a href="find;%s;%s">Feature %s</a> <row id: %s> is equal to %s <row id: %s> in %s'%(layer.id(),idList[i],idList[i],rowList[i],idList[j],rowList[j],layer.name()), error = True)
					elemsToRemove.append(idList[j])
					
		if fix: layer.startEditing()
					
		if layer.isEditable():
			for id in elemsToRemove:
				layer.deleteFeature(id)
				
		if fix:
			layer.commitChanges()
			layer.updateExtents()
					
	def checkElevation(self):
		for node in self.nodesLayer.getFeatures():
			objId = node['OBJ_ID']
			elevTop = node['ELEV_TOP']
			elevBot = node['ELEV_BOT']
			# search for drained links
			request = QgsFeatureRequest().setFilterExpression( u'"NODE_START" = \'%s\''%(objId) )
			linkElev = []
			linkId = []
			for link in  self.linksLayer.getFeatures( request ):
				elev = link['ELEV_START']
				diam = link['DIAM']
				if isinstance(diam, QPyNullVariant): diam = link['DIM1']
				
				if elev<elevBot:
					self.progress.setInfo('Insertion mismatch at the START of the link %s and <a href="find;%s;%s">node %s</a>: ELEV_START = %s, ELEV_BOT = %s'\
													%(link['OBJ_ID'], self.nodesLayer.id(),node.id(),node['OBJ_ID'],elev,elevBot), error = True)
				if (elev+diam)>elevTop:
					self.progress.setInfo('Insertion mismatch at the START of the link %s and <a href="find;%s;%s">node %s</a>: ELEV_START = %s, DIAM = %s, ELEV_TOP = %s'\
													%(link['OBJ_ID'],self.nodesLayer.id(),node.id(),node['OBJ_ID'],elev,diam,elevTop), error = True)
					
			# search for draining links
			request = QgsFeatureRequest().setFilterExpression( u'"NODE_END" = \'%s\''%(objId) )
			for link in  self.linksLayer.getFeatures( request ):
				elev = link['ELEV_END']
				diam = link['DIAM']
				if isinstance(diam, QPyNullVariant): diam = link['DIM1']
														
				if elev<elevBot:
					self.progress.setInfo('Insertion mismatch at the END of the link %s and <a href="find;%s;%s">node %s</a>: ELEV_END = %s, ELEV_BOT = %s'\
													%(link['OBJ_ID'],self.nodesLayer.id(),node.id(),node['OBJ_ID'],elev,elevBot), error = True)
				if (elev+diam)>elevTop:
					self.progress.setInfo('Insertion mismatch at the END of the link %s and <a href="find;%s;%s">node %s</a>: ELEV_END = %s, DIAM = %s, ELEV_TOP = %s'\
													%(link['OBJ_ID'],self.nodesLayer.id(),node.id(),node['OBJ_ID'],elev,diam,elevTop), error = True)
													

	def fixElevBot(self,elevFld = 'ELEV_BOT',fix = False ):
		elevIdx = self.nodesLayer.fieldNameIndex(elevFld)
		msgIdx = self.nodesLayer.fieldNameIndex('MSG')
		
		idList = []
		elevList = []
		msgList = []
		
		i = 0
		for node in self.nodesLayer.getFeatures():
			objId = node['OBJ_ID']
			elevBot = node[elevFld]
			#print 'testing id:',objId,'elev:', elevBot
			
			if isinstance(elevBot, QPyNullVariant): tElevBot = 100000
			else: tElevBot = elevBot
			
			newElev = tElevBot
			# search for drained links
			request = QgsFeatureRequest().setFilterExpression( u'"NODE_START" = \'%s\''%(objId) )
			for link in  self.linksLayer.getFeatures( request ):
				elev = link['ELEV_START']
				if elev<newElev:
					newElev = elev
					
			# search for draining links
			request = QgsFeatureRequest().setFilterExpression( u'"NODE_END" = \'%s\''%(objId) )
			for link in  self.linksLayer.getFeatures( request ):
				elev = link['ELEV_END']
				if elev<newElev:
					newElev = elev
			
			if newElev == 100000:
				# no in/out links
				self.progress.setInfo('Isolated <a href="find;%s;%s">node %s</a>. Check network topology'%(self.nodesLayer.id(),node.id(),objId), error = True)
				continue
					
			# update ELEV_BOT
			if newElev < elevBot:
				self.progress.setInfo('Lower elevation value at <a href="find;%s;%s">node %s</a> <row id: %s> will be replaced to %s instead of %s'\
												%(self.nodesLayer.id(),node.id(),node['OBJ_ID'],i,newElev,elevBot), error = True)
				
				idList.append(node.id())
				elevList.append(newElev)
				msgList.append('10(%s)'%elevFld)
			
			i+=1
			
		if fix:
			self.nodesLayer.startEditing()
		
		if self.nodesLayer.isEditable():
			for i, id in enumerate(idList):
				# update attributes
				self.progress.setInfo('set bottom elevation of <a href="find;%s;%s">node %s</a> to %s'%(self.nodesLayer.id(),id,id,elevList[i]), error = False)
				#print 'set bottom elevation of node %s to %s'%(id,elevList[i])
				self.nodesLayer.changeAttributeValue(id,elevIdx,elevList[i],True)
				self.appendMessage(self.nodesLayer,id,msgIdx,msgList[i])
				
		
		if fix:
			self.nodesLayer.commitChanges()
			self.nodesLayer.updateExtents()
					
	def checkElevTop(self,elevFld = 'ELEV_TOP', elevOffset = 0.5, fix = False ):
		from math import atan,cos
		elevIdx = self.nodesLayer.fieldNameIndex(elevFld)
		msgIdx = self.nodesLayer.fieldNameIndex('MSG')
		
		idList = []
		objList = []
		elevList = []
		msgList = []
	
		for node in self.nodesLayer.getFeatures():
			id = node.id()
			objId = node['OBJ_ID']
			elevTop = node[elevFld]

			#check if it is enought!
			# search for drained links
			request = QgsFeatureRequest().setFilterExpression( u'"NODE_START" = \'%s\''%(objId) )
			eList = []
			for link in  self.linksLayer.getFeatures( request ):
				elev = link['ELEV_START']
				elev2 = link['ELEV_END']
				length = link['LENGTH']
				slp = (elev-elev2)/length
				angle = atan(slp)
				diam = self.getRefDimension(link)
				diamAdj = diam/cos(angle)
				if diam is not None: eList.append(elev+diamAdj)
					
			# search for draining links
			request = QgsFeatureRequest().setFilterExpression( u'"NODE_END" = \'%s\''%(objId) )
			for link in  self.linksLayer.getFeatures( request ):
				elev = link['ELEV_END']
				elev2 = link['ELEV_END']
				length = link['LENGTH']
				slp = (elev-elev2)/length
				angle = atan(slp)
				diam = self.getRefDimension(link)
				diamAdj = diam/cos(angle)
				if diam is not None: eList.append(elev+diamAdj)
		
			if len(eList)>0: maxElev = max(eList)
			else:
				# no in/out links
				self.progress.setInfo('Isolated <a href="find;%s;%s">node %s</a>. Check network topology'%(self.nodesLayer.id(),node.id(),objId), error = True)
				maxElev = elevTop
				continue
			
			if isinstance(elevTop, QPyNullVariant):
				idList.append(id)
				objList.append(objId)
				elevList.append(maxElev)
				#msgList.append('Top elevation should be greater than %s instead of'%maxElev)
				msgList.append('11 (%s)'%elevFld)
				self.progress.setInfo('Top elevation of <a href="find;%s;%s">node %s</a> should be greater than %s instead of %s'%(self.nodesLayer.id(),node.id(),objId,maxElev,'NULL'), error = True)
			elif maxElev>elevTop:
				idList.append(id)
				objList.append(objId)
				elevList.append(maxElev)
				#msgList.append('Top elevation should be greater than %s instead of'%maxElev)
				msgList.append('11 (%s)'%elevFld)
				self.progress.setInfo('Top elevation of <a href="find;%s;%s">node %s</a> should be greater than %s instead of %s'%(self.nodesLayer.id(),node.id(),objId,maxElev,elevTop), error = True)
			else:
				pass
						
		#~ for i, id in enumerate(idList):
			#~ self.progress.setInfo('%s %s for node %s'%(msgList[i],elevList[i],id), error = True)
			
		if fix: self.nodesLayer.startEditing()
		
		if self.nodesLayer.isEditable():
			for i, id in enumerate(idList):
				# update attributes
				self.progress.setInfo('set top elevation of <a href="find;%s;%s">node %s</a> to %s'%(self.nodesLayer.id(),id,objList[i],elevList[i]+float(elevOffset)), error = False)
				#print 'set bottom elevation of node %s to %s'%(id,elevList[i])
				self.nodesLayer.changeAttributeValue(id,elevIdx,elevList[i]+float(elevOffset),True)
				self.appendMessage(self.nodesLayer,id,msgIdx,msgList[i])
		
		if fix:
			self.nodesLayer.commitChanges()
			self.nodesLayer.updateExtents()
					
	def getNodeByLink(self,link,idFld):
		objId = link[idFld]
		request = QgsFeatureRequest().setFilterExpression( u'"OBJ_ID" = \'%s\''%(objId) )
		for node in  self.nodesLayer.getFeatures( request ):
			res = node
			break # there should be only one node for each line edge
			
		return res
					
	def getLinkByNode(self,node,idFld):
		res=[]
		objId = node['OBJ_ID']
		request = QgsFeatureRequest().setFilterExpression( u'"%s" = \'%s\''%(idFld,objId) )
		for link in  self.linksLayer.getFeatures( request ):
			res.append(link)
			
		return res
		
	def getNodeValueById(self,objId,valueFld):
		res = []
		request = QgsFeatureRequest().setFilterExpression( u'"OBJ_ID" = \'%s\''%(objId) )
		for node in  self.nodesLayer.getFeatures( request ):
			res.append(node[valueFld])
			
		return res
		