#!/usr/bin/env python
# -- coding: utf-8 --
#from __future__ import unicode_literals
#--------------------------------------------------------------------------------------------
__author__      = "Volker Petersen <volker.petersen01@gmail.com>"
__version__     = "Navigation_Route_Parser.pyw Revision: 2.0"
__date__        = "Date: 2011/09/26 | 2015/08/08"
__copyright__   = "Copyright (c) 2011 Volker Petersen"
__license__     = "Python 3.6 | GPL http://www.gnu.org/licenses/gpl.txt"
__doc__ = """
--------------------------------------------------------------------------------------------
    OpenCPN to MySQL Waypoint legend:
    Diamonds   "regular WP on route"
    Empty      "none" WP on route"
    Circle     "Harbor"
    Anchorage  "Mooring / Anchorage"
--------------------------------------------------------------------------------------------
"""
try:
    import sys
    import wx
    import math
    from wx.lib.wordwrap import wordwrap
    import os, inspect
    from datetime import datetime
    from bs4 import BeautifulSoup
    from tabulate import tabulate
    from uploadMySQL import uploadMySQLfile
    import json
except ImportError as e:
    print ("Import error: %s\nAborting the program %s" %(str(e), __version__))
    sys.exit()

#
# in OpenCPN mark Waypoints as follows:
# Diamonds for "regular WP on route"
# Circle for "Harbor"
# Anchorage for "Mooring / Anchorage"
#

#--------------------------------------------------------------------------------------------
# main class Navigation_Route_Parser using a SplitterWindowContainer
#--------------------------------------------------------------------------------------------
class Navigation_Route_Parser(wx.Frame):
    """ Navigation Route Parser main Class """
    def __init__(self):
        global path, left, right, log
        wx.Frame.__init__(self, None, wx.ID_ANY, title="Navigation Route Parser App", pos=(10, 100), size=(557, 535))
        #wx.Frame.SetMinSize(self, (557, 535)) # size and pos tuples (width x height)
        #self.Centre() # centers the frame in the window / screen
        #wx.Frame.SetPosition(self, (10, 100)) # set Frame position to 10 over and 100 down from Top Left Corner
        favicon = wx.Icon('icons/sailing_fav.ico', wx.BITMAP_TYPE_ICO, 16, 16)
        wx.Frame.SetIcon(self, favicon)

#       setup the SplitterWindow with two panels
        splitter = wx.SplitterWindow(self, wx.ID_ANY)
        left  = wx.Panel(splitter, style=wx.BORDER_SUNKEN)
        right = wx.Panel(splitter, style=wx.BORDER_SUNKEN)
        right.SetBackgroundColour("white")

        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left.SetSizer(left_sizer)

        right.log = wx.TextCtrl(right, -1, "", pos=(2, 2),
            size=(360, 470), style=wx.TE_MULTILINE|wx.TE_READONLY)
        right.log.SetValue(log)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        right.SetSizer(right_sizer)
        splitter.SplitVertically(left, right, 170)

#       setup the Menus
        menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        menubar.Append(fileMenu, "&File")

        helpMenu = wx.Menu()
        menubar.Append(helpMenu, "&Help")

        file_directory = fileMenu.Append(wx.ID_ANY, "Select &Route File\tAlt-R")
        file_GPX_MySQL = fileMenu.Append(wx.ID_ANY, "Parse &GPX->MySQL File\tAlt-G")
        file_MySQL_GPX = fileMenu.Append(wx.ID_ANY, "Parse &MySQL->GPX File\tAlt-M")
        file_SPOT_MySQL = fileMenu.Append(wx.ID_ANY, "Parse &SPOT->MySQL File\tAlt-S")
        file_uploadMySQL = fileMenu.Append(wx.ID_ANY, "&Upload MySQL File\tAlt-U")
        file_DISTANCES = fileMenu.Append(wx.ID_ANY, "&Compute Distances\tAlt-C")
        file_exit = fileMenu.Append(wx.ID_ANY, "E&xit\tAlt-X")

        self.Bind(wx.EVT_MENU, self.onSelectRouteFile, file_directory)
        self.Bind(wx.EVT_MENU, self.onParseSQLRouteFile, file_GPX_MySQL)
        self.Bind(wx.EVT_MENU, self.onParseGPXRouteFile, file_MySQL_GPX)
        self.Bind(wx.EVT_MENU, self.onParseSPOTRouteFile, file_SPOT_MySQL)
        self.Bind(wx.EVT_MENU, self.onUploadMySQLFile, file_uploadMySQL)
        self.Bind(wx.EVT_MENU, self.onComputeDistances, file_DISTANCES)
        self.Bind(wx.EVT_MENU, self.onTimeToExit, file_exit)

        about = helpMenu.Append(wx.ID_ANY, "&About\tAlt-A")
        self.Bind(wx.EVT_MENU, self.onHelpAbout, about)
        self.SetMenuBar(menubar)

        blength=130
        bheight=30
        lstart = 20
        yoffset = 70
        y = 100
        b1 = wx.Button(left, wx.ID_ANY, "Select Route File", (lstart,15), (blength,bheight))
        self.Bind(wx.EVT_BUTTON, self.onSelectRouteFile, b1)
        b1.SetToolTipString("Select the Navigation Route File from which\n"+
            "to parse the route and waypoint information.\n")
        left.path = wx.TextCtrl(left, -1, path, pos=(5, 60), size=(blength+30, bheight+10),
            style=wx.TE_MULTILINE|wx.HSCROLL|wx.TE_READONLY|wx.TE_NO_VSCROLL)
        y = y + yoffset - 40

        b5 = wx.Button(left, wx.ID_ANY, "Parse GPX->MySQL", (lstart,y), (blength,bheight))
        self.Bind(wx.EVT_BUTTON, self.onParseSQLRouteFile, b5)
        b5.SetToolTipString("Parse the route and waypoint information \n"
            "from the OpenCPN selected .gpx file to MySQL-query file.\n")
        y = y + yoffset - 20

        b6 = wx.Button(left, wx.ID_ANY, "Parse MySQL->GPX", (lstart,y), (blength,bheight))
        self.Bind(wx.EVT_BUTTON, self.onParseGPXRouteFile, b6)
        b6.SetToolTipString("Parse the route and waypoint information \n"
            "from a MySQL-query file to an OpenCPN .gpx file.\n")
        y = y + yoffset - 20

        b7 = wx.Button(left, wx.ID_ANY, "Parse SPOT->MySQL", (lstart,y), (blength,bheight))
        self.Bind(wx.EVT_BUTTON, self.onParseSPOTRouteFile, b7)
        b7.SetToolTipString("Parse the route and waypoint information \n"
            "from a SPOT file to a MySQL-query file.\n")
        y = y + yoffset - 20

        b8 = wx.Button(left, wx.ID_ANY, "Upload MySQL", (lstart,y), (blength,bheight))
        self.Bind(wx.EVT_BUTTON, self.onUploadMySQLFile, b8)
        b8.SetToolTipString("Upload a MySQL-query file \n"
            "to the MySQL website DB.\n")
        y = y + yoffset - 20

        b9 = wx.Button(left, wx.ID_ANY, "Compute Distances", (lstart,y), (blength,bheight))
        self.Bind(wx.EVT_BUTTON, self.onComputeDistances, b9)
        b9.SetToolTipString("Compute Distances, Speed, and Etmals between Waypoints \n")
        y = y + yoffset

        b10 = wx.Button(left, wx.ID_ANY, "Exit App", (lstart,y), (blength,bheight))
        self.Bind(wx.EVT_BUTTON, self.onTimeToExit, b10)

#--------------------------------------------------------------------------------------------
# Event handler to Compute Distances, Speed, and Etmals between Waypoints
#--------------------------------------------------------------------------------------------
    def onComputeDistances(self, event):
        global path, filename, left, right, log

        if path == "":
            path = "D:\VolkerPetersen\Google Drive\Sailing\OpenCPN_Routes\2016_06_Jacksonville_Bermuda.gpx"
        try:
            inputfile = open(os.path.join(path, filename), "r")
            xml = inputfile.read()
            inputfile.close
        except:
            print ("Error opening file: %s" %path)

        ComputeRouteDistances(xml, True, True, False)
        return

