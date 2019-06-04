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
        self.unit = 'mPa*s'
    
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
                    else:
                        if self.composition == af.tree[dataSet]['Composition']:
                            dataSetList.append(af.tree[dataSet])
                        else:
                            continue
                
                
        
        #Finally change the working directory back to the original one
        os.chdir(apiLoc)
        self.dataSetList = dataSetList
        
        return dataSetList
    
    
    #Extracts the measurements from the datasets
    def getMeasurements(self):
        measurements = [[]]
        temperatures = [[]]
        parameters = [[]]
        for dataSet in self.dataSetList:
            i = 0
            if dataSet['Property'][0].lower() == self.propert.lower():
                
                #Attempt to make asdf file more robust in terms of misspelling, We try to get all the keys
                #in a list and use a regular expression matching.
                allKeys = list(dataSet.keys())
                allKeysString = ' '.join(allKeys)
                tempRegex = re.compile(r'temp[\S]*|Temp[\S]*')
                mo1 = tempRegex.search(allKeysString)
                tempKey = mo1.group()
                measureRegex = re.compile(r'meas[\S]*|Meas[\S]*')
                mo1 = measureRegex.search(allKeysString)
                measureKey = mo1.group()
                
                temperatures[i] = dataSet[tempKey]
                measurements[i] = dataSet[measureKey]
                i = i+1
                
        self.numMeasurements = i
        self.measurements = measurements
        self.temperatures = temperatures
        return 0
    
    #TODO MAKE THE FUNCTION once more datapoints are gathered
    #Creates a vector where all measurements are combined
    def combineMeasurements(self):
        return 0
    
    #TODO: Loop through each individual dataset, waiting for more data too test that
    
    #Creates a regression of the data
    def regressData(self,x,y):
        #TODO Add the functions for other properties, Will do when I get data for other properties
        if self.propert.lower() == 'viscosity':
            test_func = lambda x,a,b: self.Arrhenius(x,a,b)
            p0 = [0.2,2000]
        params,covar = optimize.curve_fit(test_func,x,y,p0)
        self.parameters = params
        
        
        
        return 0
    
    #Using matplotlib, this generates figures containing datapoint and regression
    def viewProperties(self):
        for i in range(self.numMeasurements):
            #plt.plot(self.temperatures[i],self.measurements[i],'bs', label='ID HERE')
            plt.xlabel('Temperature (°C)')
            plt.ylabel(self.propert + ' (' + self.unit + ')')
            
            #Doing individual regression and plotting, This will be moved to a different function is future versions
            xData = np.array(self.temperatures[i])
            yData = np.array(self.measurements[i])
            self.regressData(xData,yData)
            xx = np.linspace(min(xData),max(xData),num=100)
            if self.propert.lower() == 'viscosity':
                yy = self.Arrhenius(xx,self.parameters[0],self.parameters[1])
            plt.plot(xx,yy)
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
        self.getMeasurements()
        #self.combineMeasurements() <- Add when function is complete
        #self.regressData() <- Add when function is finished
    
    ## Regression Base Functions
    #Arrhenius function, default for Viscosity Regression
    def Arrhenius(self,x,a,b):
        return a*np.exp(b/(8.314*x))
    
    
    #TODO: Make FUnction
    #Function to predict new data points, Plan is to generally predict with Kriging but can include heuristics
    #for "smarter" prediction (ex: If composition is included in library known, use one of the regression methods)
    def predict(self,x):
        y = 0
        return y
        
## Example Run
#newAPI = API('Viscosity',['NaBF4','NaF'])
        
newAPI = API('Viscosity',['NaBF4','NAF'])

newAPI.initialize()
newAPI.getMeasurements()
newAPI.viewProperties()