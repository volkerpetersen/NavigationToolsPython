#!/usr/bin/env python
# -- coding: utf-8 --
# ---------------------------------------------------------------------------
__author__ = "Volker Petersen <volker.petersen01@gmail.com>"
__app__ = "NMEA_Websocket_Logging.py"
__version__ = "version 1.0.0, Python >3.11.0"
__date__ = "Date: 2024/03/25"
__copyright__ = "Copyright (c) 2024 Volker Petersen"
__license__ = "GNU General Public License, published by the Free Software Foundation"
__doc__ = """
-----------------------------------------------------------------------------
 Logs lat/lon data at 1) a set frequency per hour, 2) each watch change,
 and 3) 8:00am PST to a gpx route file.
 Using the Websocket protocol.

    requirements:
        https://pypi.org/project/pynmeagps/
        -m pip install --upgrade pynmeagps
        pip install websockets
-----------------------------------------------------------------------------
"""

try:
    import sys
    import os
    import socket
    import pytz
    from time import sleep
    import random
    from datetime import datetime
    from pynmeagps.nmeareader import NMEAReader
    from pynmeagps import latlon2dmm, haversine, bearing
    from NavToolsLib import NavTools

except ImportError as e:
    print(
        f"Import error: {str(e)} \nAborting the program {__app__}")
    sys.exit()


WATCHES = {0: ["Stbd", "Symbol-X-Large-Green"], 
           1: ["Port", "Symbol-X-Large-Red"],
          }
HOST = "169.254.230.248"          # TCP IP address on s/v Andreas
PORT = 2053                       # TCP Port
SOURCE = "TCP"                    # can be TCP or FILE
SOURCE = "File"
MODE = "PRODUCTION"               # can be TEST or PRODUCTION
#MODE = "TEST"
WATCH_CYCLE = 3                   # watches change every 3 hours
WATCH_START = 19                  # hour of the first watch on a trip
WP_FREQ = 10                      # create a waypoint every 10 minutes
DAILY_REPORT = 8                  # hour (local time) of the daily position report
DATE_TIME = "%Y-%m-%d %H:%M:%S"   # date time format
DATE = "%Y-%m-%d"                 # date format
DST = True                        # Daylight Savings Time - True/False
LOCAL_TIME = "US/Pacific"         # local time zone
MSGLEN = 1024                     # TCP message length in bytes
GPS_ID = "RMC"                    # NMEA GPS msgID to be processed

def logging(filename):
    """
    Logs lat/lon data at 1) a set frequency per hour, 2) each watch change,
    and 3) 8:00 PST to a gpx route file.

    Input:
        filename (string) log file name
    """
    logCTR = 0                # count the number of log messenges
    watchChangeEvent = True   # true while we're waiting for next watch change event
    dailyEvent = True         # true while we're waiting for next daily event
    wpEvent = True            # true while we're waiting for next waypoint event
    logEvent = False          # true when a matching log condition was found
    watch = 0                 # ctr to alternate between the 2 watches
    navtools = NavTools()     # create an instance of the Nav Tools Library
    watchHour = WATCH_START%WATCH_CYCLE
    sym = "empty"
    viz = "viz_name>0"
    routeName = os.path.basename(filename)
    routeName = routeName.split(".")[0]

    try:
        HOST = socket.gethostname()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(60)
        client_socket.connect((HOST, PORT))
        #conn, addr = client_socket.connect((HOST, PORT))
        #if conn:
        if client_socket:
            print(f"TCP connection via IP {HOST}:{PORT}")
        else:
            raise Exception("TCP connection error", "unknown", 42)
    except:
        time = datetime.now()
        print(f"\n{time.strftime(DATE_TIME)}: TCP connection at IP {HOST}:{PORT} failed.\n")
        return

    try:
        gpx = navtools.strRANDOMreplace(navtools.gpxHeader)
        gpx = gpx.replace("nameX", routeName)
        with open(filename, 'w') as writer:
            writer.write(gpx)

        # infinate loop terminated by Ctrl-C. Runs every 20 seconds
        tcpError = 0
        while tcpError < 70:
            nmea = None
            #data = conn.recv(MSGLEN)
            data = client_socket.recv(MSGLEN)
            if data:
                nmea = NMEAReader.parse(data, validate=0)
            if (nmea is not None and nmea.msgID == GPS_ID):
                utc = merge_date_time(nmea.date, nmea.time)
                utcStr = utc.strftime(DATE_TIME)+"Z"
                utcStr = utcStr.replace(" ", "T")
                local = utc_to_local(utc, LOCAL_TIME)
                hour = int(local.strftime("%H"))
                minute = int(local.strftime("%M"))
                #print(f"\n{logCTR} - {utc} position: Lat {pos[0]}   Lon {pos[1]}")

                # log with WP_FREQ during each hour starting a 5 past the hour
                if (minute>4 and (minute-5)%WP_FREQ==0 and wpEvent):
                    wpEvent = False
                    logEvent = True
                    name = ""
                    viz = "viz_name>0"  # wp is not visible
                    sym = "empty"

                # log every WATCH_CYCLE starting each day at watchHour
                if (hour>(watchHour-1) and ((hour-watchHour)%WATCH_CYCLE)==0 and watchChangeEvent):
                    watchChangeEvent = False
                    logEvent = True
                    name = F"_{WATCHES[watch%2][0]}"
                    viz = "viz_name>1"  # wp is visible
                    sym = WATCHES[watch%2][1]
                    watch = watch + 1
                    
                # log daily at DAILY_REPORT hour
                if (hour==DAILY_REPORT and dailyEvent):
                    dailyEvent = False
                    logEvent = True
                    name = F"_{DAILY_REPORT}:00_Position"
                    viz = "viz_name>1"  # wp is visible
                    sym = "diamond"

                # save log Events to file
                if logEvent:
                    logEvent = False
                    logCTR = logCTR + 1
                    pos = latlon2dmm(nmea.lat, nmea.lon)
                    print(f"\n{logCTR} - {local.strftime('%H:%M:%S')} {name} Lat {pos[0]}   Lon {pos[1]}")

                    with open(filename, 'a') as writer:
                        wp = navtools.strRANDOMreplace(navtools.gpxWaypoint)
                        wp = wp.replace("latX", f"{nmea.lat:.6f}")
                        wp = wp.replace("lonX", f"{nmea.lon:.6f}")
                        wp = wp.replace("wpX", f"NM{(logCTR):04d}{name}")
                        wp = wp.replace("timeX", utcStr)
                        wp = wp.replace("viz_name>0", viz)
                        wp = wp.replace("empty", sym)
                        writer.write(wp)
                    # end writing to file
                else:
                    # enable waiting for next Event whent current Event 
                    # condition is not any longer true
                    if(hour>DAILY_REPORT):
                        dailyEvent = True
                    if(hour%WATCH_CYCLE)>0:
                        watchChangeEvent = True
                    if(minute>4 and ((minute-5)%WP_FREQ)>0):
                        wpEvent = True
                    print(".", end='')   # indicates valid NMEA read but no Event condition found
            else:
                if(nmea is None):
                    print("?", end='')   # indicates TCP problems
                    tcpError = tcpError + 1
                else:
                    print("!", end='')   # indicates no GPS_ID NMEA GPS sentence found
            #sleep(1)                     # sleep for 1 second
        # end of while loop
        client_socket.close()
    except KeyboardInterrupt:
        print("\nLog Session terminated by user")
        client_socket.close()
        if(os.path.isfile(filename)):
            with open(filename, 'a') as writer:
                writer.write(navtools.gpxFooter)
    

def tcpNMEAread(stream: socket.socket):
    """
    Reads NMEA data from a TCP socket stream.

    Input:
        stream (socket.socket)
    """
    msgcount = 0
    start = datetime.now()
    nmr = NMEAReader(stream, validate=0)
    try:
        for (_, parsed_data) in nmr:
            if (parsed_data.msgID == GPS_ID):
                pos = latlon2dmm(parsed_data.lat, parsed_data.lon)
                print(f"{parsed_data.msgID}: Lat {pos[0]}   Lon {pos[1]}")
            msgcount += 1
    except KeyboardInterrupt:
        dur = datetime.now() - start
        secs = dur.seconds + dur.microseconds / 1e6
        print("Session terminated by user")
        print(
            f"{msgcount:,d} messages read in {secs:.2f} seconds:",
            f"{msgcount/secs:.2f} msgs per second",
        )

def fileNMEAread(filename):
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
                #print(f"\nraw:  {raw_data}")
                if (parsed_data.msgID == GPS_ID):
                    pos = latlon2dmm(parsed_data.lat, parsed_data.lon)
                    utc = merge_date_time(parsed_data.date, parsed_data.time)
                    local = utc_to_local(utc, LOCAL_TIME)
                    utcxx = local_to_utc(local, LOCAL_TIME)
                    print(f"{parsed_data.msgID}: {utc}  Lat {pos[0]}   Lon {pos[1]}")
                    #print(utc, local, utcxx)

                msgcount += 1
            print(f"\nRead and parsed {msgcount} NMEA sentences")
        except Exception as e:
            print(f"Error reading NMEA from file\n{str(e)}")


def NMEAsocket():
    """
    Opens a TCP socket stream.

    Input:
        None
    """
    print(f"Opening socket {HOST}:{PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        tcpNMEAread(sock)

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
    
    if ("TEST" in MODE):
        if("TCP" in SOURCE):
            NMEAsocket()
        elif("File" in SOURCE):
            filename = os.path.join(scriptPath, "nmea_sample.log")
            fileNMEAread(filename)

            # test case
            # 103.0nm / 168T in Expedition
            # 102.8nm / 168T in OpenCPN
            lat1 = 34.062950
            lon1 = -119.9593833330
            lat2 = 32.3883333330
            lon2 = -119.5250
            navtools = NavTools()
            dist = haversine(lat1,lon1,lat2,lon2)*navtools.KM_NM
            hdg = bearing(lat1,lon1,lat2,lon2)
            print(f"\nNMEA:     {dist:.3f}nm  {hdg:.2f}degree")

            dist = navtools.calc_distance(lat1,lon1,lat2,lon2)
            hdg = navtools.calc_heading(lat1,lon1,lat2,lon2)
            print(f"Navtools: {dist:.3f}nm  {hdg:.2f}degree")
        else:
            print(f"\nInvalid program SOURCE ('{SOURCE}')\n")
    elif ("PRODUCTION" in MODE):
        filename = os.path.join(scriptPath, f"gpx_log_{random.randint(0, 9999):04d}.gpx")
        logging(filename)
    else:
        print("\nUnsupport app MODE\n")

    print("\n\nDone!\n")