#--------------------------------------------------------------------------------------------
# Event handler to Select an OpenCPN .gpx or MySQL route file to be parsed
#--------------------------------------------------------------------------------------------
    def onSelectRouteFile(self, event):
        global path, filename, left, right, log, settings, default_settings
        filters = 'OpenCPN route files (*.gpx)|*.gpx|MySQL route file (*.sql)|*.sql|All files (*.*)|*.*'
        dlg = wx.FileDialog(self, "Choose a OpenCPN .gpx route file:", wildcard = filters, style=wx.FD_OPEN | wx.FD_MULTIPLE)
        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it.
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            filename = os.path.basename(path)
            path = os.path.dirname(path)
            lines = left.path.GetNumberOfLines()
            len = 0
            for i in range(0, lines):
                len = len + left.path.GetLineLength(i)
            left.path.Replace(0,len, path)

            # check if we have a new *.gpx file selection.  If so, update the
            # default_settings file
            if (path.find(".gpx") != -1):
                settings["lastGPX"] = path
                write_json(default_settings, settings)
            log = "==> Set route file to: " + os.path.join(path, filename) + "\n\n" + log
            right.log.SetValue(log)
        # Only destroy a dialog after you're done with it.
        dlg.Destroy()

#--------------------------------------------------------------------------------------------
# Event handler to parse the waypoint and route information from the .gpx file
# into a MySQL query file
#--------------------------------------------------------------------------------------------
    def onParseSQLRouteFile(self, event):
        global right, log, path, filename, sql

        log = parseSQLRouteFile(path, sql, filename)
        right.log.SetValue(log + "\n\n")

#--------------------------------------------------------------------------------------------
# Event handler to parse the waypoint and route information from the MySQL file
# into a OpenCPN .gpx file
#--------------------------------------------------------------------------------------------
    def onParseGPXRouteFile(self, event):
        global right, log, path, filename

        gpx_header = """<?xml version="1.0" encoding="utf-8" ?>
        <gpx version="1.1" creator="OpenCPN" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd" xmlns:opencpn="http://www.opencpn.org">
        <rte>
        <name>Route Name</name>
        <extensions>
            <opencpn:start></opencpn:start>
            <opencpn:end></opencpn:end>
            <opencpn:viz>1</opencpn:viz>
            <opencpn:guid>17ab0000-eb25-48bc-930a-000000000000</opencpn:guid>
        </extensions>\n"""

        today = datetime.now()
        log_msg = ""

        # debug code segment
        #path = "D:\\VolkerPetersen\\Dropbox\\Sailing\\OpenCPN_Routes\\spot_messages.sql"
        # end of debug code segment

        try:
            inputfile = open(os.path.join(path, filename), "r")
            xml = inputfile.read()
            inputfile.close

        except:
            print ("Error opening file: %s" %path)

        values = ") VALUES"
        if values in xml:
           print (xml.index(values))
           xml = xml[xml.index(values)+len(values):]
           xml = xml.replace(');', '),')
           wps = xml.split("),")
        else:
            msg = "==> "+today.strftime("%Y-%m-%d  %H:%M:%S ") + " MySQL Route Parsing Function"
            msg = msg + "\nDidn't find any waypoints in  MySQL - missing '" + values + "' string."
            msg = msg + " in the MySQL route file " + path +"\n\n"
            log_msg = msg + log_msg
            log = log_msg + "\n\n" + log
            right.log.SetValue(log)
            return

        filename2 = filename.replace('.sql', '.gpx')
        OutputFile = open(os.path.join(path, filename2), "w")

        name = filename.replace('.sql', '')
        output = gpx_header.replace('Route Name', name)

        wp_ctr = 1
        for wp in wps:
            #print (wp)
            wp_data = wp.split(", ")
            #print (len(wp_data))
            if len(wp_data) > 3:
                lat = wp_data[3].replace("'", "")
                lon = wp_data[4].replace("'", "")
                output += '<rtept lat="' + lat + '" lon="' + lon + '">\n'
                output += '<time></time>\n'
                output += '<name>'+wp_data[2]+'</name>\n'
                output += '<sym>empty</sym><type>WPT</type>\n'
                output += '<extensions><opencpn:guid>717ab0000-eb25-48bc-930a-%012d' %wp_ctr
                output += '</opencpn:guid>\n<opencpn:viz>0</opencpn:viz>\n<opencpn:viz_name>0</opencpn:viz_name>\n</extensions>\n</rtept>\n'
                wp_ctr += 1

        output += '</rte>\n</gpx>\n'
        #print output

        OutputFile.write(output)
        OutputFile.close

        msg = "==> "+today.strftime("%Y-%m-%d  %H:%M:%S ") + " MySQL Route Parsing Function"
        msg = msg + "\nDone! Converted " + str(wp_ctr-1) + " waypoints in"
        msg = msg + " from the MySQL route file " + path +" to a .gpx file.\n\n"
        log_msg = msg + log_msg
        log = log_msg + "\n\n" + log
        right.log.SetValue(log)
        return

