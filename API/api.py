import os
import asdf
import numpy as np
import matplotlib.pyplot as plt
import math
import re
from scipy import optimize

class API:
    def __init__(self, propert, salts, composition = []):
        self.propert = propert
        self.salts = salts
        self.composition = composition
        self.regressionType = 'None'
        self.fitModel = 'None'
        self.source = []
        
        if propert.lower() == 'viscosity':
            self.unit = 'mPa*s'
        elif propert.lower() == 'density':
            self.unit = 'g/cm3'
        else:
            self.unit = 'Unit undefined'
    
    #Scan the database library and extract datasets that contain the desired salts
    def scanLibrary(self):
        dataSetList = []
        #Get a list of all asdf files in Library and loop through them
        apiLoc = os.getcwd()
        
        os.chdir('..\\Library')
        
        for file in os.listdir():
            if not file.endswith('asdf'):
                continue
            af = asdf.open(file)
            
            for dataSet in af.tree:
                if not dataSet.startswith('dataSet'):
                    continue
                
                
                #Ensuring that we can directly compare salt list by lowercasing and sorting them
                saltList = [a.lower() for a in af.tree[dataSet]['Components']]
                requestList = [a.lower() for a in self.salts]
                saltList.sort()
                requestList.sort()

                
                if saltList == requestList:
                    if self.composition == []:
                        dataSetList.append(af.tree[dataSet])
                        self.source.append(file)
                    else:
                        if self.composition == af.tree[dataSet]['Composition']:
                            dataSetList.append(af.tree[dataSet])
                            self.source.append(file)
                        else:
                            continue
                
                
        
        #Finally change the working directory back to the original one
        os.chdir(apiLoc)
        self.dataSetList = dataSetList
        self.source = set(self.source)
        
        return dataSetList
    
    #Organizes all the salt measurements into X and Y, where X is a matrix where each column represents composition and temperature
    #and Y contains the property measurements
    def organizeData(self):
        numSalts = len(self.salts)
        l = 0
        for dataSet in self.dataSetList:
            if dataSet['Property'][0].lower() == self.propert.lower():
                
                #Regular expression for asdf keys
                allKeys = list(dataSet.keys())
                allKeysString = ' '.join(allKeys)
                tempRegex = re.compile(r'temp[\S]*|Temp[\S]*')
                mo1 = tempRegex.search(allKeysString)
                tempKey = mo1.group()
                measureRegex = re.compile(r'meas[\S]*|Meas[\S]*')
                mo1 = measureRegex.search(allKeysString)
                measureKey = mo1.group()
                compRegex = re.compile(r'comp[\S]*ion|Comp[\S]*ion')
                mo1 = compRegex.search(allKeysString)
                compKey = mo1.group()
                
                
                tempMat = np.zeros( (numSalts + 1 ,dataSet[tempKey].shape[0]))
                for i in range(numSalts):
                    tempMat[i,:] = np.repeat(dataSet[compKey][i],dataSet[tempKey].shape[0])
                tempMat[-1,:] = dataSet[tempKey]
                if l == 0:
                    X = tempMat
                    Y = dataSet[measureKey]
                else:
                    X = np.concatenate((X,tempMat),axis=1)
                    Y = np.concatenate((Y,dataSet[measureKey]))
                l = l+1
        self.X = X
        self.Y = Y
        
        #Checking if salt data contains multiple composition, in the case it will do a one dimensional regression
        self.oneDimensional = True
        for i in range(X.shape[0]-1):
            oneComp = X[i,:]
            checkers = (oneComp[1:] == oneComp[:-1])
            if all(checkers):
                pass
            else:
                self.oneDimensional = False
                
                
        #Check for binary mixture (only relevant for multiple compositions)
        if not self.oneDimensional and X.shape[0] == 3:
            self.binary = True
        else:
            self.binary = False
        
        return 0
    
    #TODO: Loop through each individual dataset, waiting for more data too test that
    
    #Creates a regression of the data
    def regressData(self,x,y):
        #TODO Add the functions for other properties, Will do when I get data for other properties
        if self.propert.lower() == 'viscosity':
            basis_func = lambda x,a,b: self.Arrhenius(x,a,b)
        elif self.propert.lower() == 'density':
            basis_func = lambda x,a,b: self.oneDimensionalLine(x,a,b)
        p0 = [0.2,2000]
        params,covar = optimize.curve_fit(basis_func,x,y,p0)
        self.parameters = params
        return 0
    
    def buildModel(self):
        return 0
    
    #Using matplotlib, this generates figures containing datapoint and regression
    def makePlot(self):
        #If only one composition exists
        if self.oneDimensional:
            #plt.plot(self.temperatures[i],self.measurements[i],'bs', label='ID HERE')
            plt.xlabel('Temperature (°C)')
            plt.ylabel(self.propert + ' (' + self.unit + ')')
            #Check for 1 dimensional plot condition by checking if composition remains consistent troughout
                
            
            #Doing individual regression and plotting, This will be moved to a different function is future versions
            xData = self.X[-1,:]
            yData = self.Y
            self.regressData(xData,yData)
            xx = np.linspace(min(xData),max(xData),num=100)
            if self.propert.lower() == 'viscosity':
                yy = self.Arrhenius(xx,self.parameters[0],self.parameters[1])
            elif self.propert.lower() == 'density':
                yy = self.oneDimensionalLine(xx,self.parameters[0],self.parameters[1])
            plt.plot(xx,yy)
            #plt.scatter(xData,yData)
        elif self.binary:
            print('Two dimensional stuff in development')
        else:
            print("Can't make relevant figure")
            
        #TODO Set a binary mixture here
        return 0
    
    #Method to initialize the object (i.e. scan the library and do some preliminary data processing)
    #so it's ready for data viewing
    
    #Function to predict new data points, Plan is to generally predict with Kriging but can include heuristics
    #for "smarter" prediction (ex: If composition is included in library known, use one of the regression methods)
    def predict(self,x):
        y = 0
        return y
    
    
    def initialize(self):
        self.scanLibrary()
        self.organizeData()
        if self.oneDimensional:
            #self.regressData() <- Add when function is finished
            pass
        else:
            #self.buildModel() <- Add when function is finished
            pass
    
    
    def printExcelReport(self):
        return 0
    
    
    ## Regression Base Functions
    #Arrhenius function, default for Viscosity Regression
    def Arrhenius(self,x,a,b):
        return a*np.exp(b/(8.314*x))
    
    #Simple linear regression for Density
    def oneDimensionalLine(self,x,a,b):
        return a*x + b
    
    #TODO: Make FUnction
    #Function to predict new data points, Plan is to generally predict with Kriging but can include heuristics
    #for "smarter" prediction (ex: If composition is included in library known, use one of the regression methods)
    def predict(self,x):
        y = 0
        return y
        
## Example Run
#newAPI = API('Viscosity',['NaBF4','NaF'])
        
newAPI = API('viscosity',['NaNO3', 'KNO3'])
newAPI.scanLibrary()
newAPI.organizeData()
newAPI.makePlot()
print(newAPI.X)
print(newAPI.Y)
print(newAPI.source)

#newAPI.initialize()
#newAPI.getMeasurements()
#newAPI.makePlot()
#print(newAPI.numMeasurements)
