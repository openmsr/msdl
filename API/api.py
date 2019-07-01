import os
import asdf
import numpy as np
import matplotlib.pyplot as plt
import math
import re
from scipy import optimize

#For Kriging model
import pyKriging  
from pyKriging.krige import kriging  
from pyKriging.samplingplan import samplingplan


class API:
    def __init__(self, propert, salts, composition = []):
        self.propert = propert         #Desired physical property
        self.salts = salts             #List of desired salt combo
        self.composition = composition #Salt composition
        self.regressionType = 'None' #Description of the Regression type
        self.modelType = 'kriging'    #Type of model to fit the data (Default Kriging for now)
        self.fitModel = 'None'      #Objec to store the fit model
        self.source = []            #List of asdf files that include the salt combo
        self.allSets = []          #List of all datasets currently in library
        
        #Setting the unit of the physical property (For picture caption)
        if propert.lower() == 'viscosity':
            self.unit = 'Pa*s'
        elif propert.lower() == 'density':
            self.unit = 'g/cm3'
        elif propert.lower() == 'thermal conductivity':
            self.unit = 'W/(m K)'
        else:
            self.unit = 'Unit undefined'
            
    #Scan the database library and extract datasets that contain the desired salts
    def scanLibrary(self):
        dataSetList = []
        #Get a list of all asdf files in Library and loop through them
        apiLoc = os.getcwd()
        
        os.chdir('..\\Library')
        
        for file in os.listdir():
            if not file.endswith('asdf'):   #Only look through .asdf files
                continue
            af = asdf.open(file)
            
            for dataSet in af.tree:
                if not dataSet.startswith('dataSet'):   #Skip searching the metadata tree
                    continue
                
                
                #Ensuring that we can directly compare salt list by lowercasing and sorting them
                saltList = [a.lower() for a in af.tree[dataSet]['Components']] 
                self.allSets.append(saltList)
                requestList = [a.lower() for a in self.salts]
                saltList.sort()
                requestList.sort()
                
                #Only work with files that match the specified salt combo
                if saltList == requestList:
                    if self.composition == []:
                        dataSetList.append(af.tree[dataSet])
                        self.source.append(file)    #Append filename to the source list
                    else:
                        if self.composition == af.tree[dataSet]['Composition']:     #If composition is specified, only grab specific composition
                            dataSetList.append(af.tree[dataSet])
                            self.source.append(file)
                        else:
                            continue
                
                
        
        #Finally change the working directory back to the original one
        os.chdir(apiLoc)
        self.dataSetList = dataSetList  #Storing raw data in API object
        self.source = set(self.source)  #Delete source duplicates
        
        return dataSetList
    
    #Organizes all the salt measurements into X and Y, where X is a matrix where each column represents composition and temperature
    #and Y contains the property measurements
    def organizeData(self):
        numSalts = len(self.salts)
        l = 0
        for dataSet in self.dataSetList:
            if dataSet['Property'][0].lower() == self.propert.lower():
                
                #Regular expression for asdf keys (Attempt to make more robust in case misspelling in excel files occurr)
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
                
                
                temps = np.array(dataSet[tempKey])  #Sometimes temperature arrays don't come out as numpy arrays (If they only have integers), this ensures it
                
                #Creating X and Y vectors
                tempMat = np.zeros( (numSalts + 1 ,temps.shape[0]))
                for i in range(numSalts):
                    tempMat[i,:] = np.repeat(dataSet[compKey][i],temps.shape[0])    #One composition is measured many times, so we create a proper array size to match temperature readings
                tempMat[-1,:] = temps
                if l == 0:
                    X = tempMat
                    Y = dataSet[measureKey]
                else:
                    X = np.concatenate((X,tempMat),axis=1)
                    Y = np.concatenate((Y,dataSet[measureKey]))
                l = l+1
        
        #Do to keeping track with variable l, if it's 0 it means no datasets were found that match the physical property        
        if l>0:        
            self.X = X
            self.Y = np.array(Y)
        #Set flags and ending function early to prevent raising exceptions
        else:
            print('No data in libray matches specifications')
            self.oneDimensional = False
            self.binary = False
            return 0    
        
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
            #In a binary mixture one of the rows containing composition is irrelevant thus it's deleted
            X = np.delete(X,0,0)
            self.X = X
        else:
            self.binary = False
        
        
        #Casting whatever may pop up to float64, (Some scan cases lead to string data values)
        if X.dtype == "<U32":
            X = np.char.replace(X, ' ', '')
            X = X.astype(float)
        if Y.dtype == "<U32":
            Y = np.char.replace(Y, ' ', '')
            Y = Y.astype(float)
        self.Y = Y
        self.X = X
        return 0
        
    #Creates a regression of the data
    def regressData(self):
        x = np.array(self.X[-1,:])
        y = np.array(self.Y)
        if self.propert.lower() == 'viscosity':
            basis_func = lambda x,a,b: self.Arrhenius(x,a,b)
            p0 = [0.2,2000]
        elif self.propert.lower() == 'density' or self.propert.lower() == 'thermal conductivity':
            basis_func = lambda x,a,b: self.oneDimensionalLine(x,a,b)
            p0 = [0.2,2000]
        params,covar = optimize.curve_fit(basis_func,x,y,p0)
        self.parameters = params
        return 0
    
    def buildModel(self):
        if self.modelType == 'kriging':
            print('Statistical model: Simple Kriging')
            X = self.X
            Y = self.Y
            if self.oneDimensional:
                X = X[-1,:]
            X = X.reshape(-1,1)
            
            k = kriging(X,Y, name ='simple')
            k.train()
            self.fitModel = k
        else:
            print('Invalid model type request')
        return 0
    
    #Using matplotlib, this generates figures containing datapoint and regression
    def makePlot(self):
        #If only one composition exists
        if self.oneDimensional:
            
            
            #Create data regression line
            xData = np.array(self.X[-1,:])
            yData = np.array(self.Y)
            self.regressData()
            xx = np.linspace(min(xData),max(xData),num=100)
            if self.propert.lower() == 'viscosity':
                yy = self.Arrhenius(xx,self.parameters[0],self.parameters[1])
            elif self.propert.lower() == 'density' or self.propert.lower() == 'thermal conductivity':
                yy = self.oneDimensionalLine(xx,self.parameters[0],self.parameters[1])
            
            #Since graph is one dimensional we extract the composition to print on graph
            comp = np.zeros(self.X.shape[0]-1)
            
            for i in range(len(comp)):
                comp[i] = self.X[i,0]
            
            
            #Create blackbox fit line
            yFit = np.zeros(xx.shape)
            for i in range(len(xx)):
                yFit[i] = self.fitModel.predict([xx[i]])

            
            
            #First plot, data along with regression
            plt.figure(0)
            plt.xlabel('Temperature (°C)')
            plt.ylabel(self.propert.capitalize() + ' (' + self.unit + ')')
            plt.scatter(xData,yData)
            plt.plot(xx,yy)
            plt.legend(["Regression Fit","Data"])
            plt.title(' '.join(self.salts) + ' ' + np.array2string(comp))
            
            #Second plot, data along with blackbox model
            plt.figure(1)
            plt.xlabel('Temperature (°C)')
            plt.ylabel(self.propert.capitalize() + ' (' + self.unit + ')')
            plt.scatter(xData,yData)
            plt.plot(xx,yFit,'r')
            plt.legend(["Blackbox Fit","Data"])
            plt.title(' '.join(self.salts) + ' ' + np.array2string(comp))
            
            
            
        elif self.binary:
            self.fitModel.plot()
        else:
            print("Can't make relevant figure for dimensions larger than 3")
            
        return 0
    
    #Method to initialize the object (i.e. scan the library and do some preliminary data processing)
    #so it's ready for data viewing
    
    
    #Function that tries to find a minimum and maximum of the dataset, finds both min and max of raw data and then utilizing fit models to predict it.
    def minMax(self):
        return 0
        
    
    def printExcelReport(self):
        
        return 0
    
    def initialize(self):
        self.scanLibrary()
        self.organizeData()
        if self.oneDimensional:
            self.regressData()
        self.buildModel()
    
    
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
        
newAPI = API('density',['LiBr'])
newAPI.initialize()
newAPI.makePlot()

print(newAPI.X)
print(newAPI.Y)

#newAPI.initialize()
#newAPI.getMeasurements()
#newAPI.makePlot()
#print(newAPI.numMeasurements)
