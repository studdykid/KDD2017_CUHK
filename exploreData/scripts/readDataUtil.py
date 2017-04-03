import pandas as pd
import numpy as np

def read_trajectory( f1, f2=None):
  if f1[-4:]==".pkl" and f2[-4:]==".pkl":
    df_trajectories = pd.read_pickle(f1)
    df_travel_segment = pd.read_pickle(f2)
  else:
    df_trajectories = pd.read_csv(f1)
    df_trajectories["starting_time"] = pd.to_datetime(df_trajectories["starting_time"])
    df_trajectories['day_of_week'] = df_trajectories['starting_time'].dt.dayofweek
    df_trajectories['minute_block'] = df_trajectories["starting_time"].map( lambda t : "%02d%02d" % (t.hour, int(t.minute/20)*20))
    
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
    
    #df_travel_segment.set_index('starting_time', inplace=True)
    #df_trajectories.set_index('starting_time', inplace=True)

    df_trajectories.to_pickle("df_trajectories.pkl")
    df_travel_segment.to_pickle("df_travel_segment.pkl")
  return (df_trajectories, df_travel_segment)
 

def read_volume(f):
    df_volume = pd.read_csv(f)
    df_volume["time"] = pd.to_datetime(df_volume["time"])
    df_volume['day_of_week']  = df_volume['time'].dt.dayofweek
    df_volume['minute_block'] = df_volume["time"].map( lambda t : "%02d%02d" % (t.hour, int(t.minute/20)*20))
    df_volume.set_index('time', inplace=True)
    return df_volume

def read_weather(f):
    df_weather = pd.read_csv(f)
    df_weather["time"] = pd.to_datetime(df_weather["date"]) + df_weather['hour'].apply( lambda hr : pd.Timedelta(hr, 'h'))
    df_weather.set_index('time', inplace=True)
    return df_weather