#--------------------------------------------------------------------------------------------
# Event handler to parse the waypoint and route information from the SPOT file
# into a MySQL query file
#--------------------------------------------------------------------------------------------
    def onParseSPOTRouteFile(self, event):
        global right, log, path, filename

        sql_header = """-- phpMyAdmin SQL Dump
-- version 3.3.9
SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

-- Database: `map`
-- Table structure for table `Table_Name`

CREATE TABLE IF NOT EXISTS `Table_Name` (
`id` int(11) DEFAULT NULL,
`from` text,
`to` text,
`lat` text,
`lon` text,
`type` text,
`image` text
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
--
-- Dumping data for table `Table_Name`
-- roundtrip    => if first and last waypoint in the file are the same
-- one-way trip => if first and last waypoint are different
--
TRUNCATE `Table_Name`;
INSERT INTO `Table_Name` (`id`, `from`, `to`, `lat`, `lon`, `type`, `image`) VALUES\n"""

        today = datetime.now()
        log_msg = ""
        rows = []

        # debug code segment
        #path = "D:\\VolkerPetersen\\Dropbox\\Sailing\\OpenCPN_Routes\\spot_messages.spot"
        # end of debug code segment

        try:
            inputfile = open(os.path.join(path, filename), "r")
            xml = inputfile.read()
            inputfile.close
        except:
            print ("Error opening file: %s" %os.path.join(path, filename))

        soup = BeautifulSoup(xml, "xml")
        ctr = 0
        wps = soup.find_all('trkpt')

        path2 = os.path.join(path, filename)
        path2 = path.replace('.spot', '.sql')
        OutputFile = open(path2, "w")

        name = filename.replace('.spot', '')
        output = sql_header.replace('Table_Name', name)

        ctr = 0
        wp_ctr = 1
        for wp in wps:
            #print wp.contents  # converts BeautifulSoup content to list
            name = wp.contents[3].string
            time = wp.contents[1].string
            name = 'WP' + str(wp_ctr).zfill(3)
            wp_ctr += 1
            lat = wp['lat']
            lon = wp['lon']
            if (ctr == 0):
                output += "(" + str(ctr)+", '"+name+"', '" + name +"', " + "'" + str(lat) + "', '" +str(lon) + "', 'harbor', ''),\n"
                route = 'harbor'
                first_lat = lat
                first_lon = lon
            if (ctr > 0):
                """
                -----------------------------------------------------------------
                in OpenCPN mark Waypoints as follows:
                Diamonds for "regular WP on route"
                Circle for "Harbor"
                Anchorage for "Mooring / Anchorage"
                ------------------------------------------------------------------
                """
                if lat == first_lat and lon == first_lon:
                    route = 'harbor'
                else:
                    route = 'route'
                output += "(" + str(ctr)+", '" + old_name +"', '" + name +"', " + "'" + str(lat) + "', '" +str(lon) + "', '" + route + "', ''),\n"
            rows.append([name, time, lat, lon, route])
            #print "==> WP ", ctr, "  ", name, "  lat: ", lat, "   lon: ", lon
            ctr +=1
        output = output[:-2] + ";"
        OutputFile.write(output)
        OutputFile.close
        print (tabulate(rows, headers=["Name", "Time", "Latitude", "Longitude", "Route"], floatfmt=',.4f', numalign="right"))

        msg = "==> "+today.strftime("%Y-%m-%d  %H:%M:%S ") + " Route Parsing Function"
        msg = msg + "\nDone, parsed a total of "+str(ctr)+" waypoints"
        msg = msg + " from the SPOT route file " + path +"\n\n"
#        msg = msg + output
        log_msg = msg + log_msg
        log = log_msg + "\n\n" + log
        right.log.SetValue(log)

