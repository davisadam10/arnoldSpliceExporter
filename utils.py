import maya.cmds as cmds
nodes = cmds.ls(sl=True)

class AttributeExport(object):
    def __init__(self):
        self.name = None
        self.type = None
        self.value = None

class NodeExport(object):
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.attrs = []

    def addAttr(self, name, type, value):
        attr = AttributeExport()
        attr.name = name
        attr.type = type
        attr.value = value
        self.attrs.append(attr)

class MayaSpliceArnoldExporter(NodeExport):
    def __init__(self):
        #template

allNodes = []
for node in nodes:
    exportNode = NodeExport(node, cmds.nodeType(node))
    attrs = cmds.listAttr(node, ud=True)
    for attr in attrs:
        attrType = cmds.getAttr("%s.%s" % (node, attr), type=True)
        value = cmds.getAttr("%s.%s" % (node, attr))
        print attr, attrType, value
        exportNode.addAttr(attr, attrType, value)
    allNodes.append(exportNode)
    
allNodes[0].attrs[0].value
    