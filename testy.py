# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import sys

for directory in sys.path:
    print(directory)
    
    
import RootsTool





testClass = RootsTest.TestClass()
myList = [0.5, 2.3, 5.6]

testClass.SetTestVecD(myList)

otherList = testClass.GetTestVecD()

print(otherList)