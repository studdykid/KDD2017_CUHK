import pandas as pd
import numpy as np
import datetime
import readDataUtil


datapath = "../../../../data/original_dataset/"
df_trajectories, df_travel_segment = readDataUtil.read_trajectory(datapath+"/training/trajectories_table_5_training.csv")
#df_trajectories, df_travel_segment = readDataUtil.read_trajectory("df_trajectories.pkl", "df_travel_segment.pkl")
df_volume = readDataUtil.read_volume(datapath+"/training/volume_table_6_training.csv")
df_weather = readDataUtil.read_weather(datapath+"/training/weather_table_7_training_update.csv")

times = pd.date_range('09/20/2016' , '10/18/2016', freq="3H")
#times = pd.date_range('09/20/2016' , '09/22/2016', freq="3H")
vols = [(1,0), (1,1), (2,0), (3,0), (3,1)]
routes = [ ("A",2), ("A",3), ("B",1), ("B",3), ("C",1), ("C",3) ]
weather_fields = ['pressure', 'sea_pressure', 'wind_direction',
                  'wind_speed', 'temperature', 'rel_humidity', 'precipitation']
vehicle_class = ['motorcycle', 'cargocar', 'privatecar', 'unknowncar']

# prepare volume data
def get_vehicle_class(row):
  vehicle_type  = row.vehicle_type
  vehicle_model = row.vehicle_model
  if vehicle_type==1 : return 'cargocar'
  if vehicle_model==1 and vehicle_type==0 : return 'motorcycle'
  if vehicle_model>1 and vehicle_type==0 : return 'privatecar'
  return 'unknowncar'

df_volume['vehicle_type'] = df_volume['vehicle_type'].replace(np.nan,-1)
df_volume['vehicle_class'] = df_volume.apply( get_vehicle_class, axis=1)
vehicle_class_volume = df_volume.groupby( ['tollgate_id','direction',pd.TimeGrouper('20min'),'vehicle_class']).size()
etc_volume = df_volume.groupby( ['tollgate_id','direction',pd.TimeGrouper('20min'),'has_etc']).size()
tot_volume = etc_volume.sum(level=[0,1,2])

# prepare route median data
trajectories_median = df_trajectories.set_index('starting_time') \
                                     .groupby(['intersection_id', 'tollgate_id',pd.TimeGrouper('20min')]) \
                                     .travel_time \
                                     .median()

colnames = []
d = {}

# fill time data
colname = 'datetime'
colnames.append(colname)
d[colname] = times

colname = 'dayofweek'
colnames.append(colname)
d[colname] = times.dayofweek

colname = 'hour'
colnames.append(colname)
d[colname] = times.hour

# fill total volume data
for (tid,io) in vols:
  for dt in range(0,240,20):
    col = []
    for aTime in times:
      targetTime = aTime + pd.Timedelta(dt,'m')
      try:
        val = tot_volume.ix[tid,io,targetTime]
      except Exception as e:
        print( "no total volume data for ",tid ,io ,targetTime)
        val = 0
      col.append(val)
    colname = 'dt%i_%s%s_%s_vol' %(dt,tid,io,'total') 
    colnames.append(colname)
    d[colname] = col

# fill etc volume data
for (tid,io) in vols:
  for dt in range(0,240,20):
    col = []
    for aTime in times:
      targetTime = aTime + pd.Timedelta(dt,'m')
      try:
        val = etc_volume.ix[tid,io,targetTime,1]
      except Exception as e:
        print( "no etc volume data for ",tid ,io ,targetTime)
        val = 0
      col.append(val)
    colname = 'dt%i_%s%s_%s_vol' %(dt,tid,io,'etc') 
    colnames.append(colname)
    d[colname] = col

# fill vehicle subclass volume data
for (tid,io) in vols:
  for dt in range(0,240,20):
    for aVClass in vehicle_class:
      col = []
      for aTime in times:
        targetTime = aTime + pd.Timedelta(dt,'m')
        try:
          val = vehicle_class_volume.ix[tid,io,targetTime,aVClass]
        except Exception as e:
          val = 0
        col.append(val)
      colname = 'dt%i_%s%s_%s_vol' %(dt,tid,io,aVClass) 
      colnames.append(colname)
      d[colname] = col

# fill route median data
for dt in range(0,240,20):
  for (p,q) in routes:
    col = []
    for aTime in times:
      targetTime = aTime + pd.Timedelta(dt,'m')
      try:
        val = trajectories_median.ix[p,q,targetTime]
      except Exception as e:
        print( "no route median for ", p, q, targetTime)
        val = np.nan
      col.append(val)
    colname = 'dt%i_%s%s_routetime_median'%(dt,p,q)
    colnames.append(colname)
    d[colname] = col
  
# fill weather data
for dt in [0,180]:
  for w in weather_fields:
    col = []
    srcCol = df_weather[w]
    for aTime in times:
      targetTime = aTime + pd.Timedelta(dt,'m')
      try:
        val = srcCol.ix[targetTime]
      except Exception as e:
        print( "no weather data for ", w, targetTime)
        val = np.nan
      col.append(val)
    colname = 'dt%i_%s'%(dt,w)
    colnames.append(colname)
    d[colname] = col

# fill chinese holiday
def is_holiday(t):
  rdate = t.date()
  if rdate>=datetime.date(2016, 9,15) and rdate<=datetime.date(2016, 9,17): return 1 #mid autum holiday
  if rdate==datetime.date(2016, 9,18): return 0
  if rdate>=datetime.date(2016,10, 1) and rdate<=datetime.date(2016,10, 7): return 1 #national holiday
  if rdate>=datetime.date(2016,10, 8) and rdate<=datetime.date(2016,10, 9): return 0
  if t.dayofweek == 0 or t.dayofweek == 6: return 1 # sun or sat
  return 0 #weekdays

col = []
for aTime in times:
  col.append( is_holiday(aTime) )

colnames.append('is_holiday')
d['is_holiday'] = col
  
print('columns in output table:')
for aColName in colnames:
  print(aColName)


df_merged_volume = pd.DataFrame( data=d , columns=colnames)
df_merged_volume.to_csv('phase1_training_vol_route_weather_joined_table.csv', index=False)
df_merged_volume.to_pickle('phase1_training_vol_route_weather_joined_table.pkl')
