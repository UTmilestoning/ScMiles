#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 14:16:45 2019

@author: weiw
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 26 14:44:51 2018

@author: Wei Wei

This code generates the colvar configuration file that required by NAMD.

Two constraints will be considered:
    1. RMSD(x, anchor_a) = RMSD(x, anchor_b).
    2. RMSD(x, any_anchors_besides_a_or_b) > RMSD(x, anchor_a) &&
       RMSD(x, any_anchors_besides_a_or_b) > RMSD(x, anchor_b).
       
Note:        
    RMSD(x, anchor_a): the root mean square displacement from anchor_a to x
"""

import os

class colvar:
    def __init__(self, parameter, anchor1=None, anchor2=None, free=None, initial=None, 
                 config_path=None):
        self.parameter = parameter
        self.anchor1 = anchor1
        self.anchor2 = anchor2
        self.free = free
        self.initial = initial
        
        scriptPath = os.path.dirname(os.path.abspath(__file__)) 
        self.config_path = scriptPath + "/colvar_free.conf" if self.free == 'yes' else scriptPath + "/colvar.conf"

        
    def __enter__(self):
#        scriptPath = os.path.dirname(os.path.abspath(__file__)) 
#        self.config_path = scriptPath + "/colvar_free.conf" if self.free == 'yes' else scriptPath + "/colvar.conf"
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        return 
            
    
    def __repr__(self) -> str:
        return ('Colvar generator')             
                
    
    def generate(self):    
        scriptPath = os.path.dirname(os.path.abspath(__file__)) 
        config_path = scriptPath + "/colvar_free.conf" if self.free == 'yes' else scriptPath + "/colvar.conf"
        
        colvarsTrajFrequency = self.parameter.colvarsTrajFrequency
        colvarsRestartFrequency = self.parameter.colvarsRestartFrequency
        
        if self.initial == 'yes': 
            outputFrequency = 1 
        elif self.free == 'yes':
            outputFrequency = colvarsTrajFrequency
        else:
            outputFrequency = colvarsTrajFrequency
            
        self.__frequency(outputFrequency, colvarsRestartFrequency)
        
        if self.free == 'yes':
            fconf = open(config_path, 'a')
            print("scriptedColvarForces on", file=fconf)
            fconf.close()
        
        if self.parameter.customColvars == 1:
            self.__append_customColvars()
        
        if self.free != 'yes':
            self.__constraint2D1()
            colvarList, centers = self.__constraint2D2()
            self.__harmonic2D()  
            self.__harmonicWalls(colvarList, centers)
        else:
            for i in range(self.parameter.AnchorNum):
                self.__rmsd_to_anchor(i+1) 
                

    def __frequency(self, colvarsTrajFrequency, colvarsRestartFrequency):
        fconf = open(self.config_path, 'w+')
        print("colvarsTrajFrequency      {}".format(colvarsTrajFrequency), file=fconf)
        print("colvarsRestartFrequency	 {}".format(colvarsRestartFrequency), file=fconf)
        fconf.close()
    
    
    def __append_customColvars(self):
        scriptPath = os.path.dirname(os.path.abspath(__file__)) 
        custom_file = scriptPath + '/custom.colvar'
        fconf = open(self.config_path, 'a')
        print("", file=fconf)
        with open(file=custom_file) as f_custom:
            for line in f_custom:
                print(line, file=fconf)
        fconf.close()


    def __collective_vari_psi(self, name=None, coeff=None, space=0):
        fconf = open(self.config_path, 'a')
        print("  " * space + "  dihedral {", file=fconf)
        if name:
            print("  " * space + "    name {}".format(name), file=fconf) 
        if coeff:
            print("  " * space + "    componentCoeff {}".format(coeff), file=fconf) 
        print("  " * space + "    group1 atomNumbers 7", file=fconf)
        print("  " * space + "    group2 atomNumbers 9", file=fconf)
        print("  " * space + "    group3 atomNumbers 15", file=fconf)
        print("  " * space + "    group4 atomNumbers 17", file=fconf)
        print("  " * space + "  }", file=fconf)
        fconf.close()
        
        
    def __collective_vari_phi(self, name=None, coeff=None, space=0):
        fconf = open(self.config_path, 'a')
        print("  " * space + "  dihedral {", file=fconf)
        if name:
            print("  " * space + "    name {}".format(name), file=fconf) 
        if coeff:
            print("  " * space + "    componentCoeff {}".format(coeff), file=fconf) 
        print("  " * space + "    group1 atomNumbers 5", file=fconf)
        print("  " * space + "    group2 atomNumbers 7", file=fconf)
        print("  " * space + "    group3 atomNumbers 9", file=fconf)
        print("  " * space + "    group4 atomNumbers 15", file=fconf)
        print("  " * space + "  }", file=fconf)
        fconf.close()


    # alapep 2D
    def __rmsd_to_anchor(self, anchor, coeff=None, space=0):
        fconf = open(self.config_path, 'a')
        name = "rmsd" + str(anchor)
        print("\n" + "  " * space + "colvar {", file=fconf)
        print("  " * space + "  name {:5}".format(name), file=fconf)
        func = "sqrt((phi - (" + str(self.parameter.anchors[anchor-1][0]) + "))^2 + (psi- (" + str(self.parameter.anchors[anchor-1][1]) + "))^2) "
        print("  " * space + "  customFunction {}".format(func), file=fconf)
        fconf.close()
        self.__collective_vari_phi(name='phi')
        self.__collective_vari_psi(name='psi')
        fconf = open(self.config_path, 'a')
        print("  " * space + "}", file=fconf)
        fconf.close()


    def __constraint2D1(self):
        fconf = open(self.config_path, 'a')
        print("\ncolvar {", file=fconf)
        print("  name neighbor", file=fconf)
        customFunc = "  customFunction sqrt((phi-(" + str(self.parameter.anchors[self.anchor1-1][0]) + \
        "))^2 + (psi-(" + str(self.parameter.anchors[self.anchor1-1][1]) + "))^2) - sqrt((phi-(" + str(self.parameter.anchors[self.anchor2-1][0]) \
        + "))^2 + (psi-(" + str(self.parameter.anchors[self.anchor2-1][1]) + "))^2)"
        print(customFunc, file=fconf)
        fconf.close()
    
        self.__collective_vari_phi(name='phi', space=1)
        self.__collective_vari_psi(name='psi', space=1)
    
        fconf = open(self.config_path, 'a')
        print("}\n\n", file=fconf)
        fconf.close()



    def __constraint2D2(self):
        colvarList = ""
        centers = ""
        for i in range(self.parameter.AnchorNum):
            if i + 1 != self.anchor1 and i + 1 != self.anchor2:
                fconf = open(self.config_path, 'a')
                print("colvar {", file=fconf)
                print("  name {}_{}".format(i + 1, self.anchor1), file=fconf)
                customFunc = "  customFunction sqrt((phi-(" + str(self.parameter.anchors[i][0]) + \
                "))^2 + (psi-(" + str(self.parameter.anchors[i][1]) + \
                "))^2) - sqrt((phi-(" + str(self.parameter.anchors[self.anchor1-1][0]) + \
                "))^2 + (psi-(" + str(self.parameter.anchors[self.anchor1-1][1]) + "))^2)"
                print(customFunc, file=fconf)
                colvarList += str(i + 1) + "_" + str(self.anchor1) + " "
                centers += "0 "
                fconf.close()
                self.__collective_vari_phi(name='phi', space=2)
                self.__collective_vari_psi(name='psi', space=2)
                fconf = open(self.config_path, 'a')
                print("}\n", file=fconf)       
    
                print("colvar {", file=fconf)
                print("  name {}_{}".format(i + 1, self.anchor2), file=fconf)
                customFunc = "  customFunction sqrt((phi-(" + str(self.parameter.anchors[i][0]) + \
                "))^2 + (psi-(" + str(self.parameter.anchors[i][1]) + \
                "))^2) - sqrt((phi-(" + str(self.parameter.anchors[self.anchor2-1][0]) + \
                "))^2 + (psi-(" + str(self.parameter.anchors[self.anchor2-1][1]) + "))^2)"
                print(customFunc, file=fconf)
    
                colvarList += str(i + 1) + "_" + str(self.anchor2) + " "
                centers += "0 "
                fconf.close()
                self.__collective_vari_phi(name='phi', space=2)
                self.__collective_vari_psi(name='psi', space=2)
                fconf = open(self.config_path, 'a')
                print("}\n", file=fconf)
                fconf.close()
        return colvarList, centers
    
    
    def __harmonic2D(self):
        fconf = open(self.config_path, 'a')
        print("harmonic {", file=fconf)
        print("  colvars neighbor", file=fconf)
        center = 0
        print("  centers {}".format(str(center)), file=fconf)
        print("  forceConstant 1.0", file=fconf)
        print("}", file=fconf)
        fconf.close()
        
        
    def __harmonicWalls(self, colvarList, centers):
        fconf = open(self.config_path, 'a')
        print("\n", file=fconf)
        print("harmonicWalls {", file=fconf)
        print("  colvars {}".format(colvarList), file=fconf)
        print("  lowerWalls {}".format(centers), file=fconf)
        print("  lowerWallConstant 1.0", file=fconf)
        print("}", file=fconf)
        fconf.close()

    
if __name__ == '__main__':
    from parameters import *
    new = parameters()
    new.initialize()
    print(new.anchors)
    colvar(new, anchor1=1, anchor2=2).generate()

    