#--------------------------------------------------------------------------------------------
# Event handler to upload a MySQL-query file to the website MySQL DB
#--------------------------------------------------------------------------------------------
    def onUploadMySQLFile(self, event):
        global path, filename, right, log

        cwd1 = "D:/My Documents/Dropbox"  # Dell Descktop
        cwd2 = "D:/VolkerPetersen"        # Dell Laptop
        if (os.path.exists(cwd1) == True):
             # Home Desktop Dell XPS computer setup parameters
             cwd = cwd1
        elif (os.path.exists(cwd2) == True):
             # Volker's laptop computer
             cwd = cwd2
        else:
            print ("\nUnknown computer and root file system.  Terminating now.")
            return False

        path2 = os.path.join(cwd, "Dropbox/ProgramCode/PHP_Projects/toerns/sql_files/")
        path2 = os.path.normpath(path2)
        #print os.path.join(path2, "ToernDirectoryTable.sql")
        #print os.path.join(path2, filename)

        log_msg = ""
        msg1 = uploadMySQLfile(os.path.join(path2, "ToernDirectoryTable.sql"))
        if not msg1:
            msg1 = "\nError in uploadMySQL('ToernDirectoryTable.sql')!\n"
            print (msg1)
        else:
            if msg1['bplaced']['Truncate']['status'] == "success" \
                and msg1['bplaced']['Insert']['status'] == "success" \
                and msg1['Hostmonster']['Truncate']['status'] == "success" \
                and msg1['Hostmonster']['Insert']['status'] == "success":
                    msg1 = msg1['bplaced']['Insert']['msg']
            #print "\n%s table ToernDirectoryTable.sql" %msg1


        msg2 = uploadMySQLfile(os.path.join(path2, filename))
        if not msg2:
            msg2 = "\nError in uploadMySQL('%s')!\n" %filename
            print (msg2)
        else:
            if msg2['bplaced']['Truncate']['status'] == "success" \
                and msg2['bplaced']['Insert']['status'] == "success" \
                and msg2['Hostmonster']['Truncate']['status'] == "success" \
                and msg2['Hostmonster']['Insert']['status'] == "success":
                    msg2 = msg2['bplaced']['Insert']['msg']
            #print "\n%s table %s" %(msg1, filename)

        msg = "==> "+today.strftime("%Y-%m-%d  %H:%M:%S ") + " upload MySQL file to Website."
        msg = msg + "\nResults for ToernDirectoryTable.sql: %s"
        msg = msg + "\nResults for %s: %s"
        msg = msg %(msg1, filename, msg2)
        log_msg = msg + log_msg
        log = log_msg + "\n\n" + log
        right.log.SetValue(log)

#--------------------------------------------------------------------------------------------
# Event handler for Exit this Program
#--------------------------------------------------------------------------------------------
    def onTimeToExit(self, event):
        """Event handler for the button Close this Program."""
        global right, log
        dlg = wx.MessageDialog(None, 'Do you really want to quit this App?',
        'OK to Quit this App', wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            today = datetime.now()
            l = "\n================================================="
            l1 = l + "\nFile Renamer App ended: "+ today.strftime("%Y/%m/%d at %H:%M:%S ")
            log = l1 + l + "\n\n" + log
            logfilename = os.getcwd()+"\\NavigationRouteParser_log.log"
            inputfile = open(logfilename, "r")
            old_log = inputfile.read()
            inputfile.close
            log = log + old_log
            FILE = open(logfilename, "w")
            FILE.writelines(log)
            FILE.close()
            print ("Logfile: %s" %logfilename)
            self.Close()
        dlg.Destroy()

#--------------------------------------------------------------------------------------------
# Event handler for the About Menu item
#--------------------------------------------------------------------------------------------
    def onHelpAbout(self, event):
        msg = """The Navigation Route Parser App is a free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License, published by the Free Software Foundation."""

        # First we create and fill the info object
        year = datetime.now().strftime("%Y")
        info = wx.AboutDialogInfo()
        info.Name = "Navigation Route Parser App"
        info.Version = "2.1"
        info.Copyright = "(C) 2014-"+year+" Volker Petersen"
        info.Description = wordwrap(msg, 350, wx.ClientDC(self))
        info.WebSite = ("http://kaiserware.bplaced.net", "Volker Petersen's Sailing Trips")
        info.Developers = [ "Volker Petersen - volker.petersen01@gmail.com" ]

        licenseText = "GNU General Public License, published by the Free Software Foundation.\n\n"
        info.License = wordwrap(licenseText, 500, wx.ClientDC(self))

        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info)

