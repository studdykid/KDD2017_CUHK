from graph_tool.all import *
import pandas as pd
import numpy as np
import pickle

def load_road_network(linksFileName, routeFileName):
  links  =  pd.read_csv(linksFileName)
  routes =  pd.read_csv(routeFileName)
  
  g = Graph()
  g.vertex_properties["vName"]    = vName      = g.new_vertex_property("string")
  g.edge_properties["eName"]      = eName      = g.new_edge_property("string")
  g.edge_properties["eLen"]       = eLen       = g.new_edge_property("double")
  g.edge_properties["eWidth"]     = eWidth     = g.new_edge_property("double")
  g.edge_properties["eLanes"]     = eLanes     = g.new_edge_property("double")
  g.edge_properties["eLaneWidth"] = eLaneWidth = g.new_edge_property("double")
  
  vDict = {} # multiple key could map to same node obj
  
  
  for idx,aLink in links.iterrows():
  
    inLinks = []
    outLinks = []
    if type(aLink["in_top"])!=float:
      inLinks= aLink["in_top"].split(",")
    if type(aLink["out_top"])!=float:
      outLinks= aLink["out_top"].split(",")
    
  
    aliasList = [ "i" + str(aLink["link_id"]) ]
    aliasList+= [ "o" + aInLink for  aInLink in  inLinks]
  
    v1 = None
    for alias in aliasList:
      if v1 : break
      if alias in vDict:
        v1 = vDict[alias]
  
    if not v1:  
      v1 = g.add_vertex()
  
    for alias in aliasList:
      if alias not in vDict:
        vDict[alias] = v1
  
  
    aliasList = [ "o" + str(aLink["link_id"]) ]
    aliasList+= [ "i" + aOutLink for  aOutLink in  outLinks]
  
    v2 = None
    for alias in aliasList:
      if v2 : break
      if alias in vDict:
        v2 = vDict[alias]
  
    if not v2:  
      v2 = g.add_vertex()
  
    for alias in aliasList:
      if alias not in vDict:
        vDict[alias] = v2
  
    e = g.add_edge(v1, v2)
    eName[e] = str(aLink["link_id"])
    eLen[e] = aLink["length"]
    eWidth[e] = aLink["width"]
    eLanes[e] = aLink["lanes"]
    eLaneWidth[e] = aLink["lane_width"]
  
  for idx,aRoute in routes.iterrows():
    routeSeq= aRoute["link_seq"].split(",")
    v = vDict["i"+routeSeq[0]]
    vName[v] = aRoute["intersection_id"]
    v = vDict["o"+routeSeq[-1]]
    vName[v] = aRoute["tollgate_id"]

  return g


if __name__=="__main__":
  import sys
  if len(sys.argv)!=4:
    print( "Usage: python3 load_road_network.py linksFileName routeFileName outputPrefix")

  g = load_road_network(sys.argv[1], sys.argv[2])
  outputPrefix = sys.argv[3]
  
  tmpTxt = g.new_edge_property("string")
  tmpWidth = g.new_edge_property("double")
  
  #plot graph with road length to inteactive window
  for e in g.edges():
    #tmpTxt[e] = "%s %.0fm %d" %( eName[e], eLen[e], eLanes[e])
    tmpTxt[e] = "%.0fm" % g.ep.eLen[e]
    tmpWidth[e] = 3*g.ep.eLanes[e]
  
  pos,sel = graph_draw(g,
                       vertex_text=g.vp.vName, vertex_font_size=18,
                       edge_text=tmpTxt, edge_font_size=18,
                       edge_pen_width=tmpWidth,
                       output_size=(1000, 600)
                      )

  g.vertex_properties["vPos"] = pos

  #draw graph with road length
  graph_draw(g,
             pos=pos,
             vertex_text=g.vp.vName, vertex_font_size=18,
             edge_text=tmpTxt, edge_font_size=18,
             edge_pen_width=tmpWidth,
             output_size=(1000, 600),
             output= outputPrefix + "_length.png"
            )
  
  #draw graph with road ID
  for e in g.edges():
    tmpTxt[e] = "%s" % g.ep.eName[e]
    tmpWidth[e] = 3*g.ep.eLanes[e]
  
  graph_draw(g,
             pos=pos,
             vertex_text=g.vp.vName, vertex_font_size=18,
             edge_text=tmpTxt, edge_font_size=18,
             edge_pen_width=tmpWidth,
             output_size=(1000, 600),
             output= outputPrefix + "_id.png"
            )
  
  #draw graph with road lanes
  for e in g.edges():
    tmpTxt[e] = "%d" % g.ep.eLanes[e]
    tmpWidth[e] = 3*g.ep.eLanes[e]
  
  graph_draw(g,
             pos=pos,
             vertex_text=g.vp.vName, vertex_font_size=18,
             edge_text=tmpTxt, edge_font_size=18,
             edge_pen_width=tmpWidth,
             output_size=(1000, 600),
             output= outputPrefix + "_lanes.png"
            )

  g.save( outputPrefix + ".gt")
  
    
    
