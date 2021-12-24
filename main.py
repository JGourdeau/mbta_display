from re import S
from pandas.core.frame import DataFrame
import requests
import json
import pandas as pd
from datetime import date, datetime, timezone
from time import sleep


def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

def get_predictions(API_KEY, STOP_ID):
    try: 
        response = requests.get('https://api-v3.mbta.com/predictions?api_key=%s&sort=arrival_time&filter[stop]=%s' %(API_KEY, STOP_ID))
        response = json.loads(response.text)
        response = response['data']
        return response
    except:
        raise ValueError


def subway_sign_data(STOP_ID, API_KEY):
    # get the time of the query 
    CURRENT_TIME = datetime.now(timezone.utc)

    # query the api
    try: 
        response = requests.get('https://api-v3.mbta.com/predictions?api_key=%s&sort=arrival_time&filter[stop]=%s' %(API_KEY, STOP_ID))
        # load the response data
        response = json.loads(response.text)
        response = response['data']
    except:
        # handle too many requests
        print(response.status_code)
        sleep(60)
        response = requests.get('https://api-v3.mbta.com/predictions?api_key=%s&sort=arrival_time&filter[stop]=%s' %(API_KEY, STOP_ID))
        # load the response data
        response = json.loads(response.text)
        response = response['data']

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
        trip = json.loads((requests.get('https://api-v3.mbta.com/trips/%s?api_key=%s'%(trip, API_KEY)).text))
        headsign_txt = trip['data']['attributes']['headsign']
        headsign.append(headsign_txt)

        # get the timedelta
        delta = ar_time - CURRENT_TIME
        seconds = delta.total_seconds()
        tminus = (int(round(seconds/60, 0)))
        min_away.append(tminus)

        # get the vehicle status
        vehicle = requests.get('https://api-v3.mbta.com/vehicles/%s?api_key=%s'%(t_id, API_KEY))
        # print(vehicle.status_code)
        vehicle = json.loads(vehicle.text)
        
        vehicle_status = vehicle['data']['attributes']['current_status']
        current_stop = vehicle['data']['relationships']['stop']['data']['id']

        # set the min string for the display
        if seconds <= 90 and vehicle_status == 'STOPPED_AT' and current_stop in [70180, 70181]:
            min_away_str.append('BRD')
        elif seconds <= 30:
            min_away_str.append('ARR')
        else: 
            min_away_str.append('%s min' %tminus)
        
    # create a df of relevant data
    train_df = pd.DataFrame({'train_id':train_ids, 'arrival_time':arrival_time, 'trip_id':trip_id, 
                             'headsign':headsign, 'min_away':min_away, 'min_away_str': min_away_str,
                             'direction':direction})

    # return only the trains that havent left the stop 
    return train_df.loc[train_df.min_away >= 0, :]


# main
if __name__ == '__main__':
    # stop_data = json.loads(requests.get('https://api-v3.mbta.com/stops/%s' %('place-bvmnl')).text)
    # jprint(stop_data)

    with open('credentials.txt', 'r') as f:
        API_KEY = f.read().strip()
    STOP_ID = 'place-bvmnl' # brookline village...this actually the parent station id

    train_df = subway_sign_data(STOP_ID, API_KEY)
    train_df_in = train_df.loc[train_df.direction=='INBOUND', ['headsign', 'min_away_str']]
    train_df_out = train_df.loc[train_df.direction=='OUTBOUND', ['headsign', 'min_away_str']]
    
    print('\n')
    print("%s" %datetime.now())
    print('INBOUND:')
    print(train_df_in.to_string(header=False, index=False, col_space=[20,20], justify=['left', 'right']))
    print('OUTBOUND:')
    print(train_df_out.to_string(header=False, index=False, col_space=[20,20], justify=['left', 'right']))
    print("\n")
    