#!/usr/bin/env python
# -- coding: utf-8 --
# ---------------------------------------------------------------------------
__author__ = "Volker Petersen <volker.petersen01@gmail.com>"
__app__ = "NMEA_TCP_Server.py"
__version__ = "version 1.0.0, Python >3.11.0"
__date__ = "Date: 2024/03/25"
__copyright__ = "Copyright (c) 2024 Volker Petersen"
__license__ = "GNU General Public License, published by the Free Software Foundation"
__doc__ = """
-----------------------------------------------------------------------------
 test server to generate TCP NMEA messenges

    requirements:
        https://pypi.org/project/pynmeagps/
        -m pip install --upgrade pynmeagps
-----------------------------------------------------------------------------
"""

try:
    import sys
    import os
    import socket
    import pytz
    from time import sleep
    from datetime import datetime
    from pynmeagps.nmeareader import NMEAReader
    from pynmeagps import latlon2dmm, haversine, bearing
    from NavToolsLib import NavTools

except ImportError as e:
    print(
        f"Import error: {str(e)} \nAborting the program {__app__}")
    sys.exit()

HOST = "10.11.13.110"             # TCP IP address
PORT = 2053                       # TCP Port
DATE_TIME = "%Y-%m-%d %H:%M:%S"   # date time format
DATE = "%Y-%m-%d"                 # date format
MSGLEN = 1024                     # TCP message length in bytes
GPS_ID = "RMC"                    # NMEA GPS msgID to be processed
LOCAL_TIME = "US/Pacific"         # local time zone


def fileNMEAread(filename, conn):
    """
    Read NMEA data from file.

    Input:
        filename: name of the NMEA log file to parse
    """
    msgcount = 0
    with open(filename, 'rb') as stream:
        nmr = NMEAReader(stream, nmeaonly=True, validate=0)
        try:
            for (raw_data, parsed_data) in nmr:
                #print(f"Msg {msgcount:3d} - parsed_data.msgID")
                if (parsed_data.msgID == GPS_ID):
                    pos = latlon2dmm(parsed_data.lat, parsed_data.lon)
                    utc = merge_date_time(parsed_data.date, parsed_data.time)
                    local = utc_to_local(utc, LOCAL_TIME)
                    utcxx = local_to_utc(local, LOCAL_TIME)
                    print(f"SERVER: {parsed_data.msgID}: {utc}  Lat {pos[0]}   Lon {pos[1]}")
                    #print(utc, local, utcxx)
                    conn.send(raw_data)
                msgcount += 1
                sleep(1)
            print(f"\nRead and parsed {msgcount} NMEA sentences")
        except Exception as e:
            print(f"SERVER shutdown.\nError:'{str(e)}'")

def merge_date_time(date, time):
    """
    Combine the NMEA GPS time and date into one dt object

    Input:
        dt object with NMEA gps time 
        dt object with NMEA gps date

    Return:
        utc dt object
    """
    dateStr = date.strftime("%Y-%m-%d")
    utc = datetime.strptime(dateStr+" "+time.strftime("%H:%M:%S"), DATE_TIME)
    return utc

def utc_to_local(utc_dt, tz=LOCAL_TIME):
    """
    Convert UTC dt to local timezone

    Input:
        utc dt object
        tz timezone designator

    Return:
        dt object with local time
    """
    local_tz = pytz.timezone(tz)
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_dt.astimezone(local_tz)

def local_to_utc(local_dt, tz=LOCAL_TIME):
    """
    Convert local timezone to UTC dt

    Input:
        local dt object
        tz timezone designator

    Return:
        dt object with UTC time
    """
    if(local_dt.tzinfo is None or local_dt.tzinfo.utcoffset(local_dt) is None):
        local_tz = pytz.timezone(tz)
        local_dt = local_tz.localize(local_dt, is_dst=DST)  # Localize the datetime
    
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt

if __name__ == "__main__":
    print(f"\nStarting {__app__} {__version__}\n{__doc__}")
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    
    filename = os.path.join(scriptPath, "nmea_sample.log")

    host = socket.gethostname()
    port = 2053  # initiate port no above 1024
    print(f"Server is connecting to {host} {port}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # get instance
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(2)
    conn, address = server_socket.accept()  # accept new connection
    print("SERVER: Received connection at: " + str(address))

    for i in range(1):
        print(f"\n{i+1}. time thru the gpx file....")
        fileNMEAread(filename, conn)

    conn.close()
    server_socket.close()

    print("\n\nDone!\n")