import requests
import pandas as pd
import time
from datetime import datetime
import sys
import os
from elasticsearch import Elasticsearch
from elasticsearch import helpers

es_client = Elasticsearch(http_compress=True)


def get_data():
    url = 'http://api.citybik.es/v2/networks/citybikes-helsinki'
    try:
        res = requests.get(url)
        city_bikes = res.json()
        df = pd.DataFrame.from_dict(city_bikes['network']['stations'])
        df = df[1:].drop('extra', axis=1) #Discard first row, drop 'extra' column
        df['timestamp'] = df['timestamp'].apply(safe_date)
        return df
    except requests.exceptions.ConnectionError:
        print('{}: Connection failed'.format(stamp))
        sys.exit(1)

def safe_date(date_value):
    return (
        pd.to_datetime(date_value) if not pd.isna(date_value)
            else  datetime(1970,1,1,0,0)
    )

def doc_generator(df):
    df_iter = df.iterrows()
    for index, document in df_iter:
        yield {
                "_index": 'your_index',
                "_type": "_doc",
                "_id" : f"{document['id']}",
                "_source": document.to_dict(),
            }
    raise StopIteration

if __name__ == '__main__':
    data = get_data()
    helpers.bulk(es_client, doc_generator(data))

