#!/usr/bin/env python
# -- coding: utf-8 --
# ---------------------------------------------------------------------------
__author__ = "Volker Petersen <volker.petersen01@gmail.com>"
__app__ = "NavToolsLib.py"
__version__ = "version 2.1.0, Python 3.7"
__date__ = "Date: 2016/06/15"
__copyright__ = "Copyright (c) 2016 Volker Petersen"
__license__ = "GNU General Public License, published by the Free Software Foundation"
__doc__ = """
-----------------------------------------------------------------------------
  Program parameters:
	none

	This is a collection of various Navigation Tolls Libraries utilized
	by these scripts:
		RouteConvertUpload.py
		OpenCPN_Route_Analyzer.py
		Navigation_Route_Analyzer.pyw
		uploadAllToernMySQL.py
		uploadMySQL.py
-----------------------------------------------------------------------------
"""

try:
    import sys
    import os
    import inspect
    import json
    from datetime import datetime
    from bs4 import BeautifulSoup
    # import lxml
    import random
    from tabulate import tabulate
    import math
    from PIL import Image, ExifTags
    configFile = 'NavConfig.ini'
    genericWPs = ['NM', 'WPT', 'WP', '0']

except ImportError as e:
    print(f"Import error: {e} \nAborting the program {__version__}s")
    sys.exit()


sql_header = """-- Table structure for table "Table_Name"
CREATE TABLE IF NOT EXISTS "Table_Name" (
"id" INTEGER,
"from" TEXT,
"to" TEXT,
"lat" REAL,
"lon" REAL,
"type" TEXT,
"image" TEXT,
"notes" TEXT,
PRIMARY KEY ("id")
);

DELETE FROM "Table_Name";
--
-- Dumping data for table "Table_Name"
-- roundtrip	=> if first and last waypoint in the file are the same
-- one-way trip => if first and last waypoint are different
--
INSERT INTO "Table_Name" ("id", "from", "to", "lat", "lon", "type", "image", "notes") VALUES\n"""


def saveNavConfig(cwd, route_file):
    """--------------------------------------------------------------------------
    Function to save the settings parameters to file

    Args:
        cwd (string):        string with the working directory
        route_file (string): string with name of the file with the route data

    Return:
        none
    """

    settingsFile = os.path.join(cwd, configFile)

    try:
        with open(settingsFile, 'r') as fr:
            rawSettings = json.load(fr)

        with open(settingsFile, 'w') as fw:
            rawSettings['lastRoute'] = route_file
            txt = json.dumps(rawSettings, indent=2)
            # print(txt))
            fw.write(txt)

    except Exception as e1:
        print(
            f"\nTerminating now due to error:\n'{str(e1)}'\nreading the config file ('{configFile}').")


def getNavConfig(verbose=False):
    """--------------------------------------------------------------------------
    Function to initialize default settings from file and return 
    them in a dictionary

    Args:
        verbose (bool): print program results when True

    Return:
        (dictionary) with the program settings
    """
    settings = {'cwd': '',
                'gpxPath': '',
                'sqlitePath': '',
                'sqliteDB': '',
                'toernDirectory': '',
                'lastRoute': '',
                'skipWP': 'True',
                'noSpeed': 'False',
                'verbose': 'verbose',
                'error': True}

    # fetch the content from the default settings file
    cwd = os.path.dirname(os.path.abspath(
        inspect.getfile(inspect.currentframe())))
    cwd = os.path.normpath(cwd)

    default_settings = os.path.join(cwd, configFile)

    try:
        with open(default_settings, 'r') as fp:
            rawSettings = json.load(fp)

        supported_devices = rawSettings['devices']
        current_device = ''
        for device in supported_devices:
            if (os.path.exists(os.path.normpath(supported_devices[device]))):
                current_device = device

        if (current_device == ''):
            msg = "Unknown computer and root file system"
            raise Exception(msg)

        toernDirectory = os.path.normpath(
            rawSettings['toernDirectory'][current_device])
        gpxPath = os.path.normpath(rawSettings['gpxPath'][current_device])
        sqliteDB = os.path.normpath(rawSettings['sqliteDB'][current_device])
        sqlitePath = os.path.normpath(
            rawSettings['sqlitePath'][current_device])
        last_route = rawSettings['lastRoute']

        if verbose:
            print(f"Configuration file...: '{configFile}'")
            print(f"Device...............: '{current_device}'")
            print(f"GPX path.............: '{gpxPath}'")
            print(f"SQLite path..........: '{sqlitePath}'")
            print(f"SQLite DB............: '{sqliteDB}'")
            print(f"Toern Directory Table: '{toernDirectory}'")
            print(f"Working Dir..........: '{cwd}'")
            print(f"Last GPX Route file..: '{last_route}'")
            print(f"Skip WPs.............: '{rawSettings['skipWP']}'")
            print(f"No Speed.............: '{rawSettings['noSpeed']}'")
            print(f"Verbose..............: '{rawSettings['verbose']}'")

        settings['cwd'] = cwd
        settings['gpxPath'] = gpxPath
        settings['sqlitePath'] = sqlitePath
        settings['sqliteDB'] = sqliteDB
        settings['lastRoute'] = last_route
        settings['toernDirectory'] = toernDirectory
        settings['skipWP'] = rawSettings['skipWP']
        settings['noSpeed'] = rawSettings['noSpeed']
        settings['verbose'] = rawSettings['verbose']
        settings['error'] = True

    except Exception as e1:
        print(
            f"\nTerminating now due to error:\n'{str(e1)}'\nreading the config file ('{configFile}').")
        settings['error'] = configFile

    return settings


def ComputeRouteDistances(xml, verbose, skipWP, noSpeed):
    """--------------------------------------------------------------------------
    Compute the distance, speed, and Etmals between sequential route waypoints
    a <desc></desc> tag/field with these entry options:
        arrival 2019-09-25 19:30    (arrival date/time at this WP)
        departure 2019-09-26 09:37  (departure date/time from this WP)
        timedleg 2019-09-26 09:37   (arrival and departure at/from this WP)
        poi                         (Point of Interest on route not being listed)
        homeport                    (designates the Waypoint from which a round-trip
                                    toern originates. Add departure and arrival
                                    times using the above keywords in add'l lines)
                                    all date are in the in the format yyyy-mm-dd hh:mm

    Args:
        xml (string):   xml code with all the route information from the OpenCPN gpx file
        verbose (bool): run this function with (True) or w/o printout (False)
        skipWP (bool):  skip output for all WPs that are marked with label 'empty'
        noSpeed (bool): True/False - don't/do compute speed and time between waypoints

    Return:
        (string) function results
    """
    global genericWP

    dateFormats = []
    dateFormats.append('%Y_%m_%d_%H%M')
    dateFormats.append('%b-%d-%Y %H:%M')
    dateFormats.append('%Y%m%d_%H%M')
    dateFormats.append('%Y-%m-%d %H:%M')
    dateFormats.append('%Y-%m-%d | %H:%M')

    soup = BeautifulSoup(xml, features="html5lib")

    wps = soup.find_all('rtept')

    rows = []
    last_lat = 0.0
    last_lon = 0.0               # lat/lon of previous WP
    leg_start_date = ""           # date/time at first "timed" WP
    total_trip_distance = 0.0  # total distance traveled on this trip
    leg_distance = 0.0           # distance between two adjacent "timed" WPs
    leg_elapsed = 0.0           # elapsed time between two adjacent "timed" WPs
    departure_flag = False       # set flag to true to indicate start of timed leg
    leg_timed_flag = False       # set flag to true to indicate this leg was timed
    sum_legs_distance = 0.0       # the sum distance traveled on all timed legs
    sum_legs_time = 0.0           # the sum time traveled on all timed legs
    leg_start_date = ""           # initialization
    leg_end_date = ""           # initialization
    # flag that indicates that end of leg is also start of next leg
    timed_flag = False
    wpCTR = 0
    for wp in wps:
        lat = float(wp['lat'])
        lon = float(wp['lon'])
        name = wp.find('name').text
        time = wp.find('time').text
        symbol = (wp.find('sym').text).lower()
        desc = wp.find('desc')

        layover = (symbol == "harbor" or
                   symbol == "circle" or
                   symbol == "service-marina" or
                   symbol == "anchorage")
        if (layover):
            departure_flag = True

        generic = False
        for genericWP in genericWPs:
            generic = (generic or name.startswith(genericWP))

        # handles the speed computations based on the <desc> tag info
        if (desc != None):
            desc = desc.text.lower()
            if (desc.startswith('homeport') and wpCTR == 0):
                if ('departure' in desc):
                    desc_arr = desc.split('\n')
                    desc = desc_arr[1]

            if (desc.startswith('homeport') and wpCTR > 0):
                if ('arrival' in desc):
                    desc_arr = desc.split('\n')
                    desc = desc_arr[2]

            if (desc.startswith('departure')):
                time = desc.replace('departure ', '')
                leg_start_date = StringToDateTime(time, dateFormats)
                # print(f"departure - Leg start: {leg_start_date} at: {name}")
                departure_flag = True

            if (desc.startswith('arrival')):
                time = desc.replace('arrival ', '')
                leg_end_date = StringToDateTime(time, dateFormats)
                # print(f"arrival      - Leg start: {leg_start_date} end: {leg_end_date} at: {name}")
                if (departure_flag):
                    leg_timed_flag = True
                    departure_flag = False
                else:
                    leg_timed_flag = False

            if (desc.startswith('timedleg')):
                time = desc.replace('timedleg ', '')
                leg_end_date = StringToDateTime(time, dateFormats)
                # print(f"timedleg  - Leg start: {leg_start_date} end: {leg_end_date} at: {name}")
                leg_timed_flag = True
                departure_flag = True
                timed_flag = True

            if (desc.startswith('poi')):
                generic = True

        if (last_lat != 0.0 and last_lon != 0.0):
            distance = calc_distance(last_lat, last_lon, lat, lon)
        else:
            distance = 0.0

        leg_distance += distance
        total_trip_distance += distance

        last_lat = lat
        last_lon = lon

        if (leg_timed_flag or not generic):
            # compute speed / etmal for the current leg from leg_start_date to leg_end_date
            speed = 0
            etmal = 0
            if (isinstance(leg_start_date, datetime) and isinstance(leg_end_date, datetime)):
                elapsed = leg_end_date-leg_start_date
                leg_elapsed = elapsed.days*24+elapsed.seconds/3600.0
                if leg_elapsed > 0.0:
                    speed = leg_distance / leg_elapsed
                    etmal = leg_distance * 24.0/leg_elapsed
                sum_legs_distance += leg_distance
                sum_legs_time += leg_elapsed

            if (lat >= 0.0):
                lat_str = "%7.3fN" % lat
            else:
                lat_str = "%7.3fS" % math.fabs(lat)

            if (lon >= 0.0):
                lon_str = "%7.3fE" % lon
            else:
                lon_str = "%7.3fW" % math.fabs(lon)

            if noSpeed:
                rows.append([name, lat_str, lon_str, leg_distance])
            else:
                rows.append([name, lat_str, lon_str, leg_distance,
                             leg_elapsed, speed, etmal])
            leg_elapsed = 0
            leg_distance = 0
            leg_timed_flag = False
            if (timed_flag):
                timed_flag = False
                leg_start_date = leg_end_date
            leg_end_date = ""

        # end of if (leg_timed_flag or not generic):
        wpCTR = wpCTR + 1
    # end of the loop accross all WPs  "for wp in wps:"

    msg = ""
    if noSpeed:
        msg += (tabulate(rows, headers=["WP Name", "Lat", "Lon",
                                        "Distance"], floatfmt=',.2f', numalign="right"))
    else:
        msg += (tabulate(rows, headers=["WP Name", "Lat", "Lon", "Distance",
                                        "Time", "Speed", "Etmal"], floatfmt=',.2f', numalign="right"))

    msg += (f"\n\nTotal Trip Distance: {total_trip_distance:9,.2f}nm")
    if (not noSpeed):
        msg += (f"\nTimed Legs Distance: {sum_legs_distance:9,.2f}nm")
        msg += (f"   ({sum_legs_distance/total_trip_distance:.2%})")
    if (sum_legs_time != 0.0 and not noSpeed):
        avg_speed = sum_legs_distance / sum_legs_time
        msg += (f"\nAverage Speed:          {avg_speed:9,.2f}kts")

    if verbose:
        print(msg)
    return msg


def get_decimal_coordinates(info):
    """--------------------------------------------------------------------------
        helper function to print a string
    Args:
        info (string): string to be printed

    Returns:
        none
    """
    print(f"Lat {info}")


def addImagesToRoute(path):
    """--------------------------------------------------------------------------
    Function to add images to route file based to the image geo tags and the 
    proximity to a given waypoint
    https://www.sylvaindurand.org/gps-data-from-photos-with-python/

    Args:
        path (string): path (including filename) for the image

    Return:
        none
    """

    points = []
    print(f"searching path: '{path}'")
    for r, d, f in os.walk(path):
        for file in f:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                filepath = os.path.join(r, file)
                img = Image.open(filepath)
                exif = img.getexif()
                latlong = None
                if exif is not None:
                    exif_dict = dict(exif)
                    for key, val in exif_dict.items():
                        if key in ExifTags.TAGS and 'GPSInfo' in ExifTags.TAGS[key]:
                            print(
                                f"testing file '{file.lower()}': {repr(val)} ")
                            latlong = get_decimal_coordinates((repr(val)))
                    if latlong is not None:
                        points.append(latlong)
                        print(
                            f"Image {f} taken at {points[0]:.4f} / {points[0]:.4f}")
                else:
                    print(exif)


def calc_distance(latFrom, lonFrom, latTo, lonTo):
    """--------------------------------------------------------------------------
        compute the distance between two lat/lon positions
        in nautical miles (nm)

    Args:
        latFrom (float): starting point latitude in degress
        lonFrom (float): starting point longitude in degress
        latto (float):   ending point latitude in degress
        lonTo (float):   ending point longitude in degress

    Return:
        (float) distance in nm
    """

    KM_NM = 0.5399565                 # km to nm conversion factor
    # Earth RADIUS (in km) as per Google Maps converted to nm
    RADIUS = 6378.137*KM_NM
    dLat = math.radians(latTo - latFrom)
    dLon = math.radians(lonTo - lonFrom)
    lat1 = math.radians(latFrom)
    lat2 = math.radians(latTo)

    a = math.sin(dLat / 2.0) * math.sin(dLat/2.0) + math.sin(dLon /
                                                             2.0) * math.sin(dLon/2.0) * math.cos(lat1) * math.cos(lat2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return RADIUS * c


def StringToDateTime(dateString, dateFormats):
    """--------------------------------------------------------------------------
        convert a string to a datetime format. Return a 0 if the 
        conversion failed

    Args:
        dateString (string):  string with a date to be converted
        dateFormats (string): date formatting string (e.g. 'YYYY-mm-dd')

    Return:
        (datetime object) converted date
    """
    for dt_format in dateFormats:
        try:
            dateValue = datetime.strptime(dateString, dt_format)
            return dateValue
        except ValueError:
            dateValue = 0
    return dateValue


def parseSQLRouteFile(pathGPX, pathSQL, filename):
    """--------------------------------------------------------------------------
        parse the GPX route data into a MySQL query file

    Args:
        pathGPX (string):  path to the gpx file location
        pathSQL (string):  path to the sql file location
        filename (string): name of the file

    Return:
        (string) with the log messages
    """

    today = datetime.now()
    log_msg = ""
    rows = []

    try:
        if (".gpx" in filename):
            filename1 = filename
            filename = filename.replace(".gpx", "")
        else:
            filename1 = filename + ".gpx"

        fn1 = os.path.join(pathGPX, filename1)
        inputFile = open(fn1, "r")
        xml = inputFile.read()
        inputFile.close()
    except:
        print(f"Error opening file: {fn1}")
        return False

    soup = BeautifulSoup(xml)
    ctr = 0
    wps = soup.find_all('rtept')

    filename2 = filename+".sql"
    fn2 = os.path.join(pathSQL, filename2)

    # print(f"gpx file: {filename1} \ngpx path: {fn1}")
    # print(f"sql file: {filename2} \nsql path: {fn2}")

    outputFile = open(fn2, "w")

    output = sql_header.replace('Table_Name', filename)

    ctr = 0
    wp_ctr = 1
    old_lat = 0.0
    old_lon = 0.0
    cum_dist = 0.0
    total = 0.0
    txt = ""
    for wp in wps:
        # print wp.contents      # converts BeautifulSoup content to list
        # print wp.contents[3].string, "Type: "+wp.contents[5].string
        # i = 0
        # for s in wp.contents:
        #      print i, ":", s,
        #      i += 1
        # print "|----end of wp content!"

        name = wp.find('name').text
        if wp.find('sym') is None:
            symbol = "empty"
        else:
            symbol = (wp.find('sym').text).lower()
        if (wp.find('desc')):
            notes = "'"+(wp.find('desc').text)+"'"
            desc = (wp.find('desc').text).lower()
        else:
            notes = "' '"
            desc = ""

        if name.startswith('NM') or name.startswith('WP') or name.startswith('0'):
            name = 'WP' + str(wp_ctr).zfill(4)
            wp_ctr += 1
        lat = wp['lat']
        lon = wp['lon']
        if (ctr == 0):
            output += "(" + str(ctr)+", '"+name+"', '" + name + "', " + \
                "'" + str(lat) + "', '" + str(lon) + "', 'harbor', '', ''),\n"
            route = 'harbor'
            first_lat = lat
            first_lon = lon
            old_name = name
        if (ctr > 0):
            """
            -----------------------------------------------------------------
            in OpenCPN mark Waypoints as follows in <sym></sym> tag:
            "diamond" for "regular WP on route"
            "empty" for "no WP display on route"
            "circle" or "harbor" or "service-marina" for "Harbor"
            "anchorage" for "Mooring / Anchorage"
            ------------------------------------------------------------------
            """
            distance = calc_distance(old_lat, old_lon, float(lat), float(lon))
            cum_dist = cum_dist + distance
            total = total + distance
            if lat == first_lat and lon == first_lon:
                route = 'harbor'
                txt = txt + \
                    "WP%d: arrived after final leg at '%s' %s after %0.2fnm.\n" % (
                        ctr, route, name, cum_dist)
            else:
                if 'anchorage' in symbol:
                    route = 'mooring'
                    # print ("WP%d arrived after final leg at '%s' %s after %0.2fnm." %(ctr, route, name, cum_dist))
                    txt = txt + \
                        ("WP%d: arrived after final leg at '%s' %s after %0.2fnm.\n" % (
                            ctr, route, name, cum_dist))
                    cum_dist = 0.0
                elif 'circle' in symbol or 'harbor' in symbol or 'service' in symbol:
                    route = 'harbor'
                    # print ("WP%d arrived after final leg at '%s' %s after %0.2fnm." %(ctr, route, name, cum_dist))
                    txt = txt + \
                        ("WP%d: arrived after final leg at '%s' %s after %0.2fnm.\n" % (
                            ctr, route, name, cum_dist))
                    cum_dist = 0.0
                elif ('poi' in desc):
                    route = 'route'
                elif ('diamond' in symbol and name.startswith('WP0')):
                    route = 'none'
                elif 'empty' in symbol:
                    route = 'none'
                else:
                    route = 'route'
            output += "(" + str(ctr)+", '" + old_name + "', '" + name + \
                "', " + "'" + str(lat) + "', '" + str(lon) + "', '"
            output += route + "', '', " + notes + "),\n"
        # print(f"from: {old_name}  to: {name}")
        old_name = name
        rows.append([ctr, name, lat, lon, route])
        old_lat = float(lat)
        old_lon = float(lon)
        ctr += 1
    # print (f"Total trip across {ctr} waypoints: {total:0.2f}nm.")
    txt = txt + (f"Total trip across {ctr} waypoints: {total:,.2f}nm.")
    output = output[:-2] + ";"
    outputFile.write(output)
    outputFile.close()
    # print(tabulate(rows, headers=["WP #", "Name", "Latitude", "Longitude", "Route"], floatfmt=',.4f', numalign="right"))

    msg = (f"\n==> {today.strftime('%Y-%m-%d        %H:%M:%S')}"
           f"\nRoute Parsing Function"
           f"\nDone, parsed a total of {ctr} waypoints "
           f"from the OpenCPN route file:\n'{pathGPX}'\nsaved to:\n'{pathSQL}'\n\n")
    msg += txt + "\n\n"
    log_msg = msg + log_msg
    return log_msg


def parseKMLRouteFile(pathGPX, filename, boatname):
    """--------------------------------------------------------------------------
    Function to parse the waypoint and route information from a .kml file
    into a GPS file.
    Yellowbrick race tracking route files are available at
    https://yb.tl/racenamexyz.kml

    Args:
        pathGPX (string):  path to the gpx file location
        filename (string): name of the file
        boatname (string): name of the boat in the .kml file

    Return:
        (string) with the log messages
    """

    today = datetime.now()
    log_msg = ""
    ctr = 0

    gpxRoute = """<?xml version="1.0" encoding="utf-8"?>
<gpx creator="OpenCPN" version="1.1" xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3" xmlns:opencpn="http://www.opencpn.org" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
<rte>
<name>nameX</name>
<extensions>
<opencpn:guid>715affff-de7d-4094-9e87-RANDOM</opencpn:guid>
<opencpn:viz>1</opencpn:viz>
<opencpn:start>Start</opencpn:start>
<opencpn:end>End</opencpn:end>
<opencpn:planned_speed>5.00</opencpn:planned_speed>
<opencpn:time_display>PC</opencpn:time_display>
</extensions>
"""

    gpxRouteWP = """<rtept lat="latX" lon="lonX">
<time>timeX</time>
<name>wpX</name>
<sym>empty</sym>
<type>WPT</type>
<extensions>
<opencpn:guid>715bffff-e783-458a-87cf-RANDOM</opencpn:guid>
<opencpn:viz_name>0</opencpn:viz_name>
<opencpn:auto_name>1</opencpn:auto_name>
<opencpn:arrival_radius>0.050</opencpn:arrival_radius>
<opencpn:waypoint_range_rings colour="#FF0000" number="0" step="-1" units="0" visible="false"/>
</extensions>
</rtept>"""
    gpxRouteEnd = "</rte></gpx>"

    try:
        pathKML = os.path.join(pathGPX, filename+".kml")
        inputFile = open(pathKML, "r")
        xml = inputFile.read()
        inputFile.close()
    except:
        print(f"Error opening file: {pathKML}")
        return False
    pathGPX = os.path.join(pathGPX, filename+".gpx")
    outputfile = open(pathGPX, "w")
    kml = BeautifulSoup(xml, "xml")
    records = kml.find_all("ns2:Placemark")
    locations = []
    times = []
    if len(records):
        # print(f"\nfound {len(records)} boat names")
        ctr = 0
        for record in records:
            boat = record.find_all("ns2:name")
            if boatname.lower() in boat[0].contents[0].lower():
                # print(f"\n\nfound our boat: {boat[0].contents[0]}\n")
                #siblings = list(record.next_siblings)
                # print(len(siblings))
                times = record.find_all("ns2:when")
                locations = record.find_all("gx:coord")
                break
            ctr += 1

        if len(locations) != 0 and len(locations) == len(times):

            # build the GPX route file
            rndDigits = (f"{random.randint(0, 0xFFFFFFFFFFFF):12x}")
            gpx = gpxRoute
            gpx = gpx.replace("nameX", filename)
            gpx = gpx.replace("RANDOM", rndDigits)
            for ctr in range(0, len(locations)):
                rndDigits = (f"{random.randint(0, 0xFFFFFFFFFFFF):12x}")
                wp = gpxRouteWP
                wp = wp.replace("RANDOM", rndDigits)
                latlon = locations[ctr].contents[0].split(",")
                wp = wp.replace("latX", latlon[1])
                wp = wp.replace("lonX", latlon[0])
                wp = wp.replace("timeX", times[ctr].contents[0])
                wp = wp.replace("wpX", "NM{:05d}".format(ctr+1))
                gpx += wp
            # of of loop over all waypoint in the KML file
            gpx += gpxRouteEnd
            outputfile.write(gpx)

            log_msg += (
                f"Done, parsed a total of {ctr} waypoints for boat '{boatname}' ")
            log_msg += (
                f"from the KML route file {pathKML} to the OpenCPN route file{pathGPX}\n")
        else:
            log_msg += (
                f"Found inconsistent number of or no location ({len(locations)}) and date ({len(times)}) records. Couldn't parse the KML route info for boat '{boatname}'.\n")
    else:
        log_msg += (
            f"Found no route information in the KML file ('{pathKML}').\n")

    outputfile.close()

    return log_msg


if __name__ == "__main__":
    """-------------------------------------------------------------------------
        Script starting point
    """
    print(f"\nStarting {__app__}")
    print(__doc__)

    settings = getNavConfig(verbose=True)

# dictionary with keys:
# {cwd, gpxPath, sqlitePath, lastGPX, lastRoute, skipWP, noSpeed, verbose, error}
