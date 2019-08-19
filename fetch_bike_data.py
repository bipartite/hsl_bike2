import requests
import pandas as pd
import time
from datetime import datetime
import sys
import os
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch_dsl import GeoPoint

es_client = Elasticsearch(http_compress=True)

GeoPoint.to_dict = lambda self: {'lat': self.lat, 'lon': self.lon}

def get_data():
    url = 'http://api.citybik.es/v2/networks/citybikes-helsinki'
    try:
        res = requests.get(url)
        city_bikes = res.json()
        df = pd.DataFrame.from_dict(city_bikes['network']['stations'])
        df = df[1:].drop('extra', axis=1) #Discard first row, drop 'extra' column
        df['timestamp'] = df['timestamp'].apply(safe_date)
        df['location'] = df[['latitude', 'longitude']].apply(create_geopoint, axis=1)
        return df
    except requests.exceptions.ConnectionError:
        print('{}: Connection failed'.format(stamp))
        sys.exit(1)

def safe_date(date_value):
    return (
        pd.to_datetime(date_value) if not pd.isna(date_value)
            else  datetime(1970,1,1,0,0)
    )

def create_geopoint(row):
    return {'lat': row['latitude'], 'lon': row['longitude']}

def doc_generator(df):
    df_iter = df.iterrows()
    ts = time.time()
    stamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H')
    for index, document in df_iter:
        yield {
                "_index": 'hsl_bike_{0}'.format(stamp),
                "_type": "_doc",
                "_id" : f"{document['id']}",
                "_source": document.to_dict(),
            }
    raise StopIteration

if __name__ == '__main__':
    data = get_data()
    helpers.bulk(es_client, doc_generator(data))

