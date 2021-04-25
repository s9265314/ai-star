#!/usr/bin/python
#-*- encoding: UTF-8 -*-

import sys
import string, re
import sqlite3

def distance(a,b):
    aL=a.split(",")
    a_len=len(aL)
    bL=b.split(",")
    b_len=len(bL)
    if a_len==0: return b_len
    if b_len==0: return a_len
    limit=min(a_len, b_len)
    idx=0
    while idx < limit:
	if aL[idx]!=bL[idx]:
	    break
	idx+=1
    return a_len+b_len-idx-idx

def searchShortestPath(a,b):
    aL=a.split(",")
    a_len=len(aL)
    bL=b.split(",")
    b_len=len(bL)
    if a_len==0: return None
    if b_len==0: return None

    L=[]
    limit=min(a_len, b_len)
    idx=0
    while idx < limit:
	if aL[idx]!=bL[idx]:
	    break
	idx+=1
    #print "aL:%s"%aL
    #print "bL:%s"%bL
    #print "common:%s"%aL[:idx]
    for jdx in range(len(aL),idx,-1):
        #print "X:%s"%aL[:jdx]
	L.append(string.join(aL[:jdx],","))
    #print "C:%s"%aL[:idx]
    L.append(string.join(aL[:idx],","))
    for jdx in range(idx+1,len(bL)+1):
        #print "Y:%s"%bL[:jdx]
        L.append(string.join(bL[:jdx],","))
    d=a_len+b_len-idx-idx
    #print "d:%s,L:%s"%(d,L)
    return (d,L)

def dict_factory(cursor, row):
    d={}
    for idx, col in enumerate(cursor.description):
	d[col[0]]=row[idx]
    return d

class Node(object):
    def __init__(self, tree, node_type, data):
	self.tree=tree
	data['node_type']=node_type
	self.data=data

    def cols(self):
	return self.data.keys()

    def __str__(self):
    	return unicode(self).encode('UTF-8')

    def __repr__(self):
    	return unicode(self).encode('UTF-8')

    def __unicode__(self):
    	str=u"%s('%s')"%(self.data['node_type'], self.data['name'])
	return str

    def __getattr__(self, attr):
	if not (attr in self.data):
	    sys.stderr.write("Error: attr %s\n"%(attr))
	    raise AttributeError
	return self.data[attr]

    def isHypernymOf(self, obj):
	if not isinstance(self, SemanticTypeNode):
	    return False
	pathL=obj._getPathList()
	levelL=obj._getLevelList()
	for idx in range(len(pathL)):
	    path=pathL[idx]
	    level=levelL[idx]
	    if self.level==level-1 and len(self.path) < path and self.path==path[:len(self.path)]:
		return True
	return False

    def isHyponymOf(self, obj):
	if not isinstance(obj, SemanticTypeNode):
	    return False
	pathL=self._getPathList()
	levelL=obj._getLevelList()
	for idx in range(len(pathL)):
	    path=pathL[idx]
	    level=levelL[idx]
	    if self.level==level+1 and len(obj.path) < path and obj.path==path[:len(obj.path)]:
		return True
	return False

    def isAncestorOf(self, obj):
	if not isinstance(self, SemanticTypeNode):
	    return False
	pathL=obj._getPathList()
	for path in pathL:
	    if len(self.path) < path and self.path==path[:len(self.path)]:
		return True
	return False

    def isDescendantOf(self, obj):
	if not isinstance(obj, SemanticTypeNode):
	    return False
	pathL=self._getPathList()
	for path in pathL:
	    if len(obj.path) < path and obj.path==path[:len(obj.path)]:
		return True
	return False

    def encode(self, codec):
	return unicode(self).encode(codec)

    def dump(self):
	L=[]
	L.append("    node_type: %s"%(self.data['node_type']))
	L.append("    node_id: %s"%(self.data['node_id']))
	L.append("    name: %s"%(self.data['name']))
	keys=self.data.keys()
	keys.sort()
	for k in keys:
	    if k in ["node_type","node_id","name"]:
		continue
	    L.append("    %s: %s"%(k, self.data[k]))
	return "{\n"+string.join(L,",\n")+"\n}\n".encode("UTF-8")