def StringToDateTime(dateString, dateFormats):
    for dt_format in dateFormats:
        try:
            dateValue = datetime.strptime(dateString, dt_format)
            return dateValue
        except ValueError:
            dateValue = 0
    return dateValue

#--------------------------------------------------------------------------------------------
# Function to compute the distance and speed between two sequential Route waypoints
#
#   *1 (harbor)    X1 (timed WP)   .......  X1 (timed WP)    *2 (harbor)
#   *1 - *2 = harbor_distance
#   X1 - X2 = leg_distance
#   . - .   = distance (distance between any two adjacent WPs)
#--------------------------------------------------------------------------------------------
def ComputeRouteDistances(xml, verbose, skipWP, noSpeed):
    dateFormats = []
    dateFormats.append('%Y_%m_%d_%H%M')
    dateFormats.append('%b-%d-%Y %H:%M')
    dateFormats.append('%Y%m%d_%H%M')
    dateFormats.append('%Y-%m-%d %H:%M')
    dateFormats.append('%Y-%m-%d | %H:%M')
    dateFormats.append('%Y-%m-%dT%H:%M:%SZ')

    genericWPs = []
    genericWPs.append('NM0')
    genericWPs.append('0')

    degree = '\xb0'
    soup = BeautifulSoup(xml, "xml")

    wps = soup.find_all('rtept')

    rows = []
    last_lat = 0.0
    last_lon = 0.0             # lat/lon of previous WP
    wp_date = ""               # date/time at current WP
    leg_start_date = ""        # date/time at first "timed" WP
    total_trip_distance = 0.0  # total distance traveled on this trip
    distance = 0.0             # distance between two adjacent WPs
    leg_distance = 0.0         # distance between two adjacent "timed" WPs
    leg_elapsed = 0.0          # elapsed time between two adjacent "timed" WPs
    departure_flag = False     # set flag to true to pick up time of first WP after leaving port
    sum_legs_distance = 0.0    # the sum distance traveled on all timed legs
    sum_legs_time = 0.0        # the sum time traveled on all timed legs
    avg_speed = 0.0
    for wp in wps:
        lat = float(wp['lat'])
        lon = float(wp['lon'])
        name = wp.find('name').text
        time = wp.find('time').text
        symbol = (wp.find('sym').text).lower()

        layover = (symbol == "harbor" or symbol == "circle" or symbol == "anchorage")
        if (layover):
            departure_flag = True

        generic = False
        for genericWP in genericWPs:
            generic = (generic or name.startswith(genericWP))

        if (departure_flag and isinstance(StringToDateTime(time, dateFormats), datetime)):
            leg_start_date =  StringToDateTime(time, dateFormats)
            departure_flag = False

        if (last_lat!=0.0 and last_lon!=0.0):
            distance = calc_distance(last_lat, last_lon, lat,lon)
        else:
            distance = 0.0

        leg_distance += distance
        total_trip_distance += distance

        last_lat = lat
        last_lon = lon

        skippingWP = skipWP and generic
        #print "WP=%s, skippingWP=%s, skipWP=%s, generic=%s" %(name, skippingWP, skipWP, generic)
        if (not skippingWP):
            if (isinstance(StringToDateTime(name, dateFormats), datetime)):
                wp_date = StringToDateTime(name, dateFormats)
            else:
                wp_date = 0

            # compute speed / etmal for the current leg from leg_start_date to wp_date
            speed = 0
            etmal = 0
            if (isinstance(wp_date, datetime) and isinstance(leg_start_date, datetime)):
                elapsed = wp_date-leg_start_date
                leg_elapsed = elapsed.days*24+elapsed.seconds/3600.0
                if leg_elapsed > 0.0:
                    speed = leg_distance / leg_elapsed
                    etmal = leg_distance * 24.0/leg_elapsed
                sum_legs_distance += leg_distance
                sum_legs_time += leg_elapsed
                leg_start_date = wp_date

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
                rows.append([name, lat_str, lon_str, leg_distance, leg_elapsed, speed, etmal])
            leg_start_date = wp_date
            leg_elapsed = 0
            leg_distance = 0

        # end of the WP skipping if clause "if (not skippingWP):"
    # end of the loop accross all WPs  "for wp in wps:"

    if verbose:
        if noSpeed:
            print (tabulate(rows, headers=["WP Name", "Lat", "Lon", "Distance"], floatfmt=',.2f', numalign="right"))
        else:
            print (tabulate(rows, headers=["WP Name", "Lat", "Lon", "Distance", "Time", "Speed", "Etmal"], floatfmt=',.2f', numalign="right"))

        print ("\nTotal Trip Distance: {:9,.2f}nm".format(total_trip_distance))
        if (total_trip_distance > sum_legs_distance and not noSpeed):
            print ("Timed Legs Distance: {:9,.2f}nm".format(sum_legs_distance)+"  (%0.1f%%)" %(sum_legs_distance/total_trip_distance*100.0))
        if (sum_legs_time!=0.0 and not noSpeed):
            avg_speed = sum_legs_distance / sum_legs_time
            print ("Average Speed:       {:9,.2f}kts".format(avg_speed))
    return

