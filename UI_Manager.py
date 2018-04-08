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
from VisualizationTabWidget import Ui_VisualizationTabWidget
from BreakTabWidget import Ui_BreakTabWidget
from SplitTabWidget import Ui_SplitTabWidget

import test_glviewer as tgl
from GLObjects import MetaGraphGL, Colorization

from MetaGraphThread import MetaGraphThread
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
import types

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
        

class VisualizationTabWidget(Ui_VisualizationTabWidget, QObject):

    lowColorChanged = pyqtSignal(object, object, object)
    highColorChanged = pyqtSignal(object, object, object)

    viewSkeleton = pyqtSignal(bool)
    viewGraph = pyqtSignal(bool)
    viewBoth = pyqtSignal(bool)

    @pyqtSlot(int)
    def edgeColorizationChanged(self, optionId : int):
        if optionId == 0: #thickness
            self.graph.colorizeThickness()
            pass
        elif optionId == 1: #width
            self.graph.colorizeWidth()
            pass
        elif optionId == 2: #thickness / width
            self.graph.colorizeRatio()
            pass
        elif optionId ==3 : #component
            self.graph.colorizeComponents()
            pass


    @pyqtSlot(int)
    def nodeColorizationChanged(self, optionId : int):
        if optionId == 0: #thickness
            self.graph.nodeColorization = Colorization.THICKNESS
            pass
        elif optionId == 1: #width
            self.graph.nodeColorization = Colorization.WIDTH
            pass
        elif optionId == 2: #degree
            self.graph.nodeColorization = Colorization.DEGREE
            pass
        elif optionId ==3 : #component
            self.graph.nodeColorization = Colorization.COMPONENTS
            pass


    @pyqtSlot(int)
    def geometryVisualizationChanged(self, optionId : int):
        if optionId == 0: #skeleton
            self.viewSkeleton.emit(True)
            pass
        elif optionId == 1: #graph
            self.viewGraph.emit(True)
            pass
        elif optionId == 2: #both
            self.viewBoth.emit(True)
            pass


    @pyqtSlot(bool)
    def enteringSkelView(self, val : bool):
        self.geometryVisualization.currentIndexChanged.disconnect(self.geometryVisualizationChanged)
        self.geometryVisualization.setCurrentIndex(0)
        self.geometryVisualization.currentIndexChanged.connect(self.geometryVisualizationChanged)


    @pyqtSlot(bool)
    def enteringGraphView(self, val : bool):
        self.geometryVisualization.currentIndexChanged.disconnect(self.geometryVisualizationChanged)
        self.geometryVisualization.setCurrentIndex(1)
        self.geometryVisualization.currentIndexChanged.connect(self.geometryVisualizationChanged)




    @pyqtSlot(bool)
    def enteringBothView(self, val : bool):
        self.geometryVisualization.currentIndexChanged.disconnect(self.geometryVisualizationChanged)
        self.geometryVisualization.setCurrentIndex(2)
        self.geometryVisualization.currentIndexChanged.connect(self.geometryVisualizationChanged)



    def __init__(self, widget, graphObject : MetaGraphGL, viewSkeletonButton, viewGraphButton, viewBothButton):
        Ui_VisualizationTabWidget.__init__(self)
        QObject.__init__(self)
        self.setupUi(widget)
        self.widget = widget
        self.graph = graphObject

        self.lowColor = QColor(Qt.blue)
        self.highColor = QColor(Qt.red)

        self.lowColorButton.setAutoFillBackground(True)
        self.highColorButton.setAutoFillBackground(True)

        self.setLowColor(self.lowColor)
        self.setHighColor(self.highColor)

        self.lowColorButton.clicked.connect(self.pickLowColor)
        self.highColorButton.clicked.connect(self.pickHighColor)

        self.edgeColorizationOptions = {}
        self.edgeColorizationOptions[0] = "by Thickness"
        self.edgeColorizationOptions[1] = "by Width"
        self.edgeColorizationOptions[2] = "by Thickness/Width"
        self.edgeColorizationOptions[3] = "by Component"

        self.nodeColorizationOptions = {}
        self.nodeColorizationOptions[0] = "by Thickness"
        self.nodeColorizationOptions[1] = "by Width"
        self.nodeColorizationOptions[2] = "by Degree"
        self.nodeColorizationOptions[3] = "by Component"


        self.geometryVisualizationOptions = {}
        self.geometryVisualizationOptions[0] = "View Skeleton"
        self.geometryVisualizationOptions[1] = "View MetaGraph"
        self.geometryVisualizationOptions[2] = "View Both"

        for key in self.edgeColorizationOptions:
            self.edgeColorization.addItem(self.edgeColorizationOptions[key])

        for key in self.nodeColorizationOptions:
            self.nodeColorization.addItem(self.nodeColorizationOptions[key])
        
        for key in self.geometryVisualizationOptions:
            self.geometryVisualization.addItem(self.geometryVisualizationOptions[key])


        self.edgeColorization.currentIndexChanged.connect(self.edgeColorizationChanged)
        self.nodeColorization.currentIndexChanged.connect(self.nodeColorizationChanged)
        self.geometryVisualization.currentIndexChanged.connect(self.geometryVisualizationChanged)

        self.viewGraph.connect(viewGraphButton.trigger)
        graphObject.enteringGraphView.connect(self.enteringGraphView)

        self.viewSkeleton.connect(viewSkeletonButton.trigger)
        graphObject.enteringSkeletonView.connect(self.enteringSkelView)

        self.viewBoth.connect(viewBothButton.trigger)
        graphObject.enteringBothView.connect(self.enteringBothView)

       
        self.lowColorChanged.connect(graphObject.lowColorChanged)
        self.highColorChanged.connect(graphObject.highColorChanged)

        self.lowColorChanged.emit(self.lowColor.redF(), self.lowColor.greenF(), self.lowColor.blueF())
        self.highColorChanged.emit(self.highColor.redF(), self.highColor.greenF(), self.highColor.blueF())

        self.graph.colorizeThickness()
        self.viewSkeleton.emit(True)


    @pyqtSlot(bool)
    def pickLowColor(self, someBool):
        pickedColor = QColorDialog.getColor(self.lowColor, self.widget)
        self.setLowColor(pickedColor)

    @pyqtSlot(bool)
    def pickHighColor(self, someBool):
        pickedColor = QColorDialog.getColor(self.highColor, self.widget)
        self.setHighColor(pickedColor)

    @pyqtSlot(QColor)
    def setLowColor(self, lowColor : QColor):
        self.lowColor = lowColor
        
        lowColorHSL = self.lowColor.toHsl()
        lowLightness = lowColorHSL.lightnessF()
        lowTextColor = QColor(Qt.black)
        if lowLightness < 0.1791:
            lowTextColor = QColor(Qt.white)


        self.lowColorButton.setStyleSheet( "background-color: " + self.lowColor.name() + "; color:" + lowTextColor.name())
        self.lowColorButton.update()
        self.lowColorChanged.emit(self.lowColor.redF(), self.lowColor.greenF(), self.lowColor.blueF())

    @pyqtSlot(QColor)
    def setHighColor(self, highColor : QColor):
        self.highColor = highColor

        highColorHSL = self.highColor.toHsl()
        highLightness = highColorHSL.lightnessF()
        highTextColor = QColor(Qt.black)
        if highLightness < 0.1791:
            highTextColor = QColor(Qt.white)

        
        self.highColorButton.setStyleSheet( "background-color: " + self.highColor.name() + "; color:" + highTextColor.name())
        self.highColorButton.update()

        self.highColorChanged.emit(self.highColor.redF(), self.highColor.greenF(), self.highColor.blueF())

class BreakTabWidget(Ui_BreakTabWidget, QObject):
    def __init__(self, widget=None):
        Ui_BreakTabWidget.__init__(self)
        QObject.__init__(self)
        self.setupUi(widget)
        self.widget = widget

class SplitTabWidget(Ui_SplitTabWidget, QObject):
    def __init__(self, widget=None):
        Ui_SplitTabWidget.__init__(self)
        QObject.__init__(self)
        self.setupUi(widget)

        self.widget = widget

        

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
        
    @pyqtSlot()
    def acceptPressed(self):
        print('accept pressed')

    def __init__(self, parent = None):
        super(RootsTabbedProgram, self).__init__(parent)
        
        #self.metaThread = MetaGraphThread()
        #self.metaThread.wasNotified.connect(self.notifyConfirmed)
        #self.metaThread.wasTerminated.connect(self.terminateConfirmed)
        #self.metaThread.start()
        
        self.currentMode = -2
        
        self.glwidget = tgl.GLWidget(self)
        self.dockedWidget = None
        self.__setUI()
        
        
    def __setUI(self, title="RootsEditor"):
        self.mainMenu = self.menuBar()
        
        self.mainMenu.setNativeMenuBar(False)
        self.fileMenu = self.mainMenu.addMenu('File')
        
        loadButton = QAction('Load rootfile', self)
        loadButton.setShortcut('Ctrl+L')
        loadButton.setShortcutContext(Qt.ApplicationShortcut)
        loadButton.setStatusTip('Load rootfile or skeleton')
        loadButton.triggered.connect(self.loadFile)
        self.fileMenu.addAction(loadButton)
        
        
        exitButton = QAction('Exit', self)
        exitButton.setShortcut('Ctrl+E')
        exitButton.setShortcutContext(Qt.ApplicationShortcut)
        exitButton.setStatusTip('Exit RootsEditor')
        exitButton.triggered.connect(self.close)
        self.fileMenu.addAction(exitButton)
        
        self.modeMenu = self.mainMenu.addMenu('Mode')
        
        connectionModeButton = QAction('Connection', self)
        connectionModeButton.setShortcut('Ctrl+C')
        connectionModeButton.setShortcutContext(Qt.ApplicationShortcut)
        connectionModeButton.setStatusTip('Connect broken components')
        connectionModeButton.triggered.connect(self.enterConnectionMode)
        self.modeMenu.addAction(connectionModeButton)
        
        breakModeButton = QAction('Break', self)
        breakModeButton.setShortcut('Ctrl+B')
        breakModeButton.setShortcutContext(Qt.ApplicationShortcut)
        breakModeButton.setStatusTip('Break invalid edges')
        breakModeButton.triggered.connect(self.enterBreakMode)
        self.modeMenu.addAction(breakModeButton)
        
        
        splitModeButton = QAction('Split', self)
        splitModeButton.setShortcut('Ctrl+X')
        splitModeButton.setShortcutContext(Qt.ApplicationShortcut)
        splitModeButton.setStatusTip('Split edges between two branches that have merged')
        splitModeButton.triggered.connect(self.enterSplitMode)
        self.modeMenu.addAction(splitModeButton)


        self.viewMenu = self.mainMenu.addMenu('View Mode')

        viewGraphButton = QAction('MetaGraph', self)
        viewGraphButton.setShortcut('Ctrl+G')
        viewGraphButton.setShortcutContext(Qt.ApplicationShortcut)
        viewGraphButton.setStatusTip('View the metagpraph only')
        viewGraphButton.triggered.connect(self.glwidget.metaGL.enterGraphView)
        self.viewMenu.addAction(viewGraphButton)

        viewSkeletonButton = QAction('Skeleton', self)
        viewSkeletonButton.setShortcut('Ctrl+R')
        viewSkeletonButton.setShortcutContext(Qt.ApplicationShortcut)
        viewSkeletonButton.setStatusTip('View the skeleton only')
        viewSkeletonButton.triggered.connect(self.glwidget.metaGL.enterSkeletonView)
        self.viewMenu.addAction(viewSkeletonButton)

        viewBothButton = QAction('Both', self)
        viewBothButton.setShortcut('Ctrl+D')
        viewBothButton.setShortcutContext(Qt.ApplicationShortcut)
        viewBothButton.setStatusTip('View metagraph and skeleton simultaneously')
        viewBothButton.triggered.connect(self.glwidget.metaGL.enterBothView)
        self.viewMenu.addAction(viewBothButton)


        recenterButton = QAction('Recenter', self)
        recenterButton.setShortcut('Ctrl+F')
        recenterButton.setShortcutContext(Qt.ApplicationShortcut)
        recenterButton.setStatusTip('Recenter view on skeleton')
        recenterButton.triggered.connect(self.glwidget.recenter)
        self.viewMenu.addAction(recenterButton)


        acceptShortcut = QAction('Accept Operation', self)
        acceptShortcut.setShortcut('Ctrl+A')
        acceptShortcut.setShortcutContext(Qt.ApplicationShortcut)
        acceptShortcut.triggered.connect(self.glwidget.metaGL.connectionOptions.acceptConnection)
        acceptShortcut.triggered.connect(self.glwidget.metaGL.breakOptions.acceptBreak)
        acceptShortcut.triggered.connect(self.glwidget.metaGL.splitOptions.acceptSplit)
        acceptShortcut.triggered.connect(self.acceptPressed)
        self.addAction(acceptShortcut)
        

        centralWidget = QtWidgets.QWidget()

        self.setCentralWidget(centralWidget)
        centralLayout = QtWidgets.QGridLayout()
        centralLayout.addWidget(self.glwidget, 1, 1)
        centralWidget.setLayout(centralLayout)
        centralWidget.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.glwidget.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.glwidget.setMinimumSize(800, 500)
        

        
        
        #notifyButton = QAction('Notify', self)
        #notifyButton.setShortcut('Ctrl+N')
        #notifyButton.triggered.connect(self.metaThread.notify)
        #self.modeMenu.addAction(notifyButton)
        
        #terminateButton = QAction('Terminate', self)
        #terminateButton.setShortcut('Ctrl+T')
        #terminateButton.triggered.connect(self.metaThread.terminate)
        #self.modeMenu.addAction(terminateButton)
        
        
        w = 1300
        h = 800
        self.resize(w, h)
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setWindowTitle('Skeleton Viewer')
        self.dockedWidget = None
        self.viewWidget = None

        dock = QDockWidget('Visualization Tab', self)
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        dockWidget = QWidget()
        VisualizationTab = VisualizationTabWidget(dockWidget, self.glwidget.metaGL, viewSkeletonButton, viewGraphButton, viewBothButton)
        
        
        
        

        self.VisualizationTab = VisualizationTab

        dock.setWidget(dockWidget)
        dock.setTitleBarWidget(QWidget())
        
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        self.visualizationDock = dock
        
        
    def enterConnectionMode(self):
        if self.currentMode == 0 or self.currentMode == -2:
            return
        self.currentMode = 0
        self.closeDockWidget()
        dock = QDockWidget('Connection Tab', self)
        dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        dockWidget = QWidget()
        ConnectionTab = ConnectionTabWidget(dockWidget)

        dock.setWidget(dockWidget)
        dock.setTitleBarWidget(QWidget())
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        self.glwidget.enterConnectionMode(ConnectionTab)
        self.dockedWidget = dock

    
    def enterBreakMode(self):
        if self.currentMode == 1 or self.currentMode == -2:
            return
        self.closeDockWidget()
        self.currentMode = 1

        self.closeDockWidget()
        dock = QDockWidget('Break Tab', self)
        dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        dockWidget = QWidget()
        BreakTab = BreakTabWidget(dockWidget)

        dock.setWidget(dockWidget)
        dock.setTitleBarWidget(QWidget())
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        self.glwidget.enterBreakMode(BreakTab)
        self.dockedWidget = dock
        
    def enterSplitMode(self):
        if self.currentMode == 2 or self.currentMode == -2:
            return
        self.closeDockWidget()
        self.currentMode = 2

        self.closeDockWidget()
        dock = QDockWidget('Connection Tab', self)
        dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        dockWidget = QWidget()
        SplitTab = SplitTabWidget(dockWidget)

        dock.setWidget(dockWidget)
        dock.setTitleBarWidget(QWidget())
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        self.glwidget.enterSplitMode(SplitTab)
        self.dockedWidget = dock

    
    def eventFilter(self, obj, event):
        return False

    def closeDockWidget(self):
        print('closing dock widget')
        if self.dockedWidget != None:
            print('dock widget is not none')
            self.dockedWidget.hide()
            self.dockedWidget.destroy()

    
    
        
    def loadFile(self):
        options = QFileDialog.Options()
        
        options |= QFileDialog.DontUseNativeDialog
        self.loadFileName = QFileDialog.getOpenFileName(self, 'Open File', "")
#        qDebug(str(self.loadFileName[0]))
        
        if self.loadFileName[0] != "":
            self.glwidget.loadFileEvent(str(self.loadFileName[0]))
            self.currentMode = -1
            #self.metaThread.loadFileEvent(str(self.loadFileName[0]))



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RootsTabbedProgram()
    window.show()
#    dialog = QDialog()
#    prog = RootsGUI(dialog)
    
#    dialog.show()
    sys.exit(app.exec_())
