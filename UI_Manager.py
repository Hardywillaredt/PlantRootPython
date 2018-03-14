# -*- coding: utf-8 -*-
"""
Created on Tue Nov 28 02:48:14 2017

@author: Will
"""

from RootsTool import  Point3d, RootAttributes, Skeleton, MetaNode3d, MetaEdge3d, MetaGraph

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtWidgets
from SkeletonViewer import *

import sys
from RootsUI import Ui_RootsUI
from ConnectionTabWidget import Ui_ConnectionTabWidget

import test_glviewer as tgl

from MetaGraphThread import MetaGraphThread
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

#class RootsGUI(Ui_RootsUI):
#    def __init__(self, dialog):
#        Ui_RootsUI.__init__(self)
#        self.setupUi(dialog)
#        self.dlg = dialog
#        self.LoadFile.clicked.connect(self.PickFile)
##        layout = self.GLWidgetHolder.layout
#        layout = QVBoxLayout(self.GLWidgetHolder)
#        layout.addStretch(1)
#        self.GLView = tgl.GLWidget()
##        self.GLView = SkeletonViewer()
#        layout.addChildWidget(self.GLView)
#        
#        self.GLWidgetHolder.setLayout(layout)
#        self.GLWidgetHolder.show()
#        #self.GLView = SkeletonViewer(self.GLWidgetHolder)
#        
#    def PickFile(self):
#        options = QFileDialog.Options()
#        
#        options |= QFileDialog.DontUseNativeDialog
#        self.loadFileName = QFileDialog.getOpenFileName(self.dlg, 'Open File', "")
#        qDebug(str(self.loadFileName[0]))
#        self.LoadSkeleton(str(self.loadFileName[0]))
#        
#    def LoadSkeleton(self, filename):
#        self.skeleton = Skeleton(filename)
#        self.GLView.setSkeleton(self.skeleton)

class ConnectionTabWidget(Ui_ConnectionTabWidget):
    def __init__(self, widget=None):
        Ui_ConnectionTabWidget.__init__(self)
        self.setupUi(widget)
        

class RootsTabbedProgram(QMainWindow):
    
    @pyqtSlot()
    def notifyConfirmed(self):
        print('Notify confirmed')
        
    @pyqtSlot()
    def terminateConfirmed(self):
        print('Terminate confirmed')
        
    @pyqtSlot()
    def mainPrint(self, toPrint : object):
        print(toPrint)
        
    def __init__(self):
        QMainWindow.__init__(self)
        
        self.metaThread = MetaGraphThread()
        self.metaThread.wasNotified.connect(self.notifyConfirmed)
        self.metaThread.wasTerminated.connect(self.terminateConfirmed)
        self.metaThread.printToMain.connect(self.mainPrint)
        self.metaThread.start()
        
        
        self.SkelViewer = tgl.GLWidget()
        self.SkelViewer.setMetaThread(self.metaThread)
        self.__setUI()
        
        
    def __setUI(self, title="RootsEditor"):
        self.mainMenu = self.menuBar()
        
        self.mainMenu.setNativeMenuBar(False)
        self.fileMenu = self.mainMenu.addMenu('File')
        
        loadButton = QAction('Load rootfile', self)
        loadButton.setShortcut('Ctrl+L')
        loadButton.setStatusTip('Load rootfile or skeleton')
        loadButton.triggered.connect(self.loadFile)
        self.fileMenu.addAction(loadButton)
        
        
        exitButton = QAction('Exit', self)
        exitButton.setShortcut('Ctrl+E')
        exitButton.setStatusTip('Exit RootsEditor')
        exitButton.triggered.connect(self.close)
        self.fileMenu.addAction(exitButton)
        
        self.modeMenu = self.mainMenu.addMenu('Mode')
        
        connectionModeButton = QAction('Connection', self)
        connectionModeButton.setShortcut('Ctrl+M')
        connectionModeButton.setStatusTip('Connect broken components')
        connectionModeButton.triggered.connect(self.enterConnectionMode)
        self.modeMenu.addAction(connectionModeButton)
        
        breakModeButton = QAction('Break', self)
        breakModeButton.setShortcut('Ctrl+B')
        breakModeButton.setStatusTip('Break invalid edges')
        breakModeButton.triggered.connect(self.enterBreakMode)
        self.modeMenu.addAction(breakModeButton)
        
        
        splitModeButton = QAction('Split', self)
        splitModeButton.setShortcut('Ctrl+X')
        splitModeButton.setStatusTip('Split edges between two branches that have merged')
        splitModeButton.triggered.connect(self.enterSplitMode)
        self.modeMenu.addAction(splitModeButton)
        
        centralWidget = QtWidgets.QWidget()

        self.setCentralWidget(centralWidget)
        centralLayout = QtWidgets.QGridLayout()
        centralLayout.addWidget(self.SkelViewer, 0, 0)
        centralWidget.setLayout(centralLayout)
        
        
        notifyButton = QAction('Notify', self)
        notifyButton.setShortcut('Ctrl+N')
        notifyButton.triggered.connect(self.metaThread.notify)
        self.modeMenu.addAction(notifyButton)
        
        terminateButton = QAction('Terminate', self)
        terminateButton.setShortcut('Ctrl+T')
        terminateButton.triggered.connect(self.metaThread.terminate)
        self.modeMenu.addAction(terminateButton)
        
        
        w = 800
        h = 800
        self.resize(w, h)
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setWindowTitle('Skeleton Viewer')
        
        
    def enterConnectionMode(self):
        dock = QDockWidget('Connection Tab', self)
        dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        dockWidget = QWidget()
        ConnectionTab = ConnectionTabWidget(dockWidget)
        
#        self.loadButton = QPushButton('Load')
#        dock2.setWidget(self.loadButton)
        dock.setWidget(dockWidget)
        dock.setTitleBarWidget(QWidget())
        newSize = QtCore.QSize()
        newSize.setWidth(self.width() + dockWidget.width())
        newSize.setHeight(self.height())
        self.resize(newSize)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        self.SkelViewer.enterConnectionMode(ConnectionTab)
    
    def enterBreakMode(self):
        self.SkelViewer.enterBreakMode()
        
    def enterSplitMode(self):
        self.SkelViewer.enterSplitMode()
    
    def eventFilter(self, obj, event):
        return False
    
    
        
    def loadFile(self):
        options = QFileDialog.Options()
        
        options |= QFileDialog.DontUseNativeDialog
        self.loadFileName = QFileDialog.getOpenFileName(self, 'Open File', "")
#        qDebug(str(self.loadFileName[0]))
        
        if self.loadFileName != "":
            self.metaThread.loadFileEvent(str(self.loadFileName[0]))
            '''
            print("Loading metagraph from file", self.loadFileName)
            self.graph = MetaGraph(str(self.loadFileName[0]))
            print("successfully loaded metagraph")
            print("Building metagraph from skeleton")
            self.graph.initializeFromSkeleton()
            print("Succesfully build metagraph")
            print("setting metagraph to skeleton modeller")
            self.SkelViewer.setMetaGraph(self.graph)
            print("Successfully set metagraph to skeleton modeller")
            '''


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RootsTabbedProgram()
    window.show()
#    dialog = QDialog()
#    prog = RootsGUI(dialog)
    
#    dialog.show()
    sys.exit(app.exec_())
