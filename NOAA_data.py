# NOAA API V2
# Documentation can be found at
# http://www.ncdc.noaa.gov/cdo-web/webservices/v2
# https://github.com/crvaden/NOAA_API_v2
import requests

class NOAAData(object):
    def __init__(self, token):
        # NOAA API Endpoint
        self.url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/'
        self.h = dict(token=token)

    def poll_api(self, req_type, payload):
        # Initiate http request - kwargs are constructed into a dict and passed as optional parameters
        # Ex (limit=100, sortorder='desc', startdate='1970-10-03', etc)
        r = requests.get(self.url + req_type, headers=self.h, params=payload)

        if r.status_code != 200:  # Handle erroneous requests
            print("Error: " + str(r.status_code))
        else:
            r = r.json()
            try:
                # Most JSON results are nested under 'results' key
                return r['results']
            except KeyError:
                return r  # for non-nested results, return the entire JSON string

    # Fetch available datasets
    # http://www.ncdc.noaa.gov/cdo-web/webservices/v2#datasets
    def datasets(self, **kwargs):
        req_type = 'datasets'
        return self.poll_api(req_type, kwargs)

    # Fetch data categories
    # http://www.ncdc.noaa.gov/cdo-web/webservices/v2#dataCategories
    def data_categories(self, **kwargs):
        req_type = 'datacategories'
        return self.poll_api(req_type, kwargs)

    # Fetch data types
    # http://www.ncdc.noaa.gov/cdo-web/webservices/v2#dataTypes
    def data_types(self, **kwargs):
        req_type = 'datatypes'
        return self.poll_api(req_type, kwargs)

    # Fetch available location categories
    # http://www.ncdc.noaa.gov/cdo-web/webservices/v2#locationCategories
    def location_categories(self, **kwargs):
        req_type = 'locationcategories'
        return self.poll_api(req_type, kwargs)

    # Fetch all available locations
    # http://www.ncdc.noaa.gov/cdo-web/webservices/v2#locations
    def locations(self, **kwargs):
        req_type = 'locations'
        return self.poll_api(req_type, kwargs)

    # Fetch All available stations
    # http://www.ncdc.noaa.gov/cdo-web/webservices/v2#stations
    def stations(self, h, p, **kwargs):
        req_type = 'stations'
        return self.poll_api(req_type, kwargs)

    # Fetch information about specific dataset
    def dataset_spec(self, set_code, **kwargs):
        req_type = 'datacategories/' + set_code
        return self.poll_api(req_type, kwargs)

    # Fetch data
    # http://www.ncdc.noaa.gov/cdo-web/webservices/v2#data
    def fetch_data(self, **kwargs):
        req_type = 'data'
        return self.poll_api(req_type, kwargs)

if __name__ == '__main__':
    api_token = "gQtYhJFKlKeiBqrbXaWgTnaUYBNcrCUa"
    location = 'Minneapolis'

    data = NOAAData(api_token)

    #records = data.fetch_data(datasetid='GHCND', locationid='CITY:US270013')
    records = data.fetch_data(datasetid='GHCND',
                              #locationid='CITY:US270013',
                              stationid='GHCND:USC00214884',
                              #datatypeid='TAVG',
                              datatypeid='TOBS',
                              startdate='2023-08-01',
                              enddate='2023-08-31',
                              limit=1000)
    """
    records = data.data_types(datasetid='GHCND', 
                              stationid='GHCND:USC00214884',
                              datacategoryid='TEMP',
                              startdate='2023-05-01',
                              enddate='2023-05-31'
                              )
    """
    #records = data.locations(limit=1000, offset=500)
    #records = data.datasets(locationid='CITY:US270013', limit=100)
    for r in records:
        print(r)

    
    #categories = data.data_categories(locationid='FIPS:37', sortfield='name')

    #for i in categories:
    #    print(i)