class SemanticTypeNode(Node):
    def __init__(self, tree, data):
	super(SemanticTypeNode,self).__init__(tree, '', data)

    def __loadPathInfo__(self):
	sql="select path, level from tree where node_id=?"
	self.tree.cursor.execute(sql,(self.node_id,))
	row=self.tree.cursor.fetchone()
	self.path=row['path']
	self.level=row['level']

    def _getPathList(self):
	return [self.path]

    def _getLevelList(self):
	return [self.level]

    def __getattr__(self, attr):
	if attr=='path' or attr=='level':
	    self.__loadPathInfo__()
	    return self.__dict__[attr]
	else:
	    return super(SemanticTypeNode,self).__getattr__(attr)

    def getAncestorList(self):
	path=self.path
	pos=len(path)
	L=[]
	while pos>0:
	    node=self.tree.getNodeByPath(path[:pos])
	    L.append(node)
	    pos=path.rfind(',',0, pos)
	L.reverse()
	return L

    def getDescendantList(self):
	#sql="select B.* from tree A, semanticTypeNode B where A.type='semanticType' and A.node_id=B.node_id and A.path like ? and A.level=?"
	#self.tree.cursor.execute(sql,(self.path+',%',self.level+1))
	# 用一些技巧取代 LIKE 加速查詢
	sql="select B.* from tree A, semanticTypeNode B where A.node_id=B.node_id and (A.path>=? and A.path<=?) and A.level>=?"
	self.tree.cursor.execute(sql,(self.path+',1',self.path+',a',self.level+1))
	L=[]
	for row in self.tree.cursor:
	    L.append(SemanticTypeNode(self.tree, row))
	return L

    def getHypernym(self):
	if self.level==1:
	    return None
	pos=self.path.rindex(",")
	pp=self.path[:pos]
	sql="select B.* from tree A, semanticTypeNode B where A.type='semanticType' and A.node_id=B.node_id and path=?"
	self.tree.cursor.execute(sql,(pp,))
	data=self.tree.cursor.fetchone()
	return SemanticTypeNode(self.tree, data)

    def getHyponymList(self):
	#sql="select B.* from tree A, semanticTypeNode B where A.type='semanticType' and A.node_id=B.node_id and A.path like ? and A.level=?"
	#self.tree.cursor.execute(sql,(self.path+',%',self.level+1))
	# 用一些技巧取代 LIKE 加速查詢
	sql="select B.* from tree A, semanticTypeNode B where A.node_id=B.node_id and (A.path>=? and A.path<=?) and A.level=?"
	self.tree.cursor.execute(sql,(self.path+',1',self.path+',a',self.level+1))
	L=[]
	for row in self.tree.cursor:
	    L.append(SemanticTypeNode(self.tree, row))
	return L

    def getWordList(self):
	#sql="select B.* from tree A, wordNode B where A.node_id=B.node_id and A.path like ? and A.level=?"
	#self.tree.cursor.execute(sql,(self.path+',%',self.level+1))

	# 用一些技巧取代 LIKE 加速查詢
	sql="select B.* from tree A, wordNode B where A.node_id=B.node_id and (A.path>=? and A.path<?) and A.level=?"
	self.tree.cursor.execute(sql,(self.path+',1',self.path+',a',self.level+1))
	L=[]
	for row in self.tree.cursor:
	    L.append(WordNode(self.tree, row))
	return L

    def getDescendantWordList(self):
	# 用一些技巧取代 LIKE 加速查詢
	sql="select B.* from tree A, wordNode B where A.node_id=B.node_id and (A.path>=? and A.path<=?) and A.level>=?"
	self.tree.cursor.execute(sql,(self.path+',1',self.path+',a',self.level+1))
	L=[]
	for row in self.tree.cursor:
	    L.append(WordNode(self.tree, row))
	return L


