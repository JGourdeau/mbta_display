from numpy import set_printoptions
import requests
import json
import pandas as pd
from datetime import datetime, timezone
from time import sleep
import re

def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)


def subway_sign_data(STOP_ID, API_KEY):
    # get the time of the query 
    CURRENT_TIME = datetime.now(timezone.utc)

    # query the api
    response = requests.get('https://api-v3.mbta.com/predictions?sort=arrival_time&filter[stop]=%s' %STOP_ID)
    if response.status_code != 200:
        print(response.status_code)
        sleep(60)
        response = requests.get('https://api-v3.mbta.com/predictions?sort=arrival_time&filter[stop]=%s' %STOP_ID) 

    response = json.loads(response.text)
    response = response['data']
    
    # print(response[0])

    # set up lists to hold relevant data
    train_ids = []
    arrival_time = []
    trip_id = []
    headsign = []
    min_away = []
    min_away_str = []
    direction = []

    # retrieve the relevant data
    for i in response: 
        # get the train id
        t_id = i['relationships']['vehicle']['data']['id']
        train_ids.append(t_id)
        # get the arrival_time
        ar_time = datetime.fromisoformat(i['attributes']['arrival_time'])
        arrival_time.append(ar_time)
        # get the trip_id from the train 
        trip = i['relationships']['trip']['data']['id']
        trip_id.append(trip)
        # get the direction of the train
        direction_id = int(i['attributes']['direction_id'])
        # print(direction_id)
        if direction_id == 0:
            direction.append('OUTBOUND')
        else: 
            direction.append('INBOUND')
        # get the headsign from the trip id
        trip = json.loads((requests.get('https://api-v3.mbta.com/trips/%s'%trip)).text)
        headsign_txt = trip['data']['attributes']['headsign']
        headsign.append(headsign_txt)
        # get the timedelta
        delta = ar_time - CURRENT_TIME
        seconds = delta.total_seconds()
        tminus = (int(round(seconds/60, 0)))
        min_away.append(tminus)

        if seconds <= 30:
            min_away_str.append('BRD')
        elif seconds <= 60: 
            min_away_str.append('ARR')
        else: 
            min_away_str.append('%s min' %tminus)
        
        

    # create a df of relevant data
    train_df = pd.DataFrame({'train_id':train_ids, 'arrival_time':arrival_time, 'trip_id':trip_id, 
                             'headsign':headsign, 'min_away':min_away, 'min_away_str': min_away_str, 'direction':direction})

    # return only the trains that havent left the stop 
    return train_df.loc[train_df.min_away >= 0, :]


# main
if __name__ == '__main__':
    with open('credentials.txt', 'r') as f:
        API_KEY = f.read().strip()
    STOP_ID = 'place-bvmnl' #70181 #brookline village # is actually the parent_station id

    train_df = subway_sign_data(STOP_ID, API_KEY)
    train_df_in = train_df.loc[train_df.direction=='INBOUND',['headsign', 'min_away_str']]
    train_df_out = train_df.loc[train_df.direction=='OUTBOUND',['headsign', 'min_away_str']]
    
    print('\nINBOUND:')
    print(train_df_in.to_string(index=False, header=False, formatters={"headsign":'{:}'.format, 'min_away_str':'\t\t\t{}'.format})) 
    print('\nOUTBOUND:')
    print(train_df_out.to_string(index=False, header=False, formatters={"headsign":'{:}'.format, 'min_away_str':'\t\t\t{}'.format})) 
    print('\n')
    
    