#--------------------------------------------------------------------------------------------
# Function to compute the distance between two Lat/Lon coordinates
#--------------------------------------------------------------------------------------------
def calc_distance(latFrom, lonFrom, latTo, lonTo):
    KM_NM = 0.539706            # km to nm conversion factor
    RADIUS = 6371.0*KM_NM       # Earth RADIUS in nm
    dLat = math.radians(latTo - latFrom)
    dLon = math.radians(lonTo - lonFrom)
    lat1 = math.radians(latFrom)
    lat2 = math.radians(latTo)

    a = math.sin(dLat / 2.0) * math.sin(dLat/2.0) + math.sin(dLon/2.0) * math.sin(dLon/2.0) * math.cos(lat1) * math.cos(lat2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return RADIUS * c


#--------------------------------------------------------------------------------------------
# Function to load the configuration from a json file
#--------------------------------------------------------------------------------------------
def read_json(filename):
    with open(filename, 'r') as fp:
        js = json.load(fp)
    return js

#--------------------------------------------------------------------------------------------
# Function to save the configuration to a json file
#--------------------------------------------------------------------------------------------
def write_json(filename, js):
    with open(filename, 'wb') as fp:
        json.dump(js, fp)

#--------------------------------------------------------------------------------------------
# Function to parse the waypoint and route information from the .gpx file
# into a MySQL query file
#--------------------------------------------------------------------------------------------
def parseSQLRouteFile(pathGPX, pathSQL, filename):
    sql_header = """-- phpMyAdmin SQL Dump
-- version 3.3.9
-- http://www.phpmyadmin.net

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

--
-- Database: `map`
-- Table structure for table `Table_Name`
--

CREATE TABLE IF NOT EXISTS `Table_Name` (
`id` int(11) DEFAULT NULL,
`from` text,
`to` text,
`lat` text,
`lon` text,
`type` text,
`image` text
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
--
-- Dumping data for table `Table_Name`
-- roundtrip    => if first and last waypoint in the file are the same
-- one-way trip => if first and last waypoint are different
--
TRUNCATE `Table_Name`;
INSERT INTO `Table_Name` (`id`, `from`, `to`, `lat`, `lon`, `type`, `image`) VALUES\n"""

    today = datetime.now()
    log_msg = ""
    rows = []

    try:
        fn = os.path.join(pathGPX, filename)
        inputfile = open(fn, "r")
        xml = inputfile.read()
        inputfile.close
    except:
        print ("Error opening file: %s" %fn)
        return False

    soup = BeautifulSoup(xml, "xml")
    ctr = 0
    wps = soup.find_all('rtept')

    filename2 = filename.replace('gpx', 'sql')
    path2 = os.path.join(pathSQL, filename2)

    #print pathSQL, "\n", filename, "\n", path2

    OutputFile = open(path2, "w")

    #fpath, fname = os.path.split(path)
    name = filename.replace('.gpx', '')
    output = sql_header.replace('Table_Name', name)

    ctr = 0
    wp_ctr = 1
    old_lat = 0.0
    old_lon = 0.0
    cum_dist = 0.0
    total = 0.0
    for wp in wps:
        #print wp.contents  # converts BeautifulSoup content to list
        #print wp.contents[3].string, "Type: "+wp.contents[5].string
        #i = 0
        #for s in wp.contents:
        #    print i, ":", s,
        #    i += 1
        #print "|----end of wp content!"

        name = wp.find('name').text
        #time = wp.find('time').text
        symbol = (wp.find('sym').text).lower()

        if name.startswith('NM') or name.startswith('WP') or name.startswith('0'):
            name = 'WP' + str(wp_ctr).zfill(3)
            wp_ctr += 1
        lat = wp['lat']
        lon = wp['lon']
        if (ctr == 0):
            output += "(" + str(ctr)+", '"+name+"', '" + name +"', " + "'" + str(lat) + "', '" +str(lon) + "', 'harbor', ''),\n"
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
            "circle" or "harbor" for "Harbor"
            "anchorage" for "Mooring / Anchorage"
            ------------------------------------------------------------------
            """
            distance = calc_distance(old_lat, old_lon, float(lat), float(lon))
            cum_dist = cum_dist + distance
            total = total + distance
            #print "WP"+str(ctr)+" of 'symbol':"+symbol+" after "+str(distance)+"nm"
            if lat == first_lat and lon == first_lon:
                route = 'harbor'
                print ("WP"+str(ctr)+": arrived after final leg at '"+route+"' "+name+" after %0.2fnm." %(cum_dist))
            else:
                if 'anchorage' in symbol:
                    route = 'mooring'
                    print ("WP"+str(ctr)+": arrived at '"+route+"' "+name+" after %0.2fnm." %(cum_dist))
                    cum_dist = 0.0
                elif 'circle' in symbol or 'harbor' in symbol:
                    route = 'harbor'
                    print ("WP"+str(ctr)+": arrived at  '"+route+"' "+name+" after %0.2fnm." %(cum_dist))
                    cum_dist = 0.0
                elif 'empty' in symbol:
                    route = 'none'
                    #print "Route = ", route
                else:
                    route = 'route'
            output += "(" + str(ctr)+", '" + old_name +"', '" + name +"', " + "'" + str(lat) + "', '" +str(lon) + "', '" + route + "', ''),\n"
        #print "from", old_name, "to", name
        old_name = name
        rows.append([ctr, name, lat, lon, route])
        old_lat = float(lat)
        old_lon = float(lon)
        ctr +=1
    print ("Total trip across %d waypoints: %0.2fnm." %(ctr, total))
    output = output[:-2] + ";"
    OutputFile.write(output)
    OutputFile.close
    #print tabulate(rows, headers=["WP #", "Name", "Latitude", "Longitude", "Route"], floatfmt=',.4f', numalign="right")

    msg = "\n==> "+today.strftime("%Y-%m-%d  %H:%M:%S ") + " Route Parsing Function"
    msg = msg + "\nDone, parsed a total of "+str(ctr)+" waypoints"
    msg = msg + " from the OpenCPN route file " + pathGPX + " saved to "+pathSQL+"\n\n"
#        msg = msg + output
    log_msg = msg + log_msg
    return log_msg


#--------------------------------------------------------------------------------------------
# Run the program
#--------------------------------------------------------------------------------------------
if __name__ == "__main__":
    global path, log, default_settings, settings, sql


    # configuration data
    supported_devices = {'Desktop': ["D:\VolkerPetersen", "D:\My Documents\Google Drive"],
                         'Laptop': ["D:\VolkerPetersen","D:\VolkerPetersen\Google Drive"]}

    unsupported_device = True
    for device in supported_devices:
        if (os.path.exists(supported_devices[device][1])):
            cwd = supported_devices[device][0]
            unsupported_device = False

    if (unsupported_device):
        print("\nUnknown computer and root file system.  Terminating now.\n")
        sys.exit()

    sql = os.path.normpath(os.path.join(cwd, "Dropbox/ProgramCode/PHP_Projects/toerns/sql_files/"))
    print(sql)
    # D:\VolkerPetersen\Dropbox\ProgramCode\Python_Projects
    today = datetime.now()
    log = "Navigation Route Parser App started: "+ today.strftime("%Y/%m/%d at %H:%M:%S ")

    # fetch the content from the default settings file
    settings = {}
    cwd = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    default_settings = cwd+'\\Navigation_Route_Parser_Settings.json'
    try:
        settings = read_json(default_settings)
        path = settings['lastGPX']
    except:
        path = os.getcwd()

    # launch the WX app
    app = wx.App(redirect=True)
    frame = Navigation_Route_Parser()
    frame.Show()
    app.MainLoop()