class WordNode(Node):
    def __init__(self, tree, data):
	super(WordNode,self).__init__(tree, 'word', data)

    def __loadPathInfo__(self):
	sql="select path, level from tree where node_id=?"
	self.tree.cursor.execute(sql,(self.node_id,))
	pL=self.tree.cursor.fetchall()
	self.pathList=[]
	self.levelList=[]
	for row in pL:
	    self.pathList.append(row['path'])
	    self.levelList.append(row['level'])
	
    def _getPathList(self):
	return self.pathList

    def _getLevelList(self):
	return self.levelList

    def __getattr__(self, attr):
	if attr=='pathList' or attr=='levelList':
	    self.__loadPathInfo__()
	    return self.__dict__[attr]
	else:
	    return super(WordNode,self).__getattr__(attr)

    def getSemanticTypeList(self):
	L=[]
	for path in self.pathList:
	    pos=path.rindex(",")
	    pp=path[:pos]
	    sql="select B.* from tree A, semanticTypeNode B where A.type='semanticType' and A.node_id=B.node_id and path=?"
	    self.tree.cursor.execute(sql,(pp,))
	    data=self.tree.cursor.fetchone()
	    L.append(SemanticTypeNode(self.tree, data))
	return L

    def getSynonymWordList(self):
	nodeL=self.getSemanticTypeList()
	wordL=[]
	for node in nodeL:
	    for word in node.getWordList():
		if word.ehownet==self.ehownet and word.name!=self.name:
		    wordL.append(word)
	return wordL

    def getSiblingWordList(self):
	nodeL=self.getSemanticTypeList()
	wordL=[]
	for node in nodeL:
	    wordL+=node.getWordList()
	return wordL

    def getDescendantWordList(self):
	nodeL=self.getSemanticTypeList()
	wordL=[]
	for node in nodeL:
	    wordL+=node.getDescendantWordList()
	return wordL

class EHowNetTree(object):
    def __init__(self, dbfile):
        self.rootNode=None
	self.dbfile=dbfile
	self.conn=sqlite3.connect(self.dbfile)
	self.conn.row_factory=dict_factory
	self.cursor=self.conn.cursor()

    def getNodeByID(self, node_id):
	if node_id[0]=='w':
	    sql="select * from wordNode where node_id=?"
	    self.cursor.execute(sql,(node_id,))
	    row=self.cursor.fetchone()
	    if not row:
	        return None
	    return WordNode(self, row)
	else:
	    sql="select * from semanticTypeNode where node_id=?"
	    self.cursor.execute(sql,(node_id,))
	    row=self.cursor.fetchone()
	    if not row:
	        return None
	    return SemanticTypeNode(self, row)

    def getNodeByPath(self, path):
	sql="select * from tree where path=?"
	self.cursor.execute(sql,(path,))
	row=self.cursor.fetchone()
	if not row:
	    return None
	return self.getNodeByID(row['node_id'])

    def getWordByName(self, name):
	if isinstance(name, str):
	    name=name.decode("UTF-8")
	sql="select * from wordNode where name=?"
	self.cursor.execute(sql,(name,))
	row=self.cursor.fetchone()
	if not row:
	    return None
	return WordNode(self, row)

    def getSemanticTypeByName(self, name):
	if isinstance(name, str):
	    name=name.decode("UTF-8")
	sql="select * from semanticTypeNode where name=?"
	self.cursor.execute(sql,(name,))
	row=self.cursor.fetchone()
	if not row:
	    return None
	return SemanticTypeNode(self, row)


    def searchWord(self, word):
	if isinstance(word, str):
	    word=word.decode("UTF-8")
	sql="select * from wordNode where word=?"
	self.cursor.execute(sql,(word,))
	L=[]
	for row in self.cursor:
	    L.append(WordNode(self,row))
	return L

    def searchSemanticType(self, name):
	if isinstance(name, str):
	    name=name.decode("UTF-8")
	sql="select * from semanticTypeNode where label=?"
	self.cursor.execute(sql,(name,))
	L=[]
	for row in self.cursor:
	    L.append(SemanticTypeNode(self, row))
	return L

    def _guessObj(self, obj):
	p=self.word(obj)
	if p: return p

	p=self.semanticType(obj)
	if p: return p

	p=self.searchWord(obj)
	if p: return p

	p=self.searchSemanticType(obj)
	if p: return p

    def _getPathList(self, obj):
	if isinstance(obj, str) or isinstance(obj, unicode):
	    obj=self._guessObj(obj)

	if isinstance(obj, WordNode) or isinstance(obj, SemanticTypeNode):
	    return obj._getPathList()

	elif isinstance(obj,list):
	    L=[]
	    for x in obj:
	        L+=x._getPathList()
	    return L
	else:
	    return None

    def distance(self, obj1, obj2):
	p1L=self._getPathList(obj1)
	p2L=self._getPathList(obj2)

	min_d=65535
	for p1 in p1L:
	    for p2 in p2L:
		d=distance(p1,p2)
		if d < min_d:
		    min_d=d
	return min_d

    def searchShortestPath(self, obj1, obj2):
	p1L=self._getPathList(obj1)
	p2L=self._getPathList(obj2)

	min_d=65535
	sL=None
	for p1 in p1L:
	    for p2 in p2L:
		(d,L)=searchShortestPath(p1,p2)
		if d < min_d:
		    min_d=d
		    sL=L
	if sL==None:
	    return None

	sPath=[]
	for path in sL:
	    node=self.getNodeByPath(path)
	    sPath.append(node)
	return sPath

    ### function member aliases
    def word(self, name):
	pass

    def semanticType(self, name):
	pass

    word=getWordByName
    semanticType=getSemanticTypeByName

def test1(tree):
    list=tree.searchWord(u"栽培")
    print list
    for node in list:
        print node.getSynonymWordList()
    list=tree.searchWord(u"黃牛")
    print list
    for node in list:
        print node.getSynonymWordList()
    list=tree.searchWord(u"頭痛")
    print list
    for node in list:
        print node.getSynonymWordList()

def test2(tree):
    list=tree.searchWord(u"栽培")
    print list
    for node in list:
        print "*** %s"%node.name.encode("UTF-8")
        print node.getSiblingWordList()
    list=tree.searchWord(u"黃牛")
    print "="*30
    print list
    for node in list:
        print "*** %s"%node.name.encode("UTF-8")
        print node.getSiblingWordList()
    list=tree.searchWord(u"頭痛")
    print "="*30
    print list
    for node in list:
        print "*** %s"%node.name.encode("UTF-8")
        print node.getSiblingWordList()


    #node1=node.getSemanticTypeList()[0]
    #print node1
    #print node1.getAncestorList()
    #print node1.isAncestorOf(node)
    #print node.isDescendantOf(node1)
    #print node1.isAncestorOf(tree.word("開心.Nv,VH.1"))
    #print node.isAncestorOf(tree.word("開心.Nv,VH.1"))
    #print tree.searchShortestPath("開心", "生氣")
    #print node.sid
    #print node.name
    #print node.type
    #print node.word
    #print node.pos
    #print node.ehownet
    #print node.dump()

def test3(tree):
    list=tree.searchWord(u"鴨蛋")
    print list
    for node in list:
        print "*** %s"%node.name.encode("UTF-8")
        #print node.getSiblingWordList()
        print node.getDescendantWordList()
 
def test4(tree):
    print tree.distance("打","開心.Nv,VH.1")

if __name__=="__main__":
    from ehownet import *
    tree=EHowNetTree("../data/ehownet_ontology.sqlite")
    #test1(tree)
    #test2(tree)
    test3(tree)
    #test4(tree)
