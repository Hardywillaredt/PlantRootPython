import sys
import math

from RootsTool import MetaGraph, IssuesGL, VBOSphere
from ConnectionTabWidget import Ui_ConnectionTabWidget
from BreakTabWidget import Ui_BreakTabWidget
from SplitTabWidget import Ui_SplitTabWidget

from PyQt5 import QtCore, QtGui, QtOpenGL, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal

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
import random

try:
    from OpenGL.GL import *
except ImportError:
    app = QtGui.QApplication(sys.argv)
    QtGui.QMessageBox.critical(None, "OpenGL grabber",
            "PyOpenGL must be installed to run this example.")
    sys.exit(1)
import OpenGL.GL as gl
from OpenGL.GLU import *
from OpenGL.GLUT import *

from GLObjects import MetaGraphGL, p3d2arr

import SkelGL

from MetaGraphThread import MetaGraphThread, LoadOperationThread, JoinOperationThread, BreakOperationThread, SplitOperationThread
from RootsTool import  Point3d, RootAttributes, Skeleton, MetaNode3d, MetaEdge3d, MetaGraph




class GLWidget(QtOpenGL.QGLWidget):
    xRotationChanged = pyqtSignal(int)
    yRotationChanged = pyqtSignal(int)
    zRotationChanged = pyqtSignal(int)



    @pyqtSlot(str)
    def loadFileEvent(self, filename : str):
        self.loadThread = LoadOperationThread(filename)
        self.loadThread.finished.connect(self.loadThread.deleteLater)
        self.loadThread.sigUpdateMetaGraph.connect(self.metaGL.loadGraphSlot)
        self.loadThread.run()
    
    @pyqtSlot(int, int)
    def acceptConnection(self, v0id, v1id):
        self.connectionThread = JoinOperationThread(self.metaGL.graph, v0id, v1id)
        self.connectionThread.finished.connect(self.connectionThread.deleteLater)
        self.connectionThread.sigUpdateMetaGraph.connect(self.metaGL.updateGraphSlot)
        self.connectionThread.run()
            
    @pyqtSlot(object)
    def acceptBreak(self, edge : MetaEdge3d):
        self.breakThread = BreakOperationThread(self.metaGL.graph, edge)
        self.breakThread.finished.connect(self.breakThread.deleteLater)
        self.breakThread.sigUpdateMetaGraph.connect(self.metaGL.updateGraphSlot)
        self.breakThread.run()

    @pyqtSlot(object, object)
    def acceptSplit(self, splitEdge : MetaEdge3d, secondaries):
        self.splitThread = SplitOperationThread(self.metaGL.graph, splitEdge, secondaries)
        self.splitThread.finished.connect(self.splitThread.deleteLater)
        self.splitThread.sigUpdateMetaGraph.connect(self.metaGL.updateGraphSlot)
        #self.splitThread.start()
        self.splitThread.run()

    @pyqtSlot(object)
    def viewCenterChanged(self, center):
        self.camera.look_at(center)
        self.camera.viewCenter = center
        self.camera.standoff = np.linalg.norm(self.camera.viewCenter - self.camera.get_position())
        self.camera.resolveAngularPosition()

    @pyqtSlot()
    def recenter(self):
        self.camera.viewCenter = p3d2arr(self.metaGL.graph.skeleton.center)
        self.camera.standoff = self.metaGL.graph.skeleton.radius*2
        self.camera.resolveAngularPosition()

    

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
        self.timer.start(10)
        

        self.metaGL = MetaGraphGL(self)
        self.metaGL.connectionOptions.sigConnectionAccepted.connect(self.acceptConnection)
        self.metaGL.breakOptions.sigBreakAccepted.connect(self.acceptBreak)
        self.metaGL.splitOptions.sigSplitAccepted.connect(self.acceptSplit)
        self.metaGL.centerChanged.connect(self.viewCenterChanged)
        #self.metaThread = MetaGraphThread()
        #self.metaGL.connectionOptions.sigConnectionAccepted.connect(self.metaThread.acceptConnection)
        #self.metaGL.breakOptions.sigBreakAccepted.connect(self.metaThread.acceptBreak)
        #self.metaGL.splitOptions.sigSplitAccepted.connect(self.metaThread.acceptSplit)
        #self.metaThread.sigUpdateMetaGraph.connect(self.metaGL.updateGraphSlot)
        #self.metaThread.start()



        self.modes = {-1 : 'NoMode', 0 : 'Connection Mode', 1 : 'Separation Mode', 2 : 'Spltting Mode'}
        
        self.currentMode = -1
    
    @pyqtSlot()
    def timeOut(self):
        if self.isWDown:
            self.camera.goForward(self.speed)
        elif self.isSDown:
            self.camera.goForward(-self.speed)
            
        if self.isADown:
            self.camera.goRight(-self.speed)
        elif self.isDDown:
            self.camera.goRight(self.speed)
        
        if self.isQDown:
            self.camera.roll(-0.01 * 5)
        elif self.isEDown:
            self.camera.roll(0.01 * 5)
        self.update()
        
        
    @pyqtSlot()
    def updateCurrentGL(self, modelGL : object):
        self.modelGL = modelGL
        self.hasModelGL = True

    def setupInteraction(self):
        self.isMouseLeftDown = False
        self.isMouseRightDown = False
        self.isMouseMiddleDown = False
        self.zoom = 1.0
        self.zoomDegrees = 0.0
        self.lastMouseX = 0.0
        self.lastMouseY = 0.0
        
        self.isWDown = False
        self.isADown = False
        self.isSDown = False
        self.isDDown = False
        self.isQDown = False
        self.isEDown = False

        self.baseSpeed = 0.15 * 5
        self.speed = self.baseSpeed
        
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)
        
    def setupVis(self):
        self.camera = Camera()
        initialPosition = v3(0, 0, 40)
        
        self.camera.set_position(initialPosition)
        self.viewCenter = v3()
        self.camera.look_at(self.viewCenter)
        self.camera.set_near(1.0)
        self.camera.set_far(1000.0)
        self.baseFov = (60.0 / 180.0) * np.pi
        self.camera.set_fov(self.baseFov)
        w = float(self.width())
        h = float(self.height())
        self.camera.set_aspect(w/h)
        p = self.camera.get_model_matrix()
        
        self.imageCenterX = w / 2.0
        self.imageCenterY = h / 2.0
        
    def __del__(self):
        self.makeCurrent()
        for cyl in self.cyls:
            glDeleteLists(cyl)

    def setXRotation(self, angle : float):
        self.normalizeAngle(angle)
        oAngle = angle * 2*np.pi / 5760.0
        pitch = self.camera.get_world_pitch()
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
        angleDif = oAngle - yaw
        self.camera.yaw(angleDif)
        if angle != self.yRot:
            self.yRot = angle
            self.yRotationChanged.emit(angle)
            self.updateGL()

    def setZRotation(self, angle : float):
        self.normalizeAngle(angle)
        oAngle = angle * 2*np.pi / 5760.0
        roll = self.camera.get_world_roll()
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
        
        #glLightfv(GL_LIGHT0, GL_POSITION, lightPos)
#        glLightfv(GL_LIGHT1, GL_POSITION, lightPos)
#        glLightfv(GL_LIGHT0, GL_AMBIENT, ambientLight)
        #glEnable(GL_LIGHTING)
        glDisable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        self.cx = 0
        self.cy = 0
        self.cz = 0
        self.rad = 10
        rad = self.rad

        self.rotX = 0.0
        self.rotY = 0.0

        glEnable(GL_NORMALIZE)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.camera.get_fov_deg(), self.camera.get_aspect(), self.camera.get_near(), self.camera.get_far())
        glMatrixMode(GL_MODELVIEW)
        self.issuesGL = IssuesGL()
        self.sphere = VBOSphere()
        
        random.seed(0)
        self.randvals = []
        for row in range(0, 201):
            self.randvals.append([])
            for col in range(0, 201):
                self.randvals[row].append(random.uniform(0.25, 1.0))


    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.camera.get_fov_deg(), self.camera.get_aspect(), self.camera.get_near(), self.camera.get_far())
        

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        
        
        self.camera.look_at(self.camera.viewCenter)
        lpos = self.camera.viewCenter
        up = self.camera.get_world_up()

        pos = self.camera.get_position()
        lightpos = (pos[0], pos[1], pos[2], 1.0)
        color = (1.0, 0.0, 1.0, 1.0)

        ldir = lpos - pos

        
        
        

        gluLookAt(pos[0], pos[1], pos[2], lpos[0], lpos[1], lpos[2], up[0], up[1], up[2])
        
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, lightpos)
        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, ldir)
        ldir /= np.linalg.norm(ldir)

        #self.metaGL.display(self.zoom)
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, color)
        #self.issuesGL.issuegl()
        x = -100.0
        y = -100.0
        z = 0.0
        row = 0
        while x <= 100:
            y = -10.0
            col = 0
            while y <= 10:
                self.sphere.fancyDraw(1.0, 0.5, 1.0, x, y, z, self.randvals[row][col])
                y = y + 1.0
                col = col  + 1
            x = x + 1.0
            row = row + 1

        #glTranslated(-100.0, 0.0, 0.0)
        #for x in range(, 200):
        #    glTranslated(0.0, -100.0, 0.0)
        #    for y in range(0, 100):
        #        #glScalef(2.0, 2.0, 2.0)
        #        self.sphere.draw()
        #        #glScalef(0.5, 0.5, 0.5)
        #        glTranslated(0.0, 1.0, 0.0)
        #    glTranslated(1.0, 0.0, 0.0)

        
        glDisable(GL_LIGHTING)
        glPopMatrix()
 
        
    def resizeGL(self, width : int, height : int):
        side = min(width, height)
        
        #fov = (60.0 / 180.0) * np.pi
        #self.camera.set_fov(fov)
        w = float(self.width())
        h = float(self.height())
        self.camera.set_aspect(w/h)
        
        
        glViewport(0, 0, width, height)

        #glMatrixMode(GL_PROJECTION)
        #glLoadIdentity()
        #glFrustum(-1.0, +1.0, -1.0, 1.0, 5.0, 60.0)
        #glMatrixMode(GL_MODELVIEW)
        #glLoadIdentity()
        #glTranslated(0.0, 0.0, -40.0)
        self.imageCenterX = float(width) / 2.0
        self.imageCenterY = float(height) / 2.0



    def xRotation(self):
        return self.xRot

    def yRotation(self):
        return self.yRot

    def zRotation(self):
        return self.zRot 

    #def drawCallList(self, gear, dx : float = 0, dy : float = 0, dz : float = 0, angle : float = 0):
    #    glPushMatrix()
    #    glTranslated(dx, dy, dz)
    #    glRotated(angle, 0.0, 0.0, 1.0)
    #    glCallList(gear)
    #    glPopMatrix()

    def normalizeAngle(self, angle : float):
        while (angle < 0):
            angle += 360 * 16

        while (angle > 360 * 16):
            angle -= 360 * 16
    
    
    def keyPressEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()

        if self.underMouse() and modifiers == Qt.NoModifier:
            if key == Qt.Key_W:
                self.isWDown = True
#                self.camera.goUp(0.1)
            elif key == Qt.Key_S:
                self.isSDown = True
#                self.camera.goUp(-0.1)
                
            elif key == Qt.Key_A:
                self.isADown = True
#                self.camera.goRight(-0.1)
            elif key == Qt.Key_D:
                self.isDDown = True
#                self.camera.goRight(0.1)
                
            elif key == Qt.Key_Q:
                self.isQDown = True
#                self.camera.roll(0.05)
            elif key == Qt.Key_E:
                self.isEDown = True
#                self.camera.roll(-0.05)
        

        QtOpenGL.QGLWidget.keyPressEvent(self, event)
        
    
    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()
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

    def wheelEvent(self, QWheelEvent : QtGui.QWheelEvent):
        numDegrees = (QWheelEvent.angleDelta() / 8.0).y()


        self.zoomDegrees += numDegrees

        halfRotations = self.zoomDegrees / 180

        self.zoom = pow(2.0, halfRotations)

        self.camera.set_fov(self.baseFov / self.zoom)

        self.speed = self.baseSpeed / self.zoom

        return super().wheelEvent(QWheelEvent)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        
        if event.button() == Qt.RightButton and not self.isMouseLeftDown:
            self.isMouseRightDown = True
            self.lastMouseX = event.x()
            self.lastMouseY = event.y()
            ray = self.getRay(event.x(), event.y())
            origin = self.camera.getNpPosition()
            self.metaGL.doPicking(origin, ray)
            #self.metaThread.RayPickedEvent(origin, ray)
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
        elif event.button() == Qt.LeftButton and not self.isMouseRightDown:
            self.isMouseLeftDown = True
            self.lastMouseX = event.x()
            self.lastMouseY = event.y()
            ray = self.getRay(event.x(), event.y())
            origin = self.camera.getNpPosition()
            self.metaGL.doPicking(origin, ray)
#            (hitFound, edgeHit, edgeHitId) = self.skelModel.getFirstEdgeHit(origin, ray)
#            self.skelModel.highlightEdge(edgeHitId)
            '''
            if self.currentMode == -1:
                (hitFound, nodeHit, nodeHitId) = self.skelModel.getFirstNodeHit(origin, ray)
                self.skelModel.highlightNode(nodeHitId)
            '''

        elif event.button() == Qt.MiddleButton:
            self.isMouseMiddleDown = True
            self.lastMouseX = event.x()
            self.lastMouseY = event.y()
        
        
    def mouseMoveEvent(self, event: QtGui.QMouseEvent):

        if self.isMouseMiddleDown:
            difX = event.x() - self.lastMouseX
            difY = event.y() - self.lastMouseY

            self.camera.goUp(self.speed * difY * 0.3)
            self.camera.goRight(-self.speed * difX * 0.3)

            self.lastMouseX = event.x()
            self.lastMouseY = event.y()

        if self.isMouseLeftDown:
            difX = event.x() - self.lastMouseX
            difY = event.y() - self.lastMouseY

            
            self.camera.increment_phi(0.01*difX)
            self.camera.increment_theta(0.01*difY)
            self.camera.resolveAngularPosition()

            
            self.lastMouseX = event.x()
            self.lastMouseY = event.y()
            
        elif self.isMouseRightDown:
            difX = event.x() - self.lastMouseX
            difY = event.y() - self.lastMouseY

            self.camera.yaw(0.01 * difX)
            self.camera.pitch(0.01*difY)
            self.camera.resolveAngularPosition()

            
            self.lastMouseX = event.x()
            self.lastMouseY = event.y()
            
        if self.isMouseLeftDown or self.isMouseRightDown or self.isMouseMiddleDown:
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
        elif event.button() == Qt.MiddleButton:
            self.isMouseMiddleDown = False
            
            
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
            
    
    def enterConnectionMode(self, ConnectionWidget : Ui_ConnectionTabWidget):
        self.currentMode = 0
        self.connectionWidget = ConnectionWidget
        self.metaGL.enterConnectionMode(ConnectionWidget)

        

    def enterBreakMode(self, BreakWidget : Ui_BreakTabWidget):
        self.currentMode = 1
        self.metaGL.enterBreakMode(BreakWidget)
        
        
    def enterSplitMode(self, SplitWidget : Ui_SplitTabWidget):
        self.currentMode = 2
        self.metaGL.enterSplitMode(SplitWidget)

        
#    def UpdateConnectionWidget(self):
#        self.connectionWidget.ComponentOne.currentIndexChanged.disconnect(self.ComponentOneChangeSlot)
#        self.connectionWidget.ComponentTwo.currentIndexChanged.disconnect(self.ComponentTwoChangeSlot)
#        self.skelModel.updateConnectionWidget(self.connectionWidget)
#        self.connectionWidget.ComponentOne.currentIndexChanged.connect(self.ComponentOneChangeSlot)
#        self.connectionWidget.ComponentTwo.currentIndexChanged.connect(self.ComponentTwoChangeSlot)
        
#    @QtCore.pyqtSlot(int)
#    def ComponentOneChangeSlot(self, val):
#        p = 2
#        #self.skelModel.ChangeComponentOne(int(val))
        
#    @QtCore.pyqtSlot(int)
#    def ComponentTwoChangeSlot(self, val):
#        g = 3
##        self.skelModel.ChangeComponentTwo(int(val))
        
        
        
#        projectedZ = -1.0
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
#        
#        dirVec = m41(unprojectedPoint[0][0],
#                     unprojectedPoint[1][0],
#                     -1,
#                     0)
#        dirVec = dirVec / np.linalg.norm(dirVec)
#        dirVec[3][0] = 1
#        
#        camMat = self.camera.get_camera_matrix()
#        
#        p = camMat @ dirVec
#        
#        
#        dirVec = v3(p[0][0],
#                     p[1][0],
#                     p[2][0])
#        
#        dirVec = dirVec - self.camera.getNpPosition()
#        
#        dirVec = dirVec / np.linalg.norm(dirVec)
#        
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
