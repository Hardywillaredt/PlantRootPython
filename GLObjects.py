# -*- coding: utf-8 -*-
"""
Created on Fri Mar  9 14:26:21 2018

@author: Will
"""


import sys
import math

import numpy as np

from OpenGL.GL import *
import OpenGL.GL as gl

from OpenGL.GLU import *
from OpenGL.GLUT import *

from PyQt5 import QtCore, QtGui, QtOpenGL, QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from RootsTool import  Point3d, RootAttributes, Skeleton, MetaNode3d, MetaEdge3d, MetaGraph
import drawingUtil
import util
from ModeOptions import ConnectionModeOptions

def p3d2arr(p3d : Point3d):
    if isinstance(p3d, Point3d) or isinstance(p3d, MetaNode3d):
        return np.array([p3d.x, p3d.y, p3d.z])
    else:
        return p3d


class LineGL():
    def __init__(self, v0, v1, thickness, idx, component, v0rad=0.0, v1rad=0.0, scale=1.0):
        self.v0 = p3d2arr(v0)
        self.v1 = p3d2arr(v1)
        self.rad = thickness / 2.0
        self.id = idx
        self.component = component
        
        self.scale = scale
        self.baseScale = scale
        
        self.useVRad = False
        if v0rad != 0.0 and v1rad != 0.0:
            self.v0rad = v0rad
            self.v1rad = v1rad
            self.useVRad = True
        self.scale = scale
        
        self.isHighlight = False
        
        self.baseVertices = np.array()
        self.capVertices = np.array()
        self.normals = np.array()
        self.computeGeometry()
        
    def computeGeometry(self):
        
        if self.useVRad:
            R0 = self.v0rad
            R1 = self.v1rad
        else:
            R0 = self.rad
            R1 = self.rad
        
        R0 = R0 * scale
        R1 = R1 * scale
        
        maxR = max(R0, R1)
        numSides = max(int(maxR * 8), 8)
        
        direction = self.v0 - self.v1
        
        
        direction = direction / np.linalg.norm(direction)
        
        vec1 = np.array([])
        
        if direction[1] == 0 and direction[2] == 0:
            vec1 = np.cross(direction, [0, 1, 0])
        else:
            vec1 = np.cross(direction, [1, 0, 0])
        
        vec2 = np.cross(direction, vec1)
        
        vec1 = vec1 / np.linalg.norm(vec1)
        vec2 = vec2 / np.linalg.norm(vec2)
        
        p0 = self.v0
        p1 = self.v1
        stepSize = 2 * math.pi / numSides
        theta = 0.0
        self.normals.resize([numSides, 3])
        self.baseVertices.resize([numSides, 3])
        self.capVertices.resize([numSides, 3])
#        glBegin(GL_TRIANGLE_STRIP)
        step = 0
        while theta < 2*math.pi:
            basePoint = p0 + R0*math.cos(theta)*vec1 + R0*math.sin(theta)*vec2
            capPoint = p1 + R1*math.cos(theta)*vec1 + R1*math.sin(theta)*vec2
            n = basePoint - p0
            n = n / np.linalg.norm(n)
            theta = theta + stepSize
            self.normals[step] = n
            self.baseVertices[step] = basePoint
            self.capVertices[step] = capPoint
            step = step + 1
    
    def issueGL(self, color):
        result = gl.glGenLists(1)
        
        gl.glNewList(result, gl.GL_COMPILE)
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE, color)
        gl.glBegin(gl.GL_TRIANGLE_STRIP)
        
        for n, base, cap in zip(self.normals, self.baseVertices, self.capVertices):
            gl.glNormal3d(n[0], n[1], n[2])
            gl.glVertex3d(base[0], base[1], base[2])
            gl.glVertex3d(cap[0], cap[1], cap[2])
            
        n = self.normals[0]
        base = self.baseVertices[0]
        cap = self.capVertices[1]
        
        gl.glNormal3d(n[0], n[1], n[2])
        gl.glVertex3d(base[0], base[1], base[2])
        gl.glVertex3d(cap[0], cap[1], cap[2])
        gl.glEnd()
        gl.glEndList()
        return result
        
    def highlight(self):
        self.isHighlight = True
        self.scale = self.baseScale * 1.3
        
    def unhighlight(self):
        self.isHighlight = False
        self.scale = self.baseScale

            
    def setScale(self, scale):
        self.baseScale = scale
        
        
        
