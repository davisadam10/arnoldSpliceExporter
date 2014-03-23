import os

TEMPLATE_DIR = os.path.join(
                            "C:\Users\Adam\Desktop\Creation\\arnoldSpliceExporter",
                            "templates"
                            )

SAVE_DIR = "C:\Users\Adam\Desktop\Creation\\arnoldSpliceExporter"

class ArnoldAssTemplate(object):
    def __init__(self):
        self.baseTemplate = os.path.join(TEMPLATE_DIR, "mainTemplate.ass")
        self.procedurals = []
        self.camera = None
        self.options = None

    def addProcedural(self, node):
        self.procedurals.append(node)

    def __getProceduralsReplacementDit(self):
        returnDict = {}
        
        returnDict["<CAMERA>"] = self.camera.getAssCode()
        returnDict["<OPTIONS>"] = self.options.getAssCode()

        proceduralAssCode = ""
        for node in self.procedurals:
            proceduralAssCode += "%s\n" % (node.getAssCode())

        returnDict["<PROCEDURAL>"] = proceduralAssCode
        return returnDict

    def renderTemplate(self):
        file = open(self.baseTemplate, "r")
        lines = file.readlines()
        file.close()
        renderDict = {}
        renderDict.update(self.__getProceduralsReplacementDit())

        filledTemplate = ""
        for line in lines:
            for replacement, value in renderDict.items():
                if replacement in line:
                    line = line.replace(replacement, value)

            filledTemplate += line


        return filledTemplate

    def save(self, filePath):
        file = open(filePath, "w")
        lines = self.renderTemplate()
        file.write(lines)
        file.close()
        return filePath

class AttributeExport(object):
    def __init__(self):
        self.name = None
        self.type = None
        self.value = None
        self.typeMapping = {"double": "FLOAT", 
                    "int": "INT",
                    "long": "INT",
                    "matrix": "MATRIX",
                    
        }

    def getVariableAssType(self):
        val = None
        if self.type in self.typeMapping:
            val = self.typeMapping[self.type]
        return val

class NodeExport(object):
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.attrs = []
        self.worldMatrix = [1.0, 0.0, 0.0, 0.0,
                            0.0, 1.0, 0.0, 0.0,
                            0.0, 0.0, 1.0, 0.0,
                            0.0, 0.0, 0.0, 1.0]

        self.templateDir = TEMPLATE_DIR

    def addAttr(self, name, type, value):
        attr = AttributeExport()
        attr.name = name
        attr.type = type
        attr.value = value
        self.attrs.append(attr)

    def renderTemplate(self, template, renderDict):
        file = open("%s\%s" % (self.templateDir, template), "r")
        lines = file.readlines()
        file.close()
        filledTemplate = ""
        for line in lines:
            for replacement, value in renderDict.items():
                if replacement in line:
                    line = line.replace(replacement, str(value).replace("[", "").replace("]", "")).replace(",", ' ')

            filledTemplate += line


        return filledTemplate

class MayaSpliceArnoldExporter(NodeExport):
    def __init__(self, name, type, spliceFile):
        NodeExport.__init__(self, name, type)
        self.template = "procedural.txt"
        self.spliceFile = spliceFile

    def getAssCode(self):
        renderDict = {}
        variableCode = ""
        for attr in self.attrs:
            variableType = attr.getVariableAssType()
        
            if variableType:
                basecode = "declare %s constant %s\n" % (attr.name, variableType)
                basecode += "%s %s\n" % (attr.name, str(attr.value).replace("[", "").replace("]", "").replace(",", ' '))
                variableCode += basecode

        renderDict["<name>"] = self.name
        renderDict["<spliceFile>"] = self.spliceFile
        renderDict["<worldMatrix>"] = self.worldMatrix
        renderDict["<variables>"] = variableCode

        return self.renderTemplate(self.template, renderDict)


class MayaCameraArnoldExporter(NodeExport):
    def __init__(self, name, type):
        NodeExport.__init__(self, name, type)
        self.template = "camera.txt"
        self.fov = None
        self.nearClip = None
        self.farClip = None

    def getAssCode(self):
        renderDict = {}
        renderDict["<name>"] = self.name
        renderDict["<worldMatrix>"] = self.worldMatrix
        renderDict["<fov>"] = self.fov
        renderDict["<nearClip>"] = self.nearClip
        renderDict["<farClip>"] = self.farClip

        return self.renderTemplate(self.template, renderDict)


class ArnoldOptionsExporter(NodeExport):
    def __init__(self, name, type):
        NodeExport.__init__(self, name, type)
        self.template = "options.txt"
        self.cameraName = None    

    def getAssCode(self):
        renderDict = {}
        renderDict["<cameraName>"] = self.cameraName
        return self.renderTemplate(self.template, renderDict)



def createSpliceExportNode(node):
    import maya.cmds as cmds
    savePath = os.path.join(SAVE_DIR, "%s.splice" % (node))
    exportNode = MayaSpliceArnoldExporter(node, "spliceMayaNode", savePath)
    #cmds.fabricSplice('saveSplice', '%s' % (node), '{"fileName": "%s"}' % (savePath))
    attrs = cmds.listAttr(node, ud=True)
    for attr in attrs:
        attrType = cmds.getAttr("%s.%s" % (node, attr), type=True)
        value = cmds.getAttr("%s.%s" % (node, attr))
        exportNode.addAttr(attr, attrType, value)
    
    return exportNode

def getSceneProcedurals():
    import maya.cmds as cmds
    nodeType = "spliceMayaNode"
    splceNodes = cmds.ls(type=nodeType)
    allNodes = []
    for node in splceNodes:
        exportNode = createSpliceExportNode(node)
        allNodes.append(exportNode)

    return allNodes

def getRenderCamera():
    import maya.cmds as cmds
    cameras = cmds.ls(sl=True, type="camera")
    if cameras:
        camera = cameras[0]
        cameraNode = MayaCameraArnoldExporter(camera, "spliceMayaNode")
        cameraNode.worldMatrix = cmds.getAttr("%s.%s" % (camera, "worldMatrix"))
        cameraNode.farClip = cmds.getAttr("%s.%s" % (camera, "farClipPlane"))
        cameraNode.nearClip = cmds.getAttr("%s.%s" % (camera, "nearClipPlane"))
        
        aperture = cmds.getAttr("%s.%s" % (camera, "hfa"))
        focalLength = cmds.getAttr("%s.%s" % (camera, "focalLength"))
        fov = aperture * 0.5 / (focalLength * 0.03937)
        cameraNode.fov = 2.0 * math.atan(fov)/3.14159 * 180

        return cameraNode


assTemplate = ArnoldAssTemplate()
camera = getRenderCamera()
assTemplate.camera = camera

options = ArnoldOptionsExporter("renderOptions", "renderOptions")
options.cameraName = camera.name 
assTemplate.options = options

procedurals = getSceneProcedurals()
for procedural in procedurals:
    assTemplate.addProcedural(procedural)


filePath = os.path.join(SAVE_DIR, "generated.ass")
assTemplate.save(filePath)
        