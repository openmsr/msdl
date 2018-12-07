import os
import asdf

def dataImport(property,mixture):
    apiLoc = os.getcwd()
    os.chdir('..\\Library')
    fileList = os.listdir()
    print(fileList)
    for asdfFile in fileList:
        if not asdfFile.endswith('asdf'):
            continue
        af = asdf.open(asdfFile)
        for dataSet in af.tree:
            if not dataSet.startswith('DataSet'):
                continue
            if af.tree[dataSet]['Property'][0].lower() == 'Viscosity'.lower():
                af.tree[dataSet]['Components'].sort()
                print(af.tree[dataSet]['Components'])
    return None

dataImport('Viscosity','satisfied')
