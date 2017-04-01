import pandas as pd
import numpy as np
import matplotlib
from graph_tool.all import *

#==================================================================== 
# load data
#==================================================================== 
df_trajectories = None
df_travel_segment = None

reparse = False

if reparse:
  df_trajectories = pd.read_csv('../dataSets/training/trajectories_table_5_training.csv')
  df_trajectories["starting_time"] = pd.to_datetime(df_trajectories["starting_time"])
  
  idx=0
  link_id =[]
  starting_time = []
  travel_time = []
  for aRow in df_trajectories["travel_seq"]:
    if (idx%1000==0): print(idx)
    idx+=1
    segments = aRow.split(";")
    for aSeg in segments:
      data = aSeg.split("#")
      #df_travel_segment.append([ data[0], pd.datetime.strptime(data[1], '%Y-%m-%d %H:%M:%S'), float(data[2])], ignore_index=True)
      link_id.append(data[0])
      starting_time.append(pd.datetime.strptime(data[1], '%Y-%m-%d %H:%M:%S'))
      travel_time.append(float(data[2]))
  
  df_travel_segment = pd.DataFrame( {
                                      "link_id"       : link_id,
                                      "starting_time" : starting_time,
                                      "travel_time"   : travel_time,
                                    })
  df_travel_segment['day_of_week'] = df_travel_segment['starting_time'].dt.dayofweek
  df_travel_segment['minute_block'] = df_travel_segment["starting_time"].map( lambda t : "%02d%02d" % (t.hour, int(t.minute/20)*20))
  
  df_trajectories.to_pickle("df_trajectories.pkl")
  df_travel_segment.to_pickle("df_travel_segment.pkl")

else:
  df_trajectories = pd.read_pickle("df_trajectories.pkl")
  df_travel_segment = pd.read_pickle("df_travel_segment.pkl")

#==================================================================== 
# group data be weekday and/or 20min bin
#==================================================================== 

df_trajectories['day_of_week'] = df_trajectories['starting_time'].dt.dayofweek
df_trajectories['minute_block'] = df_trajectories["starting_time"].map( lambda t : "%02d%02d" % (t.hour, int(t.minute/20)*20))

avg_segment_time_week = df_travel_segment.groupby( ['day_of_week', 'minute_block', 'link_id']).aggregate(np.average)
avg_route_time_week   = df_trajectories.groupby( ['intersection_id', 'tollgate_id', 'day_of_week', 'minute_block',]).aggregate(np.average)
avg_route_time_whole  = df_trajectories.groupby( ['intersection_id', 'tollgate_id', pd.TimeGrouper( key="starting_time", freq="20min"), ] ).aggregate(np.average)

#===========================================================
#Plot speed of network, averaged over whole data period
#===========================================================
g = load_graph("phase1_road_network.gt")

tmpTxt = g.new_edge_property("string")
tmpWidth = g.new_edge_property("double")
tmpColor = g.new_edge_property("vector<double>")
tmpAvgTime = avg_segment_time_week.mean(level=2) #level=2 means average over same link_id

for e in g.edges():
  #tmpTxt[e] = "%s %.0fm %d" %( eName[e], eLen[e], eLanes[e])
  tmpTxt[e] = "%.2f" % (g.ep.eLen[e]/tmpAvgTime.ix[ g.ep.eName[e] ])
  tmpColor[e] = matplotlib.cm.gist_heat((g.ep.eLen[e]/tmpAvgTime.ix[ g.ep.eName[e] ]).ix[0]/15.) #15ms-1 as max speed in color map
  tmpWidth[e] = 3*g.ep.eLanes[e]

graph_draw(g,
           pos=g.vp.vPos,
           vertex_text=g.vp.vName, vertex_font_size=18,
           edge_text=tmpTxt, edge_font_size=18, edge_color=tmpColor,
           edge_pen_width=tmpWidth,
           output_size=(1000, 600)
          )

graph_draw(g,
           pos=g.vp.vPos,
           vertex_text=g.vp.vName, vertex_font_size=18,
           edge_text=tmpTxt, edge_font_size=18, edge_color=tmpColor,
           edge_pen_width=tmpWidth,
           output_size=(1000, 600),
           output= "phase1_road_network_avgspeed.png"
          )

#===========================================================
#Plot speed of network by 20min interval on week folded data
#===========================================================
#for day in range(7):
#  for hh in range(24):
#    for mm in [0,20,40]:
#      hhmm = "%02d%02d" % (hh,mm)
#      
#      for e in g.edges():
#        try:
#          tmpSpeed = (g.ep.eLen[e]/avg_segment_time_week.ix[ day, hhmm, g.ep.eName[e] ]).ix[0]
#        except Exception as err:
#          print(err)
#          tmpSpeed = 999.
#        tmpTxt[e] = "%.2f" % tmpSpeed
#        tmpColor[e] = matplotlib.cm.gist_heat(tmpSpeed/15.) #15ms-1 as max speed in color map
#        tmpWidth[e] = 3*g.ep.eLanes[e]
#      
#      graph_draw(g,
#                 pos=g.vp.vPos,
#                 vertex_text=g.vp.vName, vertex_font_size=18,
#                 edge_text=tmpTxt, edge_font_size=18, edge_color=tmpColor,
#                 edge_pen_width=tmpWidth,
#                 output_size=(1000, 600),
#                 output= "phase1_road_network_avgspeed_day%d_%s.png" % (day, hhmm)
#                )
#      print("Plotted ", "phase1_road_network_avgspeed_day%d_%s.png" % (day, hhmm))

#===========================================================
#Make dataframe of route travel time by 20min interval on week folded data
#===========================================================
routes = [ ("A",2), ("A",3), ("B",1), ("B",3), ("C",1), ("C",3) ]
routeTime = { aRoute:[] for aRoute in routes }
for day in range(7):
  for hh in range(24):
    for mm in [0,20,40]:
      hhmm = "%02d%02d" % (hh,mm)
      
      for (startPt, endPt) in routes:
        try:
          t = avg_route_time_week.ix[startPt,endPt, day, hhmm]['travel_time']
        except Exception as err:
          print(err)
          t = np.nan
        routeTime[(startPt, endPt)].append( t )
routeTime = pd.DataFrame ( routeTime, index=pd.date_range('1/10/2100' , '1/16/2100 23:59:59', freq='20min'))

#===========================================================
#Make prediction by looking up the average route travel time by 20min interval on week folded data
#===========================================================
f = open("simple_avg_predict.csv","w")
print('"intersection_id","tollgate_id","time_window","avg_travel_time"', file=f)

dates = pd.date_range('10/18/2016' , '10/24/2016')
hours = [8,9,17,18]
for aDate in dates:
  for hh in hours:
    for mm in [0,20,40]:
      hhmm = "%02d%02d" % (hh,mm)
      
      for (startPt, endPt) in routes:
        try:
          t = avg_route_time_week.ix[startPt,endPt, aDate.dayofweek, hhmm]['travel_time']
        except Exception as err:
          print("no pass record for this time", err)
          t = np.nan
        startT = aDate + np.timedelta64(hh,'h') + np.timedelta64(mm,'m')
        endT = startT + np.timedelta64(20,'m')
        outRow = [ startPt, endPt, "[%s,%s)"%(startT, endT), t ]
        outRow = [ "\"%s\"" % i for i in outRow]
        outRow = ",".join(outRow)
        print(outRow, file=f)
f.close()
