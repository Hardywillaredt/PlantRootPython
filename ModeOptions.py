# -*- coding: utf-8 -*-
"""
Created on Tue Mar 13 21:07:56 2018

@author: Will
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

from ConnectionTabWidget import Ui_ConnectionTabWidget

class ConnectionModeOptions():
    
    @pyqtSlot()
    def ComponentOneChanged(self, val):
        if self.component1 == val:
            return
        if self.node1 != None:
            self.nodeUnselected.emit(self.node1.order)
        self.node1 = None
        self.minimizedComponents[val] = True
        self.minimizedComponents[self.component1] = False
        self.component1 = val
        self.componentsChanged.emit(self.minimizedComponents)
    
    @pyqtSlot()
    def ComponentTwoChanged(self, val):
        if self.component2 == val:
            return
        if self.node2 != None:
            self.nodeUnselected.emit(self.node2.order)
        self.node2 = None          
        self.minimizedComponents[val] = True
        self.minimizedComponents[self.component2] = False
        self.component2 = val
        self.componentsChanged.emit(self.minimizedComponents)
                
    
    nodeSelected = pyqtSignal(int)
    
    nodeUnselected = pyqtSignal(int)
    
    componentsChanged = pyqtSignal(object)

    
    def __init__(self, numComponents : int):
        self.component1 = 0
        self.component2 = 0
        self.minimizedComponents = {}
        self.node1 = None
        self.node2 = None
        self.numComponents = numComponents
        self.widget = None
        for i in range(0, numComponents):
            if i == self.component1 or i == self.component2:
                self.minimizedComponents[i] = False
            else:
                self.minimizedComponents[i] = True
                
    def setWidget(self, widget : Ui_ConnectionTabWidget):
        self.widget = widget
        self.updateConnectionWidget()
        self.widget.ComponentOne.currentIndexChanged.connect(self.ComponentOneChanged)
        self.widget.ComponentTwo.currentIndexChanged.connect(self.ComponentTwoChanged)
    
    def setNumComponents(self, numComponents : int):
        self.numComponents = numComponents
        if numComponents <= self.component1:
            self.minimizedComponents[self.component1] = False
            self.component1 = numComponents - 1
            self.minimizedComponents[self.component1] = True
            self.unselectNode1()
            self.componentsChanged.emit()
        if numComponents <= self.component2:
            self.minimizedComponents[self.component2] = False
            self.component2 = numComponents - 1
            self.minimizedComponents[self.component2] = True
            self.unselectNode2()
            self.componentsChanged.emit()
        if self.node1 != None:
            if self.node1.component != self.component1:
                self.unselectNode1()
        if self.node2 != None:
            if self.node2.component != self.component2:
                self.unselectNode2
        self.updateConnectionWidget()
    
    def updateConnectionWidget(self):
        if self.widget == None:
            return
        self.widget.ComponentOne.clear()
        self.widget.ComponentTwo.clear()
        
        for i in range(0, self.numComponents):
            self.widget.ComponentOne.addItem(str(i))
            self.widget.ComponentTwo.addItem(str(i))
            
        self.widget.ComponentOne.setCurrentIndex(self.component1)
        self.widget.ComponentTwo.setCurrentIndex(self.component2)
        
    def pickConnectionNode(self, node):
        if node.component == self.component1:
            self.unselectNode1()
            self.node1 = node
            self.nodeSelected.emit(self.node1.order)
        elif node.component == self.component2:
            self.unselectNode2()
            self.node2 = node
            self.nodeSelected.emit(self.node2.order)
        
    def unselectNode1(self):
        if self.node1 != None:
            self.nodeUnselected.emit(self.node1.order)
            self.node1 = None
        
    def unselectNode2(self):
        if self.node2 != None:
            self.nodeUnselected.emit(self.node2.order)
            self.node2 = None
            
    
            
    def acceptConnection(self):
        self.unselectNode1()
        self.unselectNode2()
        
    def exitMode(self):
        self.unselectNode1()
        self.unselectNode2()
    
    
    def enterMode(self, numComponents : int, widget : Ui_ConnectionTabWidget):
        self.setNumComponents(numComponents)
        self.setConnectionWidget(widget)

class BreakModeOptions():
    
    edgeSelected = pyqtSignal(object)
    
    edgeUnselected = pyqtSignal(object)
    
    def __init__(self):
        self.breakEdge = None
        self.widget = None
        
    def setWidget(self, widget):
        self.widget = widget
        self.updateWidget()
        
    def updateWidget(self):
        p = 3
        
    def selectBreakEdge(self, edge):
        self.unselectBreakEdge()
        self.breakEdge = edge
        self.edgeSelected.emit(self.breakEdge)
        
        
    def unselectBreakEdge(self):
        if self.breakEdge != None:
            self.edgeUnselected.emit(self.breakEdge)
            self.breakEdge = None
                                     
    
    
            
                