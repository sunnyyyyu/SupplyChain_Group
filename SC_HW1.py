#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().system('pip install googlemaps')
get_ipython().system('pip install polyline')
get_ipython().system('pip install folium')
get_ipython().system('pip install geopy')


# In[2]:


import pandas as pd
import math
import scipy.optimize as opt
from geopy.geocoders import GoogleV3
import googlemaps
import polyline
import folium

# Enter your own API key
geolocator = GoogleV3(api_key='AIzaSyBxtYQ9SdK6YDHZphghPoZUT9dnmWBAuoM')
gmaps = googlemaps.Client(key='AIzaSyBxtYQ9SdK6YDHZphghPoZUT9dnmWBAuoM')


# ##  Define functions

# In[3]:


# Define functions for calculating haversine distance and driving distance
# Great circle ("as crow flies") distance
def calc_dist_haversine(lat1, lng1, lat2, lng2):
  lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])

  a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
  dist_haversine_miles = 3959 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

  return dist_haversine_miles

# Function to calculate travel distance from origin to each destination
def calc_dist_driving(lat1, lng1, lat2, lng2):

    # Request directions and get travel distance and travel time
    directions = gmaps.directions( (lat1, lng1), (lat2, lng2), mode='driving', units='imperial')

    dist_travel_mile = (directions[0]['legs'][0]['distance']['value']) // 1609.344

    return dist_travel_mile


# In[4]:


# Define function to add lat and lng
# get lat and lng for neighborhood
def get_geocode(location):
    full_location = f"{location}, Atlanta, GA"  # Append 'Atlanta, GA' to the location
    try:
        coords = geolocator.geocode(full_location)
        if coords:
            lat = round(coords.latitude, 4)
            lng = round(coords.longitude, 4)
            return lat, lng
        else:
            return None, None
    except Exception as e:
        print(f"Error geocoding {full_location}: {e}")
        return None, None


# ## Load data and transfer data type

# In[6]:


# load data into python and change data type
data = pd.read_csv("~/Desktop/24 Spring/599R_4102_Supply/group_hw1/ATL_location.csv")
data = data.dropna()
data['Population'] = pd.to_numeric(data['Population'].str.replace(',', ''))
data['Neighborhood'] = data['Neighborhood'].astype(str)


# In[7]:


data


# In[8]:


# sort data and select neignborhood with top 10 population
data_10 = data.sort_values(by='Population', ascending = False).head(10)


# In[9]:


# add geocodes for each address in data_10
data_10[['Lat', 'Lng']] = data_10['Neighborhood'].apply(lambda x: pd.Series(get_geocode(x) if x is not None else (None, None)))


# In[10]:


data_10 # top 10 neignborhoods


# In[13]:


# define function to calculate the total haversine distance
def calc_total_haversine_distance(point, data):
    total_distance = sum(calc_dist_haversine(point[0], point[1], lat, lng) for lat, lng in zip(data['Lat'], data['Lng']))
    return total_distance

# define function to calculate the total driving distancce
def calc_total_driving_distance(point, data):
    total_distance = sum(calc_dist_driving(point[0], point[1], lat, lng) for lat, lng in zip(data['Lat'], data['Lng']))
    return total_distance


# In[14]:


### Step 1: First we find optimal point using Haversine distance
initial_guess = [data_10['Lat'].mean(), data_10['Lng'].mean()]
bounds = [(data_10['Lat'].min() - 5, data_10['Lat'].max() + 5), (data_10['Lng'].min() - 5, data_10['Lng'].max() + 5)]
result_haversine = opt.minimize(calc_total_haversine_distance, initial_guess, args=(data_10,), method='SLSQP', bounds=bounds)
haversine_address = gmaps.reverse_geocode(result_haversine.x)[0]['formatted_address']
print("Optimal location using haversine distance is:", haversine_address)


# In[16]:


### Step 2: Then we find driving distance using Google Maps Direction API
diff = 0.05  
step_size = 0.02 

ranges = (slice(result_haversine.x[0] - diff, result_haversine.x[0] + diff, step_size), slice(result_haversine.x[1] - diff, result_haversine.x[1] + diff, step_size))

result_driving = opt.brute(calc_total_driving_distance, ranges, args=(data_10,), full_output=True, finish=None)
driving_address = gmaps.reverse_geocode(result_driving[0])[0]['formatted_address']
print("Optimal location using driving distance is:", driving_address)


# ## Function to show the map

# In[17]:


# function to show the map
import folium
import googlemaps
from googlemaps import directions
import polyline

# initialize the map centered around the mean of all locations in data_10
initial_guess = [data_10['Lat'].mean(), data_10['Lng'].mean()]
m = folium.Map(location=initial_guess, zoom_start=12)

# add markers for optimal locations
folium.Marker(result_haversine.x, popup=haversine_address, icon=folium.Icon(color='orange')).add_to(m)  # Point using Haversine distance
folium.Marker(result_driving[0], popup=driving_address, icon=folium.Icon(color='green')).add_to(m)  # Point using Driving distance

# add markers and draw driving paths for each location in data_10
for i in range(len(data_10)):
    start = tuple(result_driving[0])
    end = (data_10['Lat'].iloc[i], data_10['Lng'].iloc[i])

    # Add markers for locations from data_10
    folium.Marker([data_10['Lat'].iloc[i], data_10['Lng'].iloc[i]], popup=data_10['Neighborhood'].iloc[i]).add_to(m)
    
    # Get directions using Google Maps Directions API from optimal point to all locations
    directions = gmaps.directions(start, end, mode="driving")
    # Extract polyline points from API response and add to Folium map
    points = polyline.decode(directions[0]['overview_polyline']['points'])
    # Add driving path on the map
    folium.PolyLine(locations=points, color='blue', weight=5).add_to(m)


# In[18]:


# show map
display(m)


# In[ ]:




