import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px

st.title ('Motor Vehicle Collisions in New York City')
st.markdown ('This is a Streamlit dashboard for analyzing motor vehicle collisions in NYC')

def load_data (nrows):
    return pd.read_csv (
        './data.csv', 
        nrows = nrows,
        parse_dates = [['CRASH DATE', 'CRASH TIME']] 
    )

def pre_process (data):
    data.rename (
        lambda x: str (x).lower(), 
        axis = 'columns', 
        inplace = True
    )
    data.dropna (
        subset = ['latitude', 'longitude'],
        inplace = True
    )
    data = data [(data['latitude'] != 0) & (data['longitude'] != 0)]
    data.rename (
        columns = { "crash date_crash time": 'date/time' },
        inplace = True
    )
    return data

@st.cache (persist = True)
def ready_data (nrows):
    data = load_data (nrows)
    data = pre_process (data)
    return data

# presentation questions
def where_are_most_people_injured (data):
    st.header ('Where are the most people injured in NYC?')
    injured_persons = st.slider ('Number of persons injured in vehicle collisions', 1, 19)
    st.map (
        data.query ('`number of persons injured` >= @injured_persons')[['latitude', 'longitude']]
        .dropna (how = 'any')
    )

def breakdown_by_minute (data, hour):
    st.markdown ('Breakdown by minute between %i:00 and %i:00' % (hour, (hour + 1) % 24))
    hist = np.histogram (
        data['date/time'].dt.minute,
        bins = 60,
        range= (0, 60)
    )[0]
    fig = px.bar (
        pd.DataFrame ({
            "minute": range (60),
            "crashes": hist
        }), 
        x = 'minute', 
        y = 'crashes', 
        hover_data = ['minute', 'crashes'], 
        height = 400
    )
    st.write (fig)

def how_many_collisions_occur_during_given_time (data):
    st.header ('How many collisions occur during a given time of day?')
    hour = st.slider ('Hour to observe', 0, 23)
    data = data[data['date/time'].dt.hour == hour]
    st.markdown ('Vehicle collisions between %i:00 and %i:00' % (hour, (hour + 1) % 24))

    midpoint = (
        np.average (data['latitude']),
        np.average (data['longitude'])
    )

    st.write (pdk.Deck(
        map_style = 'mapbox://styles/mapbox/light-v9',
        initial_view_state = {
            "latitude": midpoint[0],
            "longitude": midpoint[1],
            "zoom": 11,
            "pitch": 50
        },
        layers = [
            pdk.Layer (
                'HexagonLayer', 
                data = data[['date/time', 'latitude', 'longitude']],
                get_position = ['longitude', 'latitude'],
                radius = 100,
                extruded = True,
                pickable = True,
                elevation_scale = 4,
                elevation_range = [0, 1000]
            )
        ]
    ))
    breakdown_by_minute (data, hour)

def most_dangerous_streets (data, n):
    st.header ('Top %d most dangerous streets by affected type' % (n))
    select = st.selectbox ('Affected type of people', ['Pedestrians', 'Cyclists', 'Motorists'])

    column = ''
    if select == 'Pedestrians':
        column = 'number of pedestrians injured'
    elif select == 'Cyclists':
        column = 'number of cyclist injured'
    else:
        column = 'number of motorist injured'
    
    st.write (
        data.query('`%s` >= 1' % (column))[['on street name', column]]
        .sort_values (by = column, ascending = False)
        .dropna (how = 'any')[:n]
    )
        


data = ready_data (100000)
where_are_most_people_injured (data)
how_many_collisions_occur_during_given_time (data)
most_dangerous_streets (data, 5)

if st.checkbox ('Show Raw Data', False):
    st.subheader ('Raw Data')
    st.write (data)