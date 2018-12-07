#dataImport.py takes in two inputs, the salt mixture and a physical property and then scans
#the entire asdf data library in folder Library for files that contain a property dataset for the given mixture
#ex: Viscosity for mixture LiF and BeF2
#It then returns the datasets found that matches the input, otherwise it returns Nothing
#This only works if the asdf files are written with correct format i.e. it searches for the "Components" and "Property" parameters
#in the files

import os
import asdf

def dataImport(property,mixture):
    dataSetList = []
    #Get the absolute path
    apiLoc = os.getcwd()

    #Get a list of all asdf files in Library and loop through them
    os.chdir('..\\Library')
    fileList = os.listdir()
    print(fileList)
    for asdfFile in fileList:

        #Skip files that are not asdf files
        if not asdfFile.endswith('asdf'):
            continue
        af = asdf.open(asdfFile)

        #Look through all the datasets, skip tree binaries that aren't datasets (Ex: metadata)
        for dataSet in af.tree:
            if not dataSet.startswith('DataSet'):
                continue
            #Ensuring that both input list and dataset list are similar by lowercasing all components and sorting it alphabetically
            #It allows us to compare the two
            af.tree[dataSet]['Components'].sort()
            mixture.sort()
            dataSetComponents = [component.lower() for component in af.tree[dataSet]['Components']]
            mixtureComponents = [component.lower() for component in mixture]

            #Check if the correct dataset parameters match the input and then append it to the output list
            if af.tree[dataSet]['Property'][0].lower() == 'Viscosity'.lower() and dataSetComponents == mixtureComponents:
                print('Property set found for mixture in file ' + asdfFile)
                dataSetList.append(af.tree[dataSet])
    return dataSetList
