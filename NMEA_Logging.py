#!/usr/bin/env python
# -- coding: utf-8 --
# ---------------------------------------------------------------------------
__author__ = "Volker Petersen <volker.petersen01@gmail.com>"
__app__ = "NMEA_Logging.py"
__version__ = "version 1.0.0, Python >3.11.0"
__date__ = "Date: 2024/03/25"
__copyright__ = "Copyright (c) 2024 Volker Petersen"
__license__ = "GNU General Public License, published by the Free Software Foundation"
__doc__ = """
-----------------------------------------------------------------------------
 Logs lat/lon data at 1) a set frequency per hour, 2) each watch change,
 and 3) 8:00am PST to a gpx route file.

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
    import time
    import random
    from datetime import datetime
    from pynmeagps.nmeareader import NMEAReader
    from pynmeagps import latlon2dmm
    from NavToolsLib import NavTools

except ImportError as e:
    print(
        f"Import error: {str(e)} \nAborting the program {__app__}")
    sys.exit()


WATCHES = {0: ["Stbd", "Symbol-X-Large-Green"], 
           1: ["Port", "Symbol-X-Large-Red"],
          }
HOST = "169.254.230.248"          # TCP IP address
PORT = 2053                       # TCP Port
SOURCE = "TCP"                    # can be TCP or FILE
SOURCE = "File"
MODE = "PRODUCTION"               # can be TEST or PRODUCTION
MODE = "TEST"
WATCH_CYCLE = 3                   # watches change every 3 hours
WP_FREQ = 10                      # create a waypoint every 10 minutes
DAILY_REPORT = 8                  # hour (local time) of the daily position report
DATE_TIME = "%Y-%m-%d %H:%M:%S"   # date time format
DATE = "%Y-%m-%d"                 # date format
DST = True                        # Daylight Savings Time - True/False
LOCAL_TIME = "US/Pacific"         # local time zone
MSGLEN = 1024                     # TCP message length in bytes


def logging(filename):
    """
    Logs lat/lon data at a 1) set frequency per hour, 2) at each watch change,
    and 3) at 8:00 PST to a gpx route file.

    Input:
        filename (string) log file name
    """
    logCTR = 0
    watchChange = True        # true while we're waiting for next watch change
    dailyEvent = True         # true while we're waiting for next daily event
    wpEvent = True            # true while we're waiting for next waypoint event
    logEvent = False          # true when a matching log condition was found
    watch = 0                 # ctr to alternate between the 2 watches
    navtools = NavTools()
    sym = "empty"
    viz = "viz_name>0"
    routeName = os.path.basename(filename)
    routeName = routeName.split(".")[0]

    try:
        socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.settimeout(10)
        conn, addr = socket.connect((HOST, PORT))
        if conn:
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
        while True:
            nmea = None
            data = conn.recv(MSGLEN)
            if data:
                nmea = NMEAReader.parse(data)
            if (nmea is not None and nmea.msgID == 'RMC'):
                utc = merge_date_time(nmea.date, nmea.time)
                utcStr = utc.strftime(DATE_TIME)+"Z"
                utcStr = utcStr.replace(" ", "T")
                local = utc_to_local(utc, LOCAL_TIME)
                hour = int(local.strftime("%H"))
                minute = int(local.strftime("%M"))
                #print(f"\n{logCTR} - {utc} position: Lat {pos[0]}   Lon {pos[1]}")
                if ((hour%WATCH_CYCLE)==0 and watchChange):
                    watchChange = False
                    logEvent = True
                    name = WATCHES[watch%2][0]
                    viz = "viz_name>1"  # wp is visible
                    sym = WATCHES[watch%2][1]
                    watch = watch + 1
                    
                if ((hour%DAILY_REPORT)==0 and dailyEvent):
                    dailyEvent = False
                    logEvent = True
                    name = F"{DAILY_REPORT}:00_Position"
                    viz = "viz_name>1"  # wp is visible
                    sym = "diamond"

                # log with WP_FREQ during each hour starting a 5 past the hour
                if ((minute-5)%WP_FREQ==0 and wpEvent):
                    wpEvent = False
                    logEvent = True
                    name = ""
                    viz = "viz_name>0"  # wp is not visible
                    sym = "empty"

                # save log Events to file
                if logEvent:
                    logEvent = False
                    logCTR = logCTR + 1
                    pos = latlon2dmm(nmea.lat, nmea.lon)
                    print(f"\n{logCTR} - {utc} position: Lat {pos[0]}   Lon {pos[1]}")

                    with open(filename, 'a') as writer:
                        wp = navtools.strRANDOMreplace(navtools.gpxWaypoint)
                        wp = wp.replace("latX", f"{nmea.lat:.6f}")
                        wp = wp.replace("lonX", f"{nmea.lon:.6f}")
                        wp = wp.replace("wpX", f"NM{(logCTR):04d}_{name}")
                        wp = wp.replace("timeX", utcStr)
                        wp = wp.replace("viz_name>0", viz)
                        wp = wp.replace("empty", sym)
                        writer.write(wp)
                    # end writing to file
                else:
                    # enable waiting for next Event whent current Event 
                    # condition is not any longer true
                    if(hour%DAILY_REPORT)>0:
                        dailyEvent = True
                    if(hour%WATCH_CYCLE)>0:
                        watchChange = True
                    if((minute-5)%WP_FREQ)>0:
                        wpEvent = True
                    print(".",)   # indicate valid read but no Event condition found
            else:
                print("?",)       # indicate TCP problems or no RMC sentence
            time.sleep(2)
        # end of while loop
    except KeyboardInterrupt:
        print("\nLog Session terminated by user")
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
    nmr = NMEAReader(stream)
    try:
        for (_, parsed_data) in nmr:
            if (parsed_data.msgID == 'RMC' or parsed_data.msgID == 'GGA'):
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
        nmr = NMEAReader(stream, nmeaonly=True)
        try:
            for (raw_data, parsed_data) in nmr:
                #print(f"\nraw:  {raw_data}")
                if (parsed_data.msgID == 'RMC'):
                    pos = latlon2dmm(parsed_data.lat, parsed_data.lon)
                    utc = merge_date_time(parsed_data.date, parsed_data.time)
                    print(f"{parsed_data.msgID}: Time: {parsed_data.time}  Lat {pos[0]}   Lon {pos[1]}")
                    local = utc_to_local(utc, LOCAL_TIME)
                    utcxx = local_to_utc(local, LOCAL_TIME)
                    print(utc, local, utcxx)

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
        else:
            print(f"\nInvalid program SOURCE ('{SOURCE}')\n")
    elif ("PRODUCTION" in MODE):
        filename = os.path.join(scriptPath, f"gpx_log_{random.randint(0, 9999):04d}.gpx")
        logging(filename)
    else:
        print("\nUnsupport app MODE\n")

    print("\n\nDone!\n")