def PointGL():
    def __init__(self, v0, radius, idx, component, scale : float =1.0):
        self.v0 = p3d2arr(v0)
        self.radius = radius
        self.id = idx
        self.component = component
            
        self.scale = scale
        self.baseScale = scale
        self.isHighlight = False
        
        
    def issueGL(self):
        
        glPushMatrix()
        glTranslated(self.v0[0], self.v0[1], self.v0[2])
        quadric = gluNewQuadric()
        gluQuadricOrientation(quadric, GLU_OUTSIDE)
        gluSphere(quadric, self.scale*self.radius, 40, 40)
        glPopMatrix()
        
    def highlight(self):
        self.isHighlight = True
        self.scale = self.baseScale * 1.3
        
    def unhighlight(self):
        self.isHighlight = False
        self.scale = self.baseScale
            
    def setScale(self, scale):
        self.baseScale = scale
    

class MetaGraphGL():
    @pyqtSlot()
    def unselectNode(self, nodeId):
        self.MetaNodesGL[nodeId].unhighlight()
        
    @pyqtSlot()
    def selectNode(self, nodeId):
        self.MetaNodesGL[nodeId].highlight()
        
    @pyqtSlot()
    def unselectEdge(self, edgeId):
        self.MetaEdgesGL[edgeId].unhighlight()
        self.rebuildMetaEdgeGLList(edgeId)
        
    @pyqtSlot()
    def selectEdge(self, edgeId):
        self.MetaEdgesGL[edgeId].highlight()
        self.rebuildMetaEdgeGLList(edgeId)
    
    @pyqtSlot()
    def rebuildNodes(self):
        self.rebuildMetaNodesGLList()
        
    @pyqtSlot()
    def componentsChanged(self, componentMap):
        self.minimizedComponentMap = componentMap
    
    def __init__(self):
        self.hasMetaGraph = False
        self.nodeSizeMap = {}
        self.minimizedComponentMap = {}
        self.graph = None
        
        self.modes = {-1 : 'NoMode', 0 : 'Connection Mode', 1 : 'Separation Mode', 2 : 'Spltting Mode'}
        self.currentMode = -1
        self.displayModes = {0 : 'Graph', 1 : 'Skeleton'}
        self.currentDisplayMode = 0
        
        self.skelGLEdgesLists = []
        self.skelGLNodesList = None
        self.graphGLEdgesLists = []
        self.graphGLNodesList = None
        self.MetaNodesGL = []
        self.MetaEdgesGL = []
        self.SkelNodesGL = []
        self.SkelEdgesGL = []
        self.colorTable = drawingUtil.ColorTable
        self.highlightColorTable = []
        self.lowlightColorTable = []
        self.numComponents = 0
        
        self.connectionOptions = None
        self.breakOptions = None
        self.splitOptions = None
        
    def setMetaGraph(self, graph : MetaGraph):
        self.graph = graph
        self.numComponents = len(self.graph.componentNodeMap)
        for key in self.graph.componentNodeMap.keys():
            self.minimizedComponentMap[key] = False
        
        self.MetaNodesGL = []
        self.MetaEdgesGL = []
        self.SkelNodesGL = []
        self.SkelEdgesGL = []
        self.numComponents = len(self.graph.componentNodeMap)
        self.fillColorTables()
                
        
        for node in self.graph.nodeLocations:
            self.MetaNodesGL.append(PointGL(node, node.size, node.order, node.component, 1.0))
            
        skeleton = self.graph.skeleton
        for edge in self.graph.edgeConnections:
            v0 = self.graph.nodeLocations[edge.node0]
            v1 = self.graph.nodeLocations[edge.node1]
            self.MetaEdgesGL.append(LineGL(v0, v1, edge.thickness, edge.order, edge.component))
            
            for skelEdge in edge.edges:
                v0 = PointGL(skeleton.vertices[skelEdge.v0id], skelEdge.thickness /2.0, skelEdge.v0id, edge.component)
                v1 = PointGL(skeleton.vertices[skelEdge.v1id], skelEdge.thickness /2.0, skelEdge.v1id, edge.component)
                line = LineGL(v0.v0, v1.v1, skelEdge.thickness, edge.order, edge.component)
                self.SkelNodesGL.append(v0)
                self.SkelNodesGL.append(v1)
                self.SkelEdgesGL.append(line)
    
    def fillColorTables(self):
        if self.numComponents > len(self.colorTable):
            for i in range(len(self.colorTable), self.numComponents):
                randColor = np.random.ranf(3)
                self.colorTable.append([randColor[0], randColor[1], randColor[2], 1.0])
        self.highlightColorTable = []
        self.lowlightColorTable = []
        for color in self.colorTable:
            self.highlightColorTable.append([min(color[0]*1.5, 1.0), min(color[1]*1.5, 1.0), min(color[2]*1.5, 1.0), min(color[3]*1.5, 1.0)])
            self.lowlightColorTable.append(color[0], color[1], color[2], color[3]/20)
    
        
    def resolveGraph(self, updateGraph : MetaGraphGL):
        '''
        Should only be callled by the MetaGraphGL maintained on the main thread
        '''
        for selfNode, otherNode in zip(self.MetaNodesGL, updateGraph.MetaNodesGL):
            otherNode.isHighlight = selfNode.isHighlight
            otherNode.baseScale = selfNode.baseScale
            otherNode.scale = selfNode.scale
            
        for selfEdge, otherEdge in zip(self.MetaEdgesGL, updateGraph.MetaEdgesGL):
            otherEdge.isHiglight = selfEdge.isHiglight
            otherEdge.baseScale = selfEdge.baseScale
            otherEdge.scale = selfEdge.scale
            
        for selfNode, otherNode in zip(self.SkelNodesGL, updateGraph.SkelNodesGL):
            otherNode.isHighlight = selfNode.isHighlight
            otherNode.baseScale = selfNode.baseScale
            otherNode.scale = selfNode.scale
            
        for selfEdge, otherEdge in zip(self.SkelEdgesGL, updateGraph.SkelEdgesGL):
            otherEdge.isHiglight = selfEdge.isHiglight
            otherEdge.baseScale = selfEdge.baseScale
            otherEdge.scale = selfEdge.scale
            
        self.MetaNodesGL = updateGraph.MetaNodesGL
        self.MetaEdgesGL = updateGraph.MetaEdgesGL
        self.SkelNodesGL = updateGraph.SkelNodesGL
        self.SkelEdgesGL = updateGraph.SkelEdgesGL
        self.graph = updateGraph.graph
        self.numComponents = updateGraph.numComponents
        self.fillColorTables()
        self.rebuildGLLists()
        self.updateModeOptions()
        
    def rebuildGLLists(self):
        '''
        Should only be called by the metagraphgl maintained on the main thread
        '''
        self.graphGLEdgesLists = []
        
        for i in range(0, len(self.MetaEdgesGL)):
            self.graphGLEdgesLists.append(None)
            self.rebuildMetaEdgeGLList(i)
        
        self.rebuildMetaNodesGLList()
        
        self.skelGLEdgesLists = []
        
        for i in range(0, len(self.SkelEdgesGL)):
            self.skelGLEdgesLists.append(None)
            self.rebuildSkelEdgeGLList(i)
            
        self.rebuildSkelNodesGLList()
        
    def rebuildMetaEdgeGLList(self, idx : int):
        edgeGL = self.MetaEdgesGL[idx]
        color = []
        if self.minimizedComponentMap[edgeGL.component]:
            color = self.lowlightColorTable[edgeGL.component]
        elif edgeGL.isHiglight:
            color = self.highlightColorTable[edgeGL.component]
        else:
            color = self.colorTable[edgeGL.component]
        
        self.graphGLEdgesLists[idx] = edgeGL.issueGL(color)
        
    def rebuildMetaNodesGLList(self):
        self.graphGLNodesList = gl.glGenLists(1)
        gl.glNewList( self.graphGLNodesList, gl.GL_COMPILE)
        for pointGL in self.MetaNodesGL:
            if self.minimizedComponentMap[pointGL.component]:
                gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE, self.lowlightColorTable[pointGL.component])
            elif pointGL.isHiglight:
                gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE, self.highlightColorTable[pointGL.component])
            else:
                gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE, self.colorTable[pointGL.component])
            
            pointGL.issueGL()
            
        gl.glEndList()
        
    def rebuildSkelEdgeGLList(self, idx : int):
        edgeGL = self.SkelEdgesGL[idx]
        color = []
        if self.minimizedComponentMap[edgeGL.component]:
            color = self.lowlightColorTable[edgeGL.component]
        elif edgeGL.isHiglight:
            color = self.highlightColorTable[edgeGL.component]
        else:
            color = self.colorTable[edgeGL.component]
            
        self.skelGLEdgesLists[idx] = edgeGL.issueGL(color)
        
    def rebuildSkelNodesGLList(self):
        self.skelGLNodesList = gl.glGenLists(1)
        gl.glNewList(self.skelGLNodesList, gl.GL_COMPILE)
        for pointGL in self.SkelNodesGL:
            if self.minimizedComponentMap[pointGL.component]:
                gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE, self.lowlightColorTable[pointGL.component])
            elif pointGL.isHiglight:
                gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE, self.highlightColorTable[pointGL.component])
            else:
                gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE, self.colorTable[pointGL.component])
            
            pointGL.issueGL()
            
        gl.glEndList()
        
                    
        
    def getFirstEdgeHit(self, origin : np.array, ray : np.array):
        print('detecting hits')
        minDist = 100000000
        hitFound = False
        edgeHit = None
        edgeHitId = -1
        if not self.hasMetaGraph:
            return (hitFound, edgeHit, edgeHitId)
        for edge in self.metaGraph.edgeConnections:
            if self.minimizedComponentMap[edge.component]:
                continue
            p0 = self.metaGraph.nodeLocations[edge.node0]
            p1 = self.metaGraph.nodeLocations[edge.node1]
            p0 = p3d2arr(p0)
            p1 = p3d2arr(p1)
            
                
            (doesIntersect, distance) = util.intersectRayCylinder(origin, ray, p0, p1, edge.thickness)
            if not doesIntersect:
                (doesIntersect, distance) = util.intersectRaySphere(origin, ray, p0, edge.thickness)
            if not doesIntersect:
                (doesIntersect, distance) = util.intersectRaySphere(origin, ray, p1, edge.thickness)
            
            if doesIntersect:
                if distance < minDist: 
                    hitFound = True
                    minDist = distance
                    edgeHit = edge
                    edgeHitId = edge.order
        return (hitFound, edgeHit, edgeHitId)
        
    def getFirstNodeHit(self, origin : np.array, ray : np.array):
        print('detecting node hits')
        minDist = 1000000000
        hitFound = False
        nodeHit = None
        nodeHitId = -1
        
        if not self.hasMetaGraph:
            return(hitFound, nodeHit, nodeHitId)

        for node in self.metaGraph.nodeLocations:
            if self.minimizedComponentMap[node.component]:
                continue
            p = p3d2arr(node)
            (doesIntersect, distance) = util.intersectRaySphere(origin, ray, p, node.size)
            
            if doesIntersect:
                if distance < minDist:
                    hitFound = True
                    minDist = distance
                    nodeHit = node
                    nodeHitId = node.order
        return(hitFound, nodeHit, nodeHitId)
        
    def changeEdgeSelection(self, edgeIds):
        self.silentUnselect()
        for edgeId in edgeIds:
            if edgeId > -1 and edgeId < len(self.MetaEdgesGL):
                self.MetaEdgesGL[edgeId].highlight()
                self.rebuildMetaGLEdgeList(edgeId)
                metaEdge = self.graph.edgeConnections[edgeId]
                self.MetaNodesGL[metaEdge.node0].highlight()
                self.MetaNodesGL[metaEdge.node1].highlight()
        self.rebuildMetaNodesGLList()
    
    def updateEdgeSelection(self, edgeIds):
        for edgeId in edgeIds:
            if edgeId > -1 and edgeId < len(self.MetaEdgesGL):
                self.MetaEdgesGL[edgeId].highlight()
                self.rebuildMetaGLEdgeList(edgeId)
                metaEdge = self.graph.edgeConnections[edgeId]
                self.MetaNodesGL[metaEdge.node0].highlight()
                self.MetaNodesGL[metaEdge.node1].highlight()
        self.rebuildMetaNodesGLList()
                
    def flipEdgeSelection(self, edgeIds):
        for edgeId in edgeIds:
            if edgeId > -1 and edgeId < len(self.MetaEdgesGL):
                edgeGL = self.MetaEdgesGL[edgeId]
                metaEdge = self.graph.edgeConnections[edgeId]
                if edgeGL.isHighlight:
                    self.MetaEdgesGL[edgeId].unhighlight()
                    self.MetaNodesGL[metaEdge.node0].unhighlight()
                    self.MetaNodesGL[metaEdge.node1].unhighlight()
                else:
                    self.MetaEdgesGL[edgeId].highlight()
                    self.MetaNodesGL[metaEdge.node0].highlight()
                    self.MetaNodesGL[metaEdge.node1].highlight()
                self.rebuildMetaGLEdgeList(edgeId)
        self.rebuildMetaNodesGLList()
        
          
    def unselect(self):
        for edge in self.MetaEdgesGL:
            if edge.isHighlight:
                edge.unhighlight()
                self.rebuildMetaGLEdgeList(edge.id)
                
        for node in self.MetaNodesGL:
            node.unhighlight()
            
        self.rebuildMetaNodesGLList()
    
    def exitOtherModes(self):
        if self.currentMode != 0:
            if self.connectionOptions != None:
                self.connectionOptions.exitMode()
        if self.currentMode != 1:
            if self.breakOptions != None:
                self.breakOptions.exitMode()
        if self.currentMode != 2:
            if self.splitOptions != None:
                self.splitOptions.exitMode()
                
        
    def enterConnectionMode(self, widget):
        if self.connectionOptions == None:
            self.connectionOptions = ConnectionModeOptions(self.numComponents)
            self.connectionOptions.enterMode(self.numComponents, widget)
            self.connectionOptions.nodeUnselected.connect(self.unselectNode)
            self.connectionOptions.nodeSelected.connect(self.selectNode)
            self.connectionOptions.componentsChanged.connect(self.componentsChanged)
        else:
            self.connectionOptions.enterMode(self.numComponents, widget)
        self.currentMode = 0
        self.exitOtherModes()
        
    
        
    