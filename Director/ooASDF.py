# oo version to create ASDF files from excel
import datetime
import os
import asdf
import shutil
from excelScrape import excelScrape
import sys

class ooASDF:
    def __init__(self,fileName):
        
        #Scan Library to see if file is in here
        self.ooASDFLoc = os.getcwd()
        os.chdir('..\\Library')
        self.libLoc = os.getcwd()
        
        os.chdir('..')
        self.rootLoc = os.getcwd()
        os.chdir(self.libLoc)
        
        #Ensure that we only pick .asdf files by appending .asdf to supplied filename if it wasn't done already
        if not fileName.endswith('.asdf'):
            fileName = fileName + '.asdf'
        
        #Open up the asdf file or create one
        if not fileName in os.listdir():
            metadata = {
            'fileName': fileName,
            'numDatasets': 0,
            'bibTex': '',
            'notes': '',
            'Created': datetime.datetime.now(),
            'Updated': datetime.datetime.now()
            }
            tree = {'metadata':metadata}
            af = asdf.AsdfFile(tree)
            af.write_to(fileName)
            self.tree = tree
        else:
            af = asdf.open(fileName)
            self.tree = af.tree
        self.af = af
        self.treeLength = len(self.tree)
        self.fileName = fileName
        
    def importBib(self, bibFile):
        os.chdir('..\\InputFiles')
        bib = open(bibFile)
        bibText = bib.read()
        bib.close()
        self.tree['metadata']['bibTex'] = bibText
        bibFileLoc = os.getcwd() + '\\' +  bibFile
        os.rename(bibFileLoc, self.rootLoc + '\\ConvertedFiles\\' + bibFile)
        return None
        
    
    def addData(self,dataFile = '',flag = 0, sheet = ''):
        
        #Get a valid excel file to scrape if no input was given, default unless there are for some reason many excel files in the input
        os.chdir('..\\InputFiles')
        if dataFile != '':
            if not dataFile.endswith('.xlsx'):
                dataFile = dataFile + '.xlsx'
        else:
            for file in os.listdir():
                if file.endswith('.xlsx'):
                    dataFile = file
                    break
            else:
                raise Exception('There are no valid excel files here')
        
        
        datFileLoc = os.getcwd() + '\\' +  dataFile
        #TODO: Use flag=0 to scan entire excel file and flag=1 to scan a single sheet
        dataSetList = excelScrape(dataFile)
        
        for dataSet in dataSetList:
            dataSetnumbering = self.tree['metadata']['numDatasets'] + 1
            self.tree['dataSet' + str(dataSetnumbering)] = dataSet
            self.tree['metadata']['numDatasets'] = dataSetnumbering
        self.treeLength = len(self.tree)
        
        #Move the recently scanned excel file to the convertedFiles folder
        os.rename(datFileLoc, self.rootLoc + '\\ConvertedFiles\\' + dataFile)
        os.chdir(self.libLoc)
        return None
        
        
    def finish(self):
        self.tree['metadata']['Updated'] = datetime.datetime.now()
        os.chdir(self.libLoc)
        af = asdf.AsdfFile(self.tree)
        
        if self.tree['metadata']['bibTex'] == '':
            raise Exception('bibTex Field is empty')
        
        af.write_to(self.fileName)
        print('ASDF File manipulation existed successfully')
        return None
            
    
            
            

#Example run
newASDF = ooASDF('oakridge1973')

## Make sure InputFiles folder has an excel file and bib file before uncommenting

newASDF.addData()
newASDF.importBib('oakridge.bib')


newASDF.finish()