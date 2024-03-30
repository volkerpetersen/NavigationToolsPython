#!/usr/bin/env python
# -- coding: utf-8 --
# ------------------------------------------------------------------------------
__author__ = "Volker Petersen <volker.petersen01@gmail.com>"
__app__ = "ECMWF Data App"
__version__ = "Version: 2.1.5, Python 3.11"
__date__ = "Date: 2023/12/29"
__copyright__ = "Copyright (c) 2023 Volker Petersen"
__license__ = "GNU General Public License, published by the Free Software Foundation"
__doc__ = """
--------------------------------------------------------------------------------
 ECMWF API V2
 Documentation can be found at
 https://cds.climate.copernicus.eu/cdsapp

 Designed to fetch historical grib files from the ECMWF site
--------------------------------------------------------------------------------
"""
try:
    import os
    import sys
    import cdsapi
except ImportError as e:
    print(f"Import error: {str(e)}\nAborting the program {__app__}")
    sys.exit()


requestName = 'reanalysis-era5-single-levels'
requestTransPac = {
        'product_type': 'reanalysis',
        'variable': [
            '10m_u_component_of_neutral_wind', '10m_u_component_of_wind', 
            '10m_v_component_of_neutral_wind', '10m_v_component_of_wind', 
            'total_precipitation',
        ],
        'year': '2022',
        'month': ['07', '08'],
        'day': [
            '01', '02', '03',
            '04', '05', '06',
            '07', '08', '09',
            '10', '11', '12',
            '13', '14', '15',
            '16', '17', '18',
            '19', '20', '21',
            '22', '23', '24',
            '25', '26', '27',
            '28', '29', '30',
            '31',
        ],
        'time': [
            '00:00', '01:00', '02:00',
            '03:00', '04:00', '05:00',
            '06:00', '07:00', '08:00',
            '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00',
            '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00',
            '21:00', '22:00', '23:00',
        ],
        'area': [
            35, -160, 18.5,
            -116,
        ],
        'format': 'grib',
    }

requestSantaBarbara = {
        'product_type': 'reanalysis',
        'variable': [
            '10m_u_component_of_neutral_wind', '10m_u_component_of_wind', 
            '10m_v_component_of_neutral_wind', '10m_v_component_of_wind', 
            'total_precipitation',
        ],
        'year': '2023',
        'month': ['06'],
        'day': [
            '01', '02', '03',
            '04', '05', '06',
            '07', '08', '09',
            '10', '11', '12',
            '13', '14', '15',
        ],
        'time': [
            '00:00', '01:00', '02:00',
            '03:00', '04:00', '05:00',
            '06:00', '07:00', '08:00',
            '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00',
            '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00',
            '21:00', '22:00', '23:00',
        ],
        'area': [
            34.6, -121, 32,
            -116.5,
        ],
        'format': 'grib',
    }


if __name__ == '__main__':
    print(f"\nStarting {__app__}")
    print(__doc__)
    
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    rootPath = os.path.dirname(scriptPath)
    downloadPath = os.path.normpath("E:\My Documents\Downloads\gribs")

    api_token = "ef703f5c-0781-4e92-a10e-224a5759685a"
    UID = '163699'
    key = f"{UID}:{api_token}"
    url = "https://cds.climate.copernicus.eu/api/v2"

    c = cdsapi.Client(url=url, key=key)

    filename = "2023_SantaBabara_ecmwf.grib"
    if(os.path.isdir(downloadPath)):
        filename = os.path.normpath(os.path.join(downloadPath, filename))
    else:
        filename = os.path.normpath(os.path.join(scriptPath, filename))
    
    print(F"storing the GRIB data in '{filename}'\n")

    #c.retrieve(requestName, requestTransPac, filename)
    c.retrieve(requestName, requestSantaBarbara, filename)
    