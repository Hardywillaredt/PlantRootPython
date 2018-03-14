import sys
import math

from RootsTool import MetaGraph
from ConnectionTabWidget import Ui_ConnectionTabWidget

from PyQt5 import QtCore, QtGui, QtOpenGL, QtWidgets

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from PyQt5.QtWidgets import QMainWindow
import drawingUtil
import util


from RootsTool import  Point3d
from camera import *
from vecmath import *
import numpy as np

from typing import Union

try:
    from OpenGL.GL import *
except ImportError:
    app = QtGui.QApplication(sys.argv)
    QtGui.QMessageBox.critical(None, "OpenGL grabber",
            "PyOpenGL must be installed to run this example.")
    sys.exit(1)

from OpenGL.GLU import *
from OpenGL.GLUT import *

import SkelGL

from MetaGraphThread import MetaGraphThread

class GLWidget(QtOpenGL.QGLWidget):
    xRotationChanged = QtCore.pyqtSignal(int)
    yRotationChanged = QtCore.pyqtSignal(int)
    zRotationChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        
        self.setupInteraction()
        self.setupVis()
        self.cyls = list()

#        self.skelModel = SkelGL.SkelGL()
#        self.skelModel.timer.timeout.connect(self.timeOut)
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.timeOut)
        self.timer.start(1000)
        
        self.hasModelGL = False
        self.modelGL = None
        self.metaThread = None
        
        self.modes = {-1 : 'NoMode', 0 : 'Connection Mode', 1 : 'Separation Mode', 2 : 'Spltting Mode'}
        
        self.currentMode = -1
    
    @QtCore.pyqtSlot()
    def timeOut(self):
        if self.isWDown:
            self.camera.goForward(0.15 * 5)
        elif self.isSDown:
            self.camera.goForward(-0.15 * 5)
            
        if self.isADown:
            self.camera.goRight(-0.15 * 5)
        elif self.isDDown:
            self.camera.goRight(0.15 * 5)
        
        if self.isQDown:
            self.camera.roll(-0.01 * 5)
        elif self.isEDown:
            self.camera.roll(0.01 * 5)
        self.update()
        
        
    @QtCore.pyqtSlot()
    def updateCurrentGL(self, modelGL : object):
        print('updating current gl')
        self.modelGL = modelGL
        self.hasModelGL = True

    def setupInteraction(self):
        self.isMouseLeftDown = False
        self.isMouseRightDown = False
        self.lastMouseX = 0.0
        self.lastMouseY = 0.0
        
        self.isWDown = False
        self.isADown = False
        self.isSDown = False
        self.isDDown = False
        self.isQDown = False
        self.isEDown = False
        
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)
        
    def setupVis(self):
        self.camera = Camera()
        initialPosition = v3(0, 0, 40)
        
        self.camera.set_position(initialPosition)
        
        self.camera.look_at(v3())
        self.camera.set_near(1.0)
        self.camera.set_far(1000.0)
        fov = (60.0 / 180.0) * np.pi
        self.camera.set_fov(fov)
        w = float(self.width())
        h = float(self.height())
        self.camera.set_aspect(w/h)
        p = self.camera.get_model_matrix()
        
        self.imageCenterX = w / 2.0
        self.imageCenterY = h / 2.0
        
        
        if isinstance(p[0][0], float):
            print('isfloat')
        else:
            print('not a float')
        print('[')
        for i in range(0, 3):
            s = str(p[i][0])
            s =  s + ' ' + str(p[i][1]) + ' ' + str(p[i][2]) + ' ' + str(p[i][3])
            print(s)
        print(']')
            
    def setMetaThread(self, metaThread : MetaGraphThread):
        self.metaThread = metaThread
        self.metaThread.currentGL.connect(self.updateCurrentGL)
        
        
#    def addMetaGraph(self, graph : MetaGraph):
#        self.skelModel.setMetaGraph(graph)
#        self.camera.set_position(self.skelModel.skeletonViewBasePoint)
#        self.camera.look_at(self.skelModel.skeletonCenter)
        
    def __del__(self):
        self.makeCurrent()
        for cyl in self.cyls:
            glDeleteLists(cyl)

    def setXRotation(self, angle : float):
        self.normalizeAngle(angle)
        oAngle = angle * 2*np.pi / 5760.0
        pitch = self.camera.get_world_pitch()
        print('pitch and angle')
        print(str(pitch))
        print(str(oAngle))
        angleDif = oAngle - pitch
        self.camera.pitch(angleDif)
        if angle != self.xRot:
            self.xRot = angle
            self.xRotationChanged.emit(angle)
            self.updateGL()

    def setYRotation(self, angle : float):
        self.normalizeAngle(angle)
        oAngle = angle * 2*np.pi / 5760.0
        yaw = self.camera.get_world_yaw()
        print('yaw and angle')
        print(str(yaw))
        print(str(oAngle))
        angleDif = oAngle - yaw
        self.camera.yaw(angleDif)
        print(str(self.camera.get_world_yaw()))
        if angle != self.yRot:
            self.yRot = angle
            self.yRotationChanged.emit(angle)
            self.updateGL()

    def setZRotation(self, angle : float):
        self.normalizeAngle(angle)
        oAngle = angle * 2*np.pi / 5760.0
        roll = self.camera.get_world_roll()
        print('roll and angle')
        print(str(roll))
        print(str(oAngle))
        angleDif = oAngle - roll
        self.camera.roll(angleDif)
        if angle != self.zRot:
            self.zRot = angle
            self.zRotationChanged.emit(angle)
            self.updateGL()
        

    def initializeGL(self):
        lightPos = (1000.0, 1000.0, 1000.0, 1.0)
        lightPos2 = (-1000.0, -1000.0, 0, 1.0)
        ambientLight = (1.0, 1.0, 1.0, 1.0)
        ref = (0.5, 0.0, 0.0, 1.0)
        ref2 = (1.0, 0.0, 0.0, 1.0)
        reflectance1 = (0.8, 0.1, 0.0, 0.7)
        reflectance2 = (0.0, 0.8, 0.2, 1.0)
        reflectance3 = (0.2, 0.2, 1.0, 1.0)

#        glLightfv(GL_LIGHT0, GL_POSITION, lightPos)
#        glLightfv(GL_LIGHT1, GL_POSITION, lightPos)
#        glLightfv(GL_LIGHT0, GL_AMBIENT, ambientLight)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        self.cx = 0
        self.cy = 0
        self.cz = 0
        self.rad = 10
        rad = self.rad

        glEnable(GL_NORMALIZE)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.camera.get_fov_deg(), self.camera.get_aspect(), self.camera.get_near(), self.camera.get_far())
        glMatrixMode(GL_MODELVIEW)

#        glPushMatrix()
#        glLoadMatrixf(self.camera.get_model_matrix())
#        p = m44()
#        glGetFloatv(GL_MODELVIEW_MATRIX, p)
#        print('model matrix?')
#        print('[')
#        for i in range(0, 3):
#            s = str(p[i][0])
#            s =  s + ' ' + str(p[i][1]) + ' ' + str(p[i][2]) + ' ' + str(p[i][3])
#            print(s)
#        print(']')
#        gluLookAt(0.0, 0.0, self.rad*2, self.cx, self.cy, self.cz, 0.0, 1.0, 0.0)
#        glPopMatrix()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.camera.get_fov_deg(), self.camera.get_aspect(), self.camera.get_near(), self.camera.get_far())
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        pos = self.camera.get_position()
        at = self.camera.get_world_forward()
        lpos = pos + at
        up = self.camera.get_world_up()
        
        gluLookAt(pos[0], pos[1], pos[2], lpos[0], lpos[1], lpos[2], up[0], up[1], up[2])
        
        if self.hasModelGL:
            self.drawGear(self.modelGL, 0, 0, 0, 0)
              
        glPopMatrix()
 
        
    def resizeGL(self, width : int, height : int):
        side = min(width, height)
        
        fov = (60.0 / 180.0) * np.pi
        self.camera.set_fov(fov)
        w = float(self.width())
        h = float(self.height())
        self.camera.set_aspect(w/h)
        
        
        glViewport(0, 0, width, height)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum(-1.0, +1.0, -1.0, 1.0, 5.0, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslated(0.0, 0.0, -40.0)
        self.imageCenterX = float(width) / 2.0
        self.imageCenterY = float(height) / 2.0
        self.pitchPerY = self.camera.get_fov() / h
        self.yawPerX = self.pitchPerY



    def xRotation(self):
        return self.xRot

    def yRotation(self):
        return self.yRot

    def zRotation(self):
        return self.zRot 

    def drawGear(self, gear, dx : float, dy : float, dz : float, angle : float):
        glPushMatrix()
        glTranslated(dx, dy, dz)
        glRotated(angle, 0.0, 0.0, 1.0)
        glCallList(gear)
        glPopMatrix()

    def normalizeAngle(self, angle : float):
        while (angle < 0):
            angle += 360 * 16

        while (angle > 360 * 16):
            angle -= 360 * 16
    
    
    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()
        if self.underMouse():
            if key == Qt.Key_W:
#                print('w pressed')
                self.isWDown = True
#                self.camera.goUp(0.1)
            elif key == Qt.Key_S:
#                print('s pressed'
                self.isSDown = True
#                self.camera.goUp(-0.1)
                
            elif key == Qt.Key_A:
#                print('a pressed')
                self.isADown = True
#                self.camera.goRight(-0.1)
            elif key == Qt.Key_D:
                self.isDDown = True
#                print('d pressed')
#                self.camera.goRight(0.1)
                
            elif key == Qt.Key_Q:
#                print('q pressed')
                self.isQDown = True
#                self.camera.roll(0.05)
            elif key == Qt.Key_E:
#                print('e pressed')
                self.isEDown = True
#                self.camera.roll(-0.05)
        

        QtOpenGL.QGLWidget.keyPressEvent(self, event)
        
    
    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()
        if self.underMouse():
            if key == Qt.Key_W:
                self.isWDown = False
            elif key == Qt.Key_S:
                self.isSDown = False
                
            elif key == Qt.Key_A:
                self.isADown = False
            elif key == Qt.Key_D:
                self.isDDown = False
                
            elif key == Qt.Key_Q:
                self.isQDown = False
            elif key == Qt.Key_E:
                self.isEDown = False
                
            elif key == Qt.Key_Return:
                if self.currentMode == 0:
                    t = 1
#                    self.skelModel.AcceptConnection()
                elif self.currentMode == 1:
                    g = 3
#                    self.skelModel.AcceptBreak()
                
        QtOpenGL.QGLWidget.keyReleaseEvent(self, event)



    def mousePressEvent(self, event: QtGui.QMouseEvent):
        
        if event.button() == Qt.RightButton and not self.isMouseLeftDown:
            self.isMouseRightDown = True
            self.lastMouseX = event.x()
            self.lastMouseY = event.y()
            ray = self.getRay(event.x(), event.y())
            origin = self.camera.getNpPosition()
            self.metaThread.RayPickedEvent(origin, ray)
            '''
            if self.currentMode == 0:
                (hitFound, nodeHit, nodeHitId) = self.skelModel.getFirstNodeHit(origin, ray)
                if hitFound:
                    self.skelModel.PickConnectionNode(nodeHit)
            if self.currentMode == 1:
                (hitFound, edgeHit, edgeHitId) = self.skelModel.getFirstEdgeHit(origin, ray)
                if hitFound:
                    self.skelModel.PickBreakEdge(edgeHit)
            '''
#            print('mouse right pressed')
        elif event.button() == Qt.LeftButton and not self.isMouseRightDown:
            self.isMouseLeftDown = True
            self.lastMouseX = event.x()
            self.lastMouseY = event.y()
            ray = self.getRay(event.x(), event.y())
            origin = self.camera.getNpPosition()
#            (hitFound, edgeHit, edgeHitId) = self.skelModel.getFirstEdgeHit(origin, ray)
#            self.skelModel.highlightEdge(edgeHitId)
            '''
            if self.currentMode == -1:
                (hitFound, nodeHit, nodeHitId) = self.skelModel.getFirstNodeHit(origin, ray)
                self.skelModel.highlightNode(nodeHitId)
            '''
#            print('mouse left pressed')
        
        
    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.isMouseLeftDown:
#            print('mouse left dragged')
            difX = event.x() - self.lastMouseX
            difY = event.y() - self.lastMouseY
            
            self.camera.pitch(self.pitchPerY * difY)
            self.camera.yaw(self.yawPerX * difX)
            self.lastMouseX = event.x()
            self.lastMouseY = event.y()
            
        elif self.isMouseRightDown:
            print('mouse right dragged')
            
        if self.isMouseLeftDown or self.isMouseRightDown:
            if event.x() > self.width():
                self.lastMouseX = 0
                newPoint = self.mapToGlobal(QtCore.QPoint(0, event.y()))
                QtGui.QCursor.setPos(newPoint.x(), newPoint.y())
            elif event.x() < 0:
                self.lastMouseX = self.width()
                newPoint = self.mapToGlobal(QtCore.QPoint(self.width(), event.y()))
                QtGui.QCursor.setPos(newPoint.x(), newPoint.y())
                
            if event.y() > self.height():
                self.lastMouseY = 0
                newPoint = self.mapToGlobal(QtCore.QPoint(event.x(), 0))
                QtGui.QCursor.setPos(newPoint.x(), newPoint.y())
            if event.y() < 0:
                self.lastMouseY = self.height()
                newPoint = self.mapToGlobal(QtCore.QPoint(event.x(), self.height()))
                QtGui.QCursor.setPos(newPoint.x(), newPoint.y())
        
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == Qt.RightButton:
            self.isMouseRightDown = False
        elif event.button() == Qt.LeftButton:
            self.isMouseLeftDown = False
            
            
    def getRay(self, windowX : float, windowY : float):
        projectedX = (windowX - self.imageCenterX) / self.imageCenterX
        projectedY = (self.imageCenterY - windowY) / self.imageCenterY
        
        view = self.camera.get_world_forward()
        view = view / np.linalg.norm(view)
        
        h = np.cross(view, self.camera.get_world_up())
        h = h / np.linalg.norm(h)
        
        v = np.cross(h, view)
        v = v / np.linalg.norm(v)
        
        vLength = np.tan(self.camera.get_fov() / 2) * self.camera.get_near()
        hLength = vLength * self.camera.get_aspect()
        
        v = v * vLength
        h = h * hLength
        
        pos = self.camera.getNpPosition() + view * self.camera.get_near() + h*projectedX + v*projectedY
        
        dirVec = pos - self.camera.getNpPosition()
        
        dirVec = dirVec/ np.linalg.norm(dirVec)
        
        return dirVec
    
#    def setMetaGraph(self, graph : MetaGraph):
#        self.skelModel.setMetaGraph(graph)
#        print(self.skelModel.skeletonViewBasePoint)
#        print(self.skelModel.skeletonCenter)
#        self.camera.set_position(self.skelModel.skeletonViewBasePoint)
#        self.camera.look_at(self.skelModel.skeletonCenter)
#        
#        if self.currentMode == 0:
#            self.UpdateConnectionWidget()
            
    
    def enterConnectionMode(self, ConnectionWidget : Ui_ConnectionTabWidget):
        self.currentMode = 0
        self.connectionWidget = ConnectionWidget        
#        self.skelModel.enterConnectionMode(ConnectionWidget)
        self.connectionWidget.ComponentOne.currentIndexChanged.connect(self.ComponentOneChangeSlot)
        self.connectionWidget.ComponentTwo.currentIndexChanged.connect(self.ComponentTwoChangeSlot)
        
    def UpdateConnectionWidget(self):
        self.connectionWidget.ComponentOne.currentIndexChanged.disconnect(self.ComponentOneChangeSlot)
        self.connectionWidget.ComponentTwo.currentIndexChanged.disconnect(self.ComponentTwoChangeSlot)
#        self.skelModel.updateConnectionWidget(self.connectionWidget)
#        self.connectionWidget.ComponentOne.currentIndexChanged.connect(self.ComponentOneChangeSlot)
#        self.connectionWidget.ComponentTwo.currentIndexChanged.connect(self.ComponentTwoChangeSlot)
        
    @QtCore.pyqtSlot(int)
    def ComponentOneChangeSlot(self, val):
        p = 2
#        self.skelModel.ChangeComponentOne(int(val))
        
    @QtCore.pyqtSlot(int)
    def ComponentTwoChangeSlot(self, val):
        g = 3
#        self.skelModel.ChangeComponentTwo(int(val))
        
        
    def enterBreakMode(self):
        self.currentMode = 1
#        self.skelModel.enterBreakMode()
        
        
    def enterSplitMode(self):
        p = 3
        
#        projectedZ = -1.0
#        print('projected x', projectedX)
#        print('projected y', projectedY)
#        print('projected z', projectedZ)
#        
#        self.camera.computeProjection()
#        
#        projectedPoint = np.array([[projectedX],
#                                   [projectedY],
#                                   [projectedZ],
#                                   [1.0]])
#        
#        inverseProjection = self.camera.getInverseProjectionMat()
#        
#        unprojectedPoint = inverseProjection @ projectedPoint
#        
#        print('unprojected point', unprojectedPoint)
#        
#        dirVec = m41(unprojectedPoint[0][0],
#                     unprojectedPoint[1][0],
#                     -1,
#                     0)
#        dirVec = dirVec / np.linalg.norm(dirVec)
#        dirVec[3][0] = 1
#        
#        print('camera space vector',  dirVec)
#        camMat = self.camera.get_camera_matrix()
#        print('cam mat', camMat)
#        
#        p = camMat @ dirVec
#        
#        print('p', p)
#        
#        dirVec = v3(p[0][0],
#                     p[1][0],
#                     p[2][0])
#        
#        dirVec = dirVec - self.camera.getNpPosition()
#        
#        dirVec = dirVec / np.linalg.norm(dirVec)
#        
#        print('dirvec', dirVec)
#        
#        return dirVec
    
#    def advanceGears(self):
#        self.gear1Rot += 2 * 16
#        self.updateGL()    
        
#    def mousePressEvent(self, event : QtGui.QMouseEvent):
#        self.lastPos = event.pos()

#    def mouseMoveEvent(self, event):
#        dx = event.x() - self.lastPos.x()
#        dy = event.y() - self.lastPos.y()
#
#        if event.buttons() & QtCore.Qt.LeftButton:
#            self.setXRotation(self.xRot + 8 * dy)
#            self.setYRotation(self.yRot + 8 * dx)
#        elif event.buttons() & QtCore.Qt.RightButton:
#            self.setXRotation(self.xRot + 8 * dy)
#            self.setZRotation(self.zRot + 8 * dx)
#
#        self.lastPos = event.pos()
        
#class MainWindow(QtWidgets.QMainWindow):
#    def __init__(self):        
#        super(MainWindow, self).__init__()
#
#        centralWidget = QtWidgets.QWidget()
#        self.setCentralWidget(centralWidget)
#
#        self.glWidget = GLWidget()
#        self.pixmapLabel = QtWidgets.QLabel()
#
#        self.glWidgetArea = QtWidgets.QScrollArea()
#        self.glWidgetArea.setWidget(self.glWidget)
#        self.glWidgetArea.setWidgetResizable(True)
#        self.glWidgetArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
#        self.glWidgetArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
#        self.glWidgetArea.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
#                QtWidgets.QSizePolicy.Ignored)
#        self.glWidgetArea.setMinimumSize(50, 50)
#
#        self.pixmapLabelArea = QtWidgets.QScrollArea()
#        self.pixmapLabelArea.setWidget(self.pixmapLabel)
#        self.pixmapLabelArea.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
#                QtWidgets.QSizePolicy.Ignored)
#        self.pixmapLabelArea.setMinimumSize(50, 50)
#
#        xSlider = self.createSlider(self.glWidget.xRotationChanged,
#                self.glWidget.setXRotation)
#        ySlider = self.createSlider(self.glWidget.yRotationChanged,
#                self.glWidget.setYRotation)
#        zSlider = self.createSlider(self.glWidget.zRotationChanged,
#                self.glWidget.setZRotation)
#
#        self.createActions()
#        self.createMenus()
#
#        centralLayout = QtWidgets.QGridLayout()
#        centralLayout.addWidget(self.glWidgetArea, 0, 0)
#        centralLayout.addWidget(self.pixmapLabelArea, 0, 1)
#        centralLayout.addWidget(xSlider, 1, 0, 1, 2)
#        centralLayout.addWidget(ySlider, 2, 0, 1, 2)
#        centralLayout.addWidget(zSlider, 3, 0, 1, 2)
#        centralWidget.setLayout(centralLayout)
#
#        xSlider.setValue(0)
#        ySlider.setValue(0)
#        zSlider.setValue(0)
#
#        self.setWindowTitle("Grabber")
#        self.resize(400, 400)
#
#    def renderIntoPixmap(self):
#        size = self.getSize()
#
#        if size.isValid():
#            pixmap = self.glWidget.renderPixmap(size.width(), size.height())
#            self.setPixmap(pixmap)
#
#    def grabFrameBuffer(self):
#        image = self.glWidget.grabFrameBuffer()
#        self.setPixmap(QtGui.QPixmap.fromImage(image))
#
#    def clearPixmap(self):
#        self.setPixmap(QtGui.QPixmap())
#
#    def about(self):
#        QtGui.QMessageBox.about(self, "About Grabber",
#                "The <b>Grabber</b> example demonstrates two approaches for "
#                "rendering OpenGL into a Qt pixmap.")
#
#    def createActions(self):
#        self.renderIntoPixmapAct = QtWidgets.QAction("&Render into Pixmap...",
#                self, shortcut="Ctrl+R", triggered=self.renderIntoPixmap)
#
#        self.grabFrameBufferAct = QtWidgets.QAction("&Grab Frame Buffer", self,
#                shortcut="Ctrl+G", triggered=self.grabFrameBuffer)
#
#        self.clearPixmapAct = QtWidgets.QAction("&Clear Pixmap", self,
#                shortcut="Ctrl+L", triggered=self.clearPixmap)
#
#        self.exitAct = QtWidgets.QAction("E&xit", self, shortcut="Ctrl+Q",
#                triggered=self.close)
#
#        self.aboutAct = QtWidgets.QAction("&About", self, triggered=self.about)
#
#        self.aboutQtAct = QtWidgets.QAction("About &Qt", self,
#                triggered=QtWidgets.qApp.aboutQt)
#
#    def createMenus(self):
#        self.fileMenu = self.menuBar().addMenu("&File")
#        self.fileMenu.addAction(self.renderIntoPixmapAct)
#        self.fileMenu.addAction(self.grabFrameBufferAct)
#        self.fileMenu.addAction(self.clearPixmapAct)
#        self.fileMenu.addSeparator()
#        self.fileMenu.addAction(self.exitAct)
#
#        self.helpMenu = self.menuBar().addMenu("&Help")
#        self.helpMenu.addAction(self.aboutAct)
#        self.helpMenu.addAction(self.aboutQtAct)
#
#    def createSlider(self, changedSignal, setterSlot):
#        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
#        slider.setRange(0, 360 * 16)
#        slider.setSingleStep(16)
#        slider.setPageStep(15 * 16)
#        slider.setTickInterval(15 * 16)
#        slider.setTickPosition(QtWidgets.QSlider.TicksRight)
#
#        slider.valueChanged.connect(setterSlot)
#        changedSignal.connect(slider.setValue)
#
#        return slider
#
#    def setPixmap(self, pixmap):
#        self.pixmapLabel.setPixmap(pixmap)
#        size = pixmap.size()
#
#        if size - QtCore.QSize(1, 0) == self.pixmapLabelArea.maximumViewportSize():
#            size -= QtCore.QSize(1, 0)
#
#        self.pixmapLabel.resize(size)
#
#    def getSize(self):
#        text, ok = QtGui.QInputDialog.getText(self, "Grabber",
#                "Enter pixmap size:", QtGui.QLineEdit.Normal,
#                "%d x %d" % (self.glWidget.width(), self.glWidget.height()))
#
#        if not ok:
#            return QtCore.QSize()
#
#        regExp = QtCore.QRegExp("([0-9]+) *x *([0-9]+)")
#
#        if regExp.exactMatch(text):
#            width = regExp.cap(0).toInt()
#            height = regExp.cap(1).toInt()
#            if width > 0 and width < 2048 and height > 0 and height < 2048:
#                return QtCore.QSize(width, height)
#
#        return self.glWidget.size()


#if __name__ == '__main__':
#
#    app = QApplication(sys.argv)
#    mainWin = MainWindow()
#    mainWin.show()
#    sys.exit(app.exec_()) 
        
                
#        p0 = Point3d()
#        p0.x = -rad + self.cx
#        p0.y = -rad + self.cy
#        p0.z = -rad + self.cz
#        p1 = Point3d()
#        p1.x = rad + self.cx
#        p1.y = -rad + self.cy
#        p1.z = -rad + self.cz
#        p2 = Point3d()
#        p2.x = rad + self.cx
#        p2.y = -rad + self.cy
#        p2.z = rad + self.cz
#        p3 = Point3d()
#        p3.x = -rad + self.cx
#        p3.y = -rad + self.cy
#        p3.z = rad + self.cz
#        
#        p00 = Point3d()
#        p00.x = -rad + self.cx
#        p00.y = rad + self.cy
#        p00.z = -rad + self.cz
#        p10 = Point3d()
#        p10.x = rad + self.cx
#        p10.y = rad + self.cy
#        p10.z = -rad + self.cz
#        p20 = Point3d()
#        p20.x = rad + self.cx
#        p20.y = rad + self.cy
#        p20.z = rad + self.cz
#        p30 = Point3d()
#        p30.x = -rad + self.cx
#        p30.y = rad + self.cy
#        p30.z = rad + self.cz
#        
#        self.cyls = list()
#        
#        self.cyls.append(drawingUtil.makeCylinder(p0, p1, ref, 5, 5))
#        self.cyls.append(drawingUtil.makeCylinder(p1, p2, ref, 5, 5))
#        self.cyls.append(drawingUtil.makeCylinder(p2, p3, ref, 5, 5))
#        self.cyls.append(drawingUtil.makeCylinder(p3, p0, ref, 5, 5))
#        
#        self.cyls.append(drawingUtil.makeCylinder(p0, p00, ref2, 5, 5))
#        self.cyls.append(drawingUtil.makeCylinder(p1, p10, ref, 5, 5))
#        self.cyls.append(drawingUtil.makeCylinder(p2, p20, ref, 5, 5))
#        self.cyls.append(drawingUtil.makeCylinder(p3, p30, ref, 5, 5))
#        
#        self.cyls.append(drawingUtil.makeCylinder(p00, p10, ref2, 5, 5))
#        self.cyls.append(drawingUtil.makeCylinder(p10, p20, ref2, 5, 5))
#        self.cyls.append(drawingUtil.makeCylinder(p20, p30, ref2, 5, 5))
#        self.cyls.append(drawingUtil.makeCylinder(p30, p00, ref2, 5, 5))