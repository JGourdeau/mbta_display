# imports
import pandas as pd
import requests
import json
import pandas as pd
from datetime import datetime, timezone
from time import sleep
import tkinter as tk
from tkinter import Frame


'''prints out a json object in a nice structure'''
def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)


'''Uses the MBTA V3 api to query the predictions of a stop and reterns the incoming and outgoing
train arrival time deltas in two seperate dataframes'''
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
        # print(i)
        # if the schedule relationship is not 'skipped'
        if i['attributes']['schedule_relationship'] != 'SKIPPED':
            # get the train id
            t_id = i['relationships']['vehicle']['data']['id']
            train_ids.append(t_id)
            # get the arrival_time
            ar_time = i['attributes']['arrival_time']
            print(ar_time)
            if ar_time:
                ar_time = datetime.fromisoformat(i['attributes']['arrival_time'])
                arrival_time.append(ar_time)
            else: 
                ar_time = datetime.fromisoformat(i['attributes']['departure_time'])
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
            if not('schedBasedVehicle' in t_id):

                vehicle = requests.get('https://api-v3.mbta.com/vehicles/%s?api_key=%s'%(t_id, API_KEY))
                # print(vehicle.status_code)
                vehicle = json.loads(vehicle.text)
        
                vehicle_status = vehicle['data']['attributes']['current_status']

                #print(vehicle_status)
                current_stop = int(vehicle['data']['relationships']['stop']['data']['id'])
                #print(current_stop)
            
            else: 
                vehicle_status = 'NOT_YET_ACTIVE'

            # set the min string for the display
            if seconds <= 90 and vehicle_status == 'STOPPED_AT' and current_stop in CHILDREN_PLATFORMS:
                min_away_str.append('..BRD..')
            elif seconds <= 30:
                min_away_str.append('..ARR..')
            else: 
                min_away_str.append('%s min' %str(tminus).zfill(2))
        
    # create a df of relevant data
    train_df = pd.DataFrame({'train_id':train_ids, 'arrival_time':arrival_time, 'trip_id':trip_id, 
                             'headsign':headsign, 'min_away':min_away, 'min_away_str': min_away_str,
                             'direction':direction})

    # return only the trains that havent left the stop 
    train_df = train_df.loc[(train_df.min_away >= 0), :].copy().sort_values('min_away')
    
    train_df_in = train_df.loc[train_df.direction=='INBOUND',['headsign', 'min_away_str']]
    train_df_out = train_df.loc[train_df.direction=='OUTBOUND',['headsign', 'min_away_str']]
    
    last_in = min(10, len(train_df_in))
    last_out = min(10, len(train_df_out))

    return train_df_in.reindex().iloc[0:last_in, :], train_df_out.reindex().iloc[0:last_out, :]


'''simple text output screen generation using the dataframes of incoming and outgoing trains'''
def update_screen(STOP_ID, API_KEY):
    train_df_in, train_df_out = subway_sign_data(STOP_ID, API_KEY)
    ret = '\nLOCATION:  ' + STOP_ID + '\n'
    ret = ret + '\n' + ('-------------------------------\n') + ("|  Last Updated: %s  |\n" %datetime.now().strftime("%I:%M:%S %p")) 
    ret = ret + ('-------------------------------\n') 
    if len(train_df_in) == 0:
        ret = ret + ('\nINBOUND:\n') + 'No Departures' + ('\n')
    else: 
        ret = ret + ('\nINBOUND:\n') + (train_df_in.to_string(header=False, index=False, col_space = [20, 20])) + ('\n')
    if len(train_df_out) == 0: 
        ret = ret + ('\nOUTBOUND:\n') + 'No Departures' + ('\n')
    else:
        ret = ret + ('\nOUTBOUND:\n') + (train_df_out.to_string(header=False, index=False, col_space = [20, 20])) + ("\n") #col_space=[20,20],
    
    station_update["text"] = ret

    return


'''reads in credential file and returns the api_key'''
def get_credentials(cred_file):
    with open(cred_file, 'r') as f:
        API_KEY = f.read().strip()
    return API_KEY


def place_bvmnl():
    # set the stop ID
    global STOP_ID 
    global CHILDREN_PLATFORMS
    STOP_ID = 'place-bvmnl' # brookline village.
    CHILDREN_PLATFORMS = [70180, 70181]
    update_screen(STOP_ID, API_KEY)


def place_cool():
    global STOP_ID 
    global CHILDREN_PLATFORMS
    STOP_ID = 'place-cool'
    CHILDREN_PLATFORMS = [70219, 70220]
    update_screen(STOP_ID, API_KEY)


'''update the preds'''
def update():
    # get the times to arrival in a dataframe
    update_screen(STOP_ID, API_KEY)
    window.after(10000, update) # run itself again after 1000 ms

# main
if __name__ == '__main__':
    
    # read in the api_key
    API_KEY = get_credentials('credentials.txt')
    
    # initialize window
    window = tk.Tk()
    window.geometry('400x600+50+50')
    window.configure(bg='black')
    window.title('MBTA Station Screen')
    station_update = tk.Label(fg="orange", justify='right', width=30, height=80, padx=25, bg='black') 
    station_update.config(highlightbackground = "orange", highlightcolor= "orange")
    f = Frame(window)

    btn_1 = tk.Button(f,
                      text = "Brookline Village",
                      command = place_bvmnl, 
                      pady=25, fg='black', activeforeground='orange', highlightbackground='orange')
    btn_2 = tk.Button(f, 
                      text='Coolidge Corner', 
                      command=place_cool, 
                      pady=25, fg='black', activeforeground='orange', highlightbackground='orange')
    
    btn_1.pack(side='left')
    btn_2.pack(side='right')
    f.pack()
    station_update.pack()
    
    
    # set default to place_bvmnl()
    place_bvmnl()
 
    # get the times to arrival in a dataframe
    update()
    window.mainloop()

    

    