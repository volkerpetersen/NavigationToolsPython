#!/usr/bin/env python
# -- coding: utf-8 --
# ---------------------------------------------------------------------------
__author__ = "Volker Petersen <volker.petersen01@gmail.com>"
__app__ = "NavToolsLib.py"
__version__ = "version 2.1.0, Python >3.7"
__date__ = "Date: 2016/06/15"
__copyright__ = "Copyright (c) 2016 Volker Petersen"
__license__ = "GNU General Public License, published by the Free Software Foundation"
__doc__ = """
-----------------------------------------------------------------------------
  NavTools Class parameters:
	none

	This is a collection of various Navigation Tools utilized
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
    import re
    from datetime import datetime, timedelta
    from bs4 import BeautifulSoup
    import lxml
    import random
    from tabulate import tabulate
    from collections import Counter
    import math
    import sqlite3
    from PIL import Image, ExifTags

except ImportError as e:
    print(
        f"Import error: {str(e)} \nAborting the program {__app__} {__version__}")
    sys.exit()


class NavTools:
    def __init__(self):
        # same values as used in the Toerns Website "plotroute.html"
        # calculations match Expedition but not OpenCPN
        # Earth RADIUS (in km) as per Google Maps converted to nm
        self.KM_NM = 0.539956803            # km to nm conversion factor
        self.RADIUS = 6378.2334*self.KM_NM  # earth radius in nm
        self.configFile = 'NavConfig.ini'
        self.genericWPs = ['NM', 'WPT', 'WP', '0']
        self.WPtypes = ['harbor', 'circle', 'service-marina', 'anchorage']
        self.sql_header = """CREATE TABLE IF NOT EXISTS "Table_Name" (
        "id" INTEGER UNIQUE,
        "name" TEXT,
        "lat" REAL,
        "lon" REAL,
        "type" TEXT,
        "image" TEXT,
        "notes" TEXT,
        PRIMARY KEY ("id")
        );
        INSERT INTO "Table_Name" ("id", "name", "lat", "lon", "type", "image", "notes") VALUES
        """
        self.gpxHeader = """<?xml version="1.0" encoding="utf-8"?>
            <gpx creator="OpenCPN" version="1.1" xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3" xmlns:opencpn="http://www.opencpn.org" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
            <rte>
            <name>nameX</name>
            <extensions>
                <opencpn:guid>715affff-de7d-4094-9e87-RANDOM</opencpn:guid>
                <opencpn:viz>1</opencpn:viz>
                <opencpn:sharedWPviz>0</opencpn:sharedWPviz>
                <opencpn:start>Start</opencpn:start>
                <opencpn:end>End</opencpn:end>
                <opencpn:planned_speed>5.00</opencpn:planned_speed>
                <opencpn:time_display>PC</opencpn:time_display>
                <gpxx:RouteExtension>
                    <gpxx:IsAutoNamed>false</gpxx:IsAutoNamed>
                </gpxx:RouteExtension>
            </extensions>
            """
        self.gpxWaypoint = """<rtept lat="latX" lon="lonX">
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
            </rtept>
            """
        self.gpxFooter = "</rte></gpx>\n"

    def __str__(self):
        return f"Nav Config is using the init file '{self.configFile}'."

    def error(self, error, method):
        print(
            f"\nTerminating now due to error:\n'{str(error)}'"
            f"\nUsing the method '{method}' with the config file ('{self.configFile}').")

    def saveConfig(self, cwd, lastFile, extension):
        """--------------------------------------------------------------------------
        Method to save the settings parameters to file

        Args:
            cwd (string):       string with the working directory
            lastFile (string):  string with name of the last file spec'ed by user
            extension (string): string with the file type extension
        Return:
            none
        """
        settingsFile = os.path.join(cwd, self.configFile)

        try:
            with open(settingsFile, 'r') as fr:
                rawSettings = json.load(fr)

            with open(settingsFile, 'w') as fw:
                rawSettings['lastFile'] = lastFile
                rawSettings['fileType'] = extension
                txt = json.dumps(rawSettings, indent=2)
                fw.write(txt)
            return True
        except Exception as e:
            self.error(e, "saveConfig")
        return False

    def getConfig(self, verbose=False):
        """--------------------------------------------------------------------------
        Method to initialize default settings from file and return
        them in a dictionary

        Args:
            verbose (bool): print program results when True

        Return:
            (dictionary) with the program settings
        """

        settings = {'cwd': '',
                    'csvPath': '',
                    'gpxPath': '',
                    'sqlitePath': '',
                    'spotPath': '',
                    'kmlPath': '',
                    'txtPath': '',
                    'sqliteDB': '',
                    'toernDirectory': '',
                    'lastFile': '',
                    'fileType': '',
                    'skipWP': 'True',
                    'noSpeed': 'False',
                    'verbose': 'verbose',
                    'error': True}

        # fetch the content from the default settings file
        cwd = os.path.dirname(os.path.abspath(
            inspect.getfile(inspect.currentframe())))
        cwd = os.path.normpath(cwd)

        default_settings = os.path.join(cwd, self.configFile)

        try:
            with open(default_settings, 'r') as fp:
                rawSettings = json.load(fp)

            supported_devices = rawSettings['devices']
            current_device = ''
            for device in supported_devices:
                if (os.path.exists(os.path.normpath(supported_devices[device]))):
                    current_device = device

            if (current_device == ''):
                msg = f"Unknown computer '{rawSettings['devices']}'and root file system"
                raise Exception(msg)

            toernDirectory = os.path.normpath(
                rawSettings['toernDirectory'][current_device])
            gpxPath = os.path.normpath(rawSettings['gpxPath'][current_device])
            sqliteDB = os.path.normpath(
                rawSettings['sqliteDB'][current_device])
            sqlitePath = os.path.normpath(
                rawSettings['sqlitePath'][current_device])
            csvPath = os.path.normpath(
                rawSettings['csvPath'][current_device])
            kmlPath = os.path.normpath(
                rawSettings['kmlPath'][current_device])
            lastFile = rawSettings['lastFile']
            fileType = rawSettings['fileType']

            if verbose:
                print(f"Configuration file...: '{self.configFile}'")
                print(f"Device...............: '{current_device}'")
                print(f"GPX path.............: '{gpxPath}'")
                print(f"CSV path.............: '{csvPath}'")
                print(f"KML path.............: '{kmlPath}'")
                print(f"SQLite path..........: '{sqlitePath}'")
                print(f"SQLite DB............: '{sqliteDB}'")
                print(f"Toern Directory Table: '{toernDirectory}'")
                print(f"Working Dir..........: '{cwd}'")
                print(f"Last Input file......: '{lastFile}'")
                print(f"Skip WPs.............: '{rawSettings['skipWP']}'")
                print(f"No Speed.............: '{rawSettings['noSpeed']}'")
                print(f"Timezone Difference..: {rawSettings['TimeZoneDifference']:.1f} hrs between race course and UTC")
                print(f"Minimum Course Change: {rawSettings['minCourseChange']:.2f} degrees")
                print(f"Verbose..............: '{rawSettings['verbose']}'")

            settings['cwd'] = cwd
            settings['csvPath'] = csvPath
            settings['gpxPath'] = gpxPath
            settings['kmlPath'] = kmlPath
            settings['sqlitePath'] = sqlitePath
            settings['sqliteDB'] = sqliteDB
            settings['lastFile'] = lastFile
            settings['fileType'] = fileType
            settings['toernDirectory'] = toernDirectory
            settings['skipWP'] = rawSettings['skipWP']
            settings['noSpeed'] = rawSettings['noSpeed']
            settings['verbose'] = rawSettings['verbose']
            settings['error'] = True
            settings['TimeZoneDifference'] = rawSettings['TimeZoneDifference']
            settings['minCourseChange'] = rawSettings['minCourseChange']

        except Exception as e:
            self.error(e, "getConfig")
            settings['error'] = self.configFile

        return settings

    def isGenericWaypoint(self, wpt):
        """--------------------------------------------------------------------------
        Method to test if current waypoint is a generic waypoint as 
        defined by the list genericWPs

        Args:
            wpt (string):   name of the waypoint to be tested

        Return:
            (boolean):      True: generic WP, False: non-generic WP
        """
        generic = False
        for genericWP in self.genericWPs:
            generic = (generic or wpt.startswith(genericWP))
        return generic

    def ComputeRouteDistances(self, xml, verbose, skipWP, noSpeed):
        """--------------------------------------------------------------------------
        Method to compute the distance, speed, and Etmals between 
        sequential route waypoints
        a <desc></desc> tag/field with these entry options:
            arrival 2019-09-25 19:30    (arrival date/time at this WP)
            departure 2019-09-26 09:37  (departure date/time from this WP)
            timedleg 2019-09-26 09:37   (arrival and departure at/from this WP)
            poi                         (Point of Interest on route not being listed)
            homeport                    (designates the Waypoint from which a round-trip
                                        toern originates. Add departure and arrival
                                        times using the above keywords in add'l lines)
                                        all dates are in the in the format yyyy-mm-dd hh:mm

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
        last_lat = 0.0              # lat of previous WP
        last_lon = 0.0              # lon of previous WP
        leg_start_date = ""         # date/time at first "timed" WP
        total_trip_distance = 0.0   # total distance traveled on this trip
        leg_distance = 0.0          # distance between two adjacent "timed" WPs
        leg_elapsed = 0.0           # elapsed time between two adjacent "timed" WPs
        departure_flag = False      # set flag to true to indicate start of timed leg
        leg_timed_flag = False      # set flag to true to indicate this leg was timed
        sum_legs_distance = 0.0     # the sum distance traveled on all timed legs
        sum_legs_time = 0.0         # the sum time traveled on all timed legs
        leg_start_date = ""         # initialization
        leg_end_date = ""           # initialization
        # flag that indicates that end of leg is also start of next leg
        timed_flag = False
        wpCTR = 0
        for wp in wps:
            lat = float(wp['lat'])
            lon = float(wp['lon'])
            name = wp.find('name').text
            time = wp.find('time').text
            symbol = wp.find('sym')
            if symbol is None:
                symbol = "empty"
            else:
                symbol = symbol.text.lower()
            desc = wp.find('desc')

            if (symbol in self.WPtypes):
                departure_flag = True

            generic = self.isGenericWaypoint(name)

            # handles the speed computations based on the <desc> tag info
            if (desc != None):
                desc = desc.text.lower()
                if (desc.startswith('homeport') and wpCTR == 0):
                    if ('departure' in desc):
                        desc_arr = desc.split('departure ')
                        desc = desc_arr[1]
                        leg_start_date = self.StringToDateTime(desc, dateFormats)

                if (desc.startswith('homeport') and wpCTR > 0):
                    if ('arrival' in desc):
                        desc_arr = desc.split('arrival ')
                        desc = desc_arr[1]
                        leg_end_date = self.StringToDateTime(desc, dateFormats)

                if (desc.startswith('departure')):
                    time = desc.replace('departure ', '')
                    leg_start_date = self.StringToDateTime(time, dateFormats)
                    # print(f"departure - Leg start: {leg_start_date} at: {name}")
                    departure_flag = True

                if (desc.startswith('arrival')):
                    time = desc.replace('arrival ', '')
                    leg_end_date = self.StringToDateTime(time, dateFormats)
                    # print(f"arrival      - Leg start: {leg_start_date} end: {leg_end_date} at: {name}")
                    if (departure_flag):
                        leg_timed_flag = True
                        departure_flag = False
                    else:
                        leg_timed_flag = False

                if (desc.startswith('timedleg')):
                    time = desc.replace('timedleg ', '')
                    leg_end_date = self.StringToDateTime(time, dateFormats)
                    # print(f"timedleg  - Leg start: {leg_start_date} end: {leg_end_date} at: {name}")
                    leg_timed_flag = True
                    departure_flag = True
                    timed_flag = True

                if (desc.startswith('poi')):
                    generic = True

            if (last_lat != 0.0 and last_lon != 0.0):
                distance = self.calc_distance(last_lat, last_lon, lat, lon)
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
                    lat_str = f"{lat:7.3f}N"
                else:
                    lat_str = f"{math.fabs(lat):7.3f}S"

                if (lon >= 0.0):
                    lon_str = f"{lon:7.3f}E"
                else:
                    lon_str = f"{math.fabs(lon):7.3f}W"

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
            if (total_trip_distance > 0.0):
                msg += (f"   ({sum_legs_distance/total_trip_distance:.2%})")
        if (sum_legs_time > 0.0 and not noSpeed):
            avg_speed = sum_legs_distance / sum_legs_time
            msg += (f"\nAverage Speed:          {avg_speed:9,.2f}kts")

        if verbose:
            print(msg)
        return msg

    def addImagesToRoute(self, path):
        """--------------------------------------------------------------------------
        Method to add images to route file based to the image geo tags and the
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
                                latlong = print(f"Lat/Lon {repr(val)}")
                        if latlong is not None:
                            points.append(latlong)
                            print(
                                f"Image {f} taken at {points[0]:.4f} / {points[0]:.4f}")
                    else:
                        print(exif)

    def calc_heading(self, latFrom, lonFrom, latTo, lonTo):
        """--------------------------------------------------------------------------
            Method to compute the heading between two lat/lon positions
            in degrees between 0 and 359

        Args:
            latFrom (str): starting point latitude in degress
            lonFrom (str): starting point longitude in degress
            latto (str):   ending point latitude in degress
            lonTo (str):   ending point longitude in degress

        Return:
            (float) degrees (between 0 and 359)
        """
        precision = 0.0000001

        try:
            latFrom = float(latFrom)
            lonFrom = float(lonFrom)
            latTo = float(latTo)
            lonTo = float(lonTo)
        except Exception as e:
            print(f"calc_heading(): error converting lat/lon strings to float")
            return 0.0
        
        dLon = math.radians(lonTo - lonFrom)
        lat1 = math.radians(latFrom)
        lat2 = math.radians(latTo)

        x = (math.cos(lat1) * math.sin(lat2)
            - math.sin(lat1)*math.cos(lat2)*math.cos(dLon))
 
        y = math.sin(dLon) * math.cos(lat2)

        if(abs(x) < precision and abs(y) < precision):
            return 0.0
        
        return ((360.0 + math.degrees(math.atan2(y, x)) ) % 360)


    def calc_distance(self, latFrom, lonFrom, latTo, lonTo):
        """--------------------------------------------------------------------------
            Method to compute the great-circle distance between two 
            lat/lon positions in nautical miles (nm)
            This Method uses the 'haversine' formula
            Calculations match Expedition but not OpenCPN
            https://www.movable-type.co.uk/scripts/latlong.html

        Args:
            latFrom (float): starting point latitude in degress
            lonFrom (float): starting point longitude in degress
            latto (float):   ending point latitude in degress
            lonTo (float):   ending point longitude in degress

        Return:
            (float) distance in nm
        """

        dLat = math.radians(latTo - latFrom)
        dLon = math.radians(lonTo - lonFrom)
        lat1 = math.radians(latFrom)
        lat2 = math.radians(latTo)

        a = (math.sin(dLat / 2.0) * math.sin(dLat/2.0)
             + math.sin(dLon / 2.0) * math.sin(dLon/2.0)
             * math.cos(lat1) * math.cos(lat2)
             )
        return (self.RADIUS * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

    def StringToDateTime(self, dateString, dateFormats):
        """--------------------------------------------------------------------------
            Method to convert a string to a datetime format. Return a 
            zero if the conversion failed

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

    def parseSQLRouteFile(self, pathGPX, pathSQL, filename):
        """--------------------------------------------------------------------------
            Method to parse the GPX route data into a MySQL query file

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

        if('Table_Name' in self.sql_header):
            output = self.sql_header.replace('Table_Name', filename)
        else:
            print(f"missing or incorrect sql_header file:\n'{self.sql_header}'")
            return False

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
                notes = '"'+(wp.find('desc').text)+'"'
                desc = (wp.find('desc').text).lower()
            else:
                notes = '" "'
                desc = ""

            if name.startswith('NM') or name.startswith('WP') or name.startswith('0'):
                name = 'WP' + str(wp_ctr).zfill(4)
                wp_ctr += 1
            lat = wp['lat']
            lon = wp['lon']
            if (ctr == 0):
                output += "(" + str(ctr)+", '" + name + "', " + \
                    "'" + str(lat) + "', '" + str(lon) + \
                    "', 'harbor', '', ''),\n"
                route = 'harbor'
                first_lat = lat
                first_lon = lon
                #print(output)
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
                distance = self.calc_distance(
                    old_lat, old_lon, float(lat), float(lon))
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
                output += "(" + str(ctr)+", '" + name + \
                    "', " + "'" + str(lat) + "', '" + str(lon) + "', '"
                output += route + "', '', " + notes + "),\n"
            # print(f"from: {old_name}  to: {name}")
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

    def getTime(self, timeStr, timezoneDifference=0.0):
        """--------------------------------------------------------------------------
        Method to convert a Yellowbrick time string into a datetime value
        and convert from UTC time to the racecourse time using the 
        parameter timezoneDifference (in hrs). 

        Args:
            timeStr (string):  time string format used by Yellowbrick
            timezoneDifference (float): timezone difference between UTC and the race course

        Return:
            (datetime) time value from the timeStr string
        """
        t = timeStr.replace("T", " ")
        t = t[:len(t)-4]
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
        return (dt+timedelta(hours=timezoneDifference))

    def strRANDOMreplace(self, gpxSTR):
        """--------------------------------------------------------------------------
        Method to modify the GPX string RANDOM placeholder with a random number

        Args:
            gpxSTR (string): string with RANDOM placeholder to be modified

        Return:
            (string) GPX string
        """
        rndDigits = (f"{random.randint(0, 0xFFFFFFFFFFFF):12x}")
        gpx = gpxSTR.replace("RANDOM", rndDigits)
        return gpx


    def parseKMLRouteFile(self, pathKML, pathGPX, filename, boatname, timezoneDifference, raceStart, watchStart, watchRhythm, minCourseChange):
        """--------------------------------------------------------------------------
        Method to parse the waypoint and route information from a .kml 
        file into a GPS file. Only after a course change of at least
        'minCourseChange' degrees will a new waypoint be created.
        Yellowbrick race tracking route files are available at
        https://yb.tl/racenamexyz.kml

        Args:
            pathKML (string):  path to the kml file location
            pathGPX (string):  path to the gpx folder
            filename (string): name of the file
            boatname (string): name of the boat in the .kml file
            timezoneDifference (float): racecourse timezone difference to UTC
            raceStart (datetime): start of the race
            watchStart (datetime): race course time of watch schedule start
            watchRhythm (int): number of watch hrs on/off
            minCourseChange (float): minimum course change before a new WP is generated

        Return:
            (string) with the log messages
        """

        log_msg = ""
        ctr = 0

        try:
            fileKML = os.path.join(pathKML, filename+".kml")
            inputFile = open(fileKML, "r")
            xml = inputFile.read()
            inputFile.close()
        except:
            print(f"Error opening file: {fileKML}")
            return False
        fileGPX = os.path.join(pathGPX, filename+".gpx")
        outputfile = open(fileGPX, "w")
        kml = BeautifulSoup(xml, features="xml")
        # different Yellowbrick kml files use different spellings
        records = kml.find_all("Placemark")
        if not len(records):
            records = kml.find_all("placemark")
        locations = []
        times = []
        if len(records):
            print(f"\nfound {len(records)} boat names")
            ctr = 0
            wpCTR = 0
            for record in records:
                boat = record.find_all("name")
                if boatname.lower() in boat[0].contents[0].lower():
                    #print(f"\n\nfound our boat: {boat[0].contents[0]}\n")
                    siblings = list(record.next_siblings)
                    #print(len(siblings))
                    times = record.find_all("ns2:when")
                    locations = record.find_all("gx:coord")
                    break
                ctr += 1

            if len(locations) != 0 and len(locations) == len(times):

                # build the GPX route file
                gpx = self.strRANDOMreplace(self.gpxHeader)
                gpx = gpx.replace("nameX", filename)
                lastHDG = 999
                watchStartFlag = False
                raceStartFlag = False
                elapsed = timedelta(seconds=0)
                wp = ""
                startCtr = 0
                for ctr in range(0, len(locations)):
                    watchChange = False
                    # location info is stored as longitute latitude string pairs
                    # example: ['-87.5822,41.876299999999986,0']
                    latlon = locations[ctr].contents[0]
                    latlon = latlon.split(',')

                    currentT = self.getTime(
                        times[ctr].text, timezoneDifference)
                    if not raceStartFlag and currentT >= raceStart:
                        raceStartFlag = True
                        startCtr = ctr     # initialize startCtr
                        lastWP = latlon    # initialize lastWP
                        lastT = currentT   # initialize lastT
                    if not watchStartFlag and currentT >= watchStart:
                        watchStartFlag = True
                    if watchStartFlag:
                        elapsed = currentT - lastT
                    if raceStartFlag:
                        hdg = self.calc_heading(lastWP[1], lastWP[0], latlon[1], latlon[0])
                        if (elapsed.total_seconds() >= watchRhythm*60*60 
                            or currentT == watchStart):
                                watchChange = True
                                                                   # only add a WP if
                        if(startCtr == ctr or                      # race start
                           watchChange or                          # watch change
                           ctr==len(locations)-1                   # last waypoint
                           or abs(hdg-lastHDG) > minCourseChange): # a course change larger than minCourseChange
                            #print(f"ctr: {ctr}  wpCTR: {wpCTR}  hdg: {hdg:.2f}")
                            #print(f"{lastWP[1]}  {lastWP[0]} - {latlon[1]}  {latlon[0]}")
                            wp = self.strRANDOMreplace(self.gpxWaypoint)
                            wp = wp.replace("latX", latlon[1])
                            wp = wp.replace("lonX", latlon[0])
                            wp = wp.replace("timeX", times[ctr].contents[0])
                            wp = wp.replace("wpX", "NM{:05d}".format(wpCTR+1))
                            strT = currentT.strftime("%Y-%m-%d %H:%M")
                            #wp = wp.replace("empty", "diamond")
                            if ctr == startCtr:
                                wp = wp.replace("empty", "diamond")
                                wp = wp.replace(
                                    f"</name>", f"</name>\n   <desc>departure {strT}</desc>")
                                wp = wp.replace(
                                    "NM{:05d}".format(wpCTR+1), "Race Start")
                            if ctr == len(locations)-1:
                                wp = wp.replace("empty", "diamond")
                                wp = wp.replace(
                                    "</name>", f"</name>\n   <desc>arrival {strT}</desc>")
                                elapsed = timedelta(seconds=0)
                            if watchChange:
                                wp = wp.replace(
                                    "NM{:05d}".format(wpCTR+1), strT)
                                wp = wp.replace(
                                    "</name>", f"</name>\n   <desc>timedleg {strT}</desc>")
                                lastT = currentT
                            lastHDG = hdg
                            wpCTR = wpCTR + 1
                            gpx += wp
                        # end of conditional clause testing for new waypoint
                        lastWP = latlon
                    print(f"processed WP{ctr} out of {len(locations)}")
                    # end of conditional clause for race start
                # of of loop over all waypoint in the KML file
                gpx += self.gpxFooter
                outputfile.write(gpx)

                log_msg += (
                    f"Done, parsed a total of {wpCTR} waypoints from {ctr} KML records for boat '{boatname}' ")
                log_msg += (
                    f"from the KML route file {fileKML} to the GPX route file{fileGPX}\n")
            else:
                log_msg += (
                    f"Found inconsistent number of or no location ({len(locations)}) and date ({len(times)}) records. Couldn't parse the KML route info for boat '{boatname}'.\n")
        else:
            log_msg += (
                f"Found no route information in the KML file ('{fileKML}').\n")

        outputfile.close()

        return str(log_msg)

    def verifyGPXRouteFile(self, pathGPX, nameGPX):
        """--------------------------------------------------------------------------
            Method to verify / fix duplicate waypoint names in GPX file

        Args:
            pathGPX (string): path to the GPX file
            nameGPX (string): GPX file name

        Return:
            msg (string): message with the results
        """
        msg = "No duplicate waypoint names found in the file\n"

        fname = os.path.join(pathGPX, nameGPX)
        try:
            with open(fname, 'r') as fr:
                xml = fr.read()

            soup = BeautifulSoup(xml, features="html5lib")
            wpNames = [x.get_text() for x in soup.find_all('name')]
            counter = Counter(wpNames)
            duplicates = [key for key in counter.keys() if counter[key] > 1]
            ctr = 0
            for duplicate in duplicates:
                if self.isGenericWaypoint(duplicate):
                    for i in range(counter[duplicate]):
                        newName = (
                            f"{duplicate}{random.randint(0, 10000):05d}")
                        xml = xml.replace(
                            (f"<name>{duplicate}</name>"),
                            (f"<name>{newName}</name>"),
                            1)
                        #print(duplicate, counter[duplicate], newName)
                        ctr = ctr + 1
            if ctr > 0:
                with open(fname, 'w') as fr:
                    fr.write(xml)
                msg = (
                    f"Fixed {ctr} duplicate waypoint {'names' if ctr>1 else 'name'}\n")
        except Exception as e:
            print(
                f"\nTerminating verifyGPXRouteFile() now due to error:\n'{str(e)}'\nreading/verifying the GPX file ('{fname}').")

        return msg

    def verifyToerndirectoryDistances(self, sqliteDB, gpxPath):
        """--------------------------------------------------------------------------
            Method to verify / fix the trip distances in the sqlite DB vs.
            the calculated distances calculated from the trip sqlite files

        Args:
            sqliteDB (string): path to the sqlite DB file

        Return:
            msg (string): message with the results
        """
        try:
            con = sqlite3.connect(sqliteDB)
            cursor = con.cursor()
            cursor.execute(
                "SELECT id, destination, maptable, miles FROM ToernDirectoryTable")
            rows = cursor.fetchall()
            cursor.close()
        except Exception as e:
            return f"sqlite DB error '{str(e)}' in method 'verifyToerndirectoryDistances'.\n"

        msg = ""
        ctr = 0
        ok = 0
        for row in rows:
            match = False
            try:
                filename = os.path.join(gpxPath, row[2]+".gpx")
                inputfile = open(filename, "r")
                xml = inputfile.read()
                inputfile.close()
            except:
                xml = ""
                msg += (f"Error opening file: '{filename}'\n")

            dist = self.ComputeRouteDistances(
                xml, verbose=False, skipWP=True, noSpeed=False)
            match = re.findall("Total Trip Distance:[ 0-9\.\,]*", dist)
            if xml != "" and len(match) > 0:
                x = match[0].split(':')
                if len(x) > 1:
                    y = x[1].replace(",", "")
                    y = float(y)
                    if round(y, 2) != round(row[3], 2):
                        msg += (f"{row[1]}: {y:.2f} vs. {row[3]:.2f}\n")
                    else:
                        ok += 1
                else:
                    msg += (
                        f"error finding distance for {row[1]} with {match.string}\n")
            ctr += 1
        msg += (f"\n{ok} out of {ctr} trips where OK\n")
        return msg

if __name__ == "__main__":
    """-------------------------------------------------------------------------
        Script starting point
    """

    print(f"\nPlease run NavigationTools.pyw App\n")
    exit(0)

    # debugging kml parser
    navtools = NavTools()
    settings = navtools.getConfig(verbose=True)
    if settings["error"] is True:
        os.chdir(settings["gpxPath"])
    else:
        raise Exception(
            f"Error reading from configuration file ('{settings['error']}')")
    pathKML = "E:\\My Documents\\Google Drive\\Sailing\\OpenCPN_Routes"
    pathGPX = pathKML
    filename = "2024_Bayview_Race_to_Mackinac"
    boatname = "Aeolus"
    timezoneDifference = -4
    raceStart = datetime.strptime("2024-07-20 14:36", "%Y-%m-%d %H:%M")
    watchStart = datetime.strptime("2024-07-20 15:00", "%Y-%m-%d %H:%M")
    watchRhythm = 3
    minCourseChange = 7.5
    msg = navtools.parseKMLRouteFile(pathKML, pathGPX, filename, boatname, timezoneDifference, raceStart, watchStart, watchRhythm, minCourseChange)

    print(msg)

