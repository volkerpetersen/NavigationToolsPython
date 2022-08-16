#!/usr/bin/env python
# -- coding: utf-8 --
# ------------------------------------------------------------------------------
__author__ = "Volker Petersen <volker.petersen01@gmail.com>"
__app__ = "Navigation Tools App"
__version__ = "Version: 2.1.5, Python 3.8"
__date__ = "Date: 2011/09/26 | 2015/08/08 | 2019/11/14 | 2022/06/29"
__copyright__ = "Copyright (c) 2011 Volker Petersen"
__license__ = "GNU General Public License, published by the Free Software Foundation"
__doc__ = """
--------------------------------------------------------------------------------
The 'Navigation Tools App' integrates various tools into one GUI.
The tools convert route data between various file formats (gpx, kml, sql, spot).
In addition the software can upload SQL files to the Toern website and compute
route statistics.

OpenCPN to MySQL Waypoint legend:
    Generic WP name options-------> NMxxx, WPxxx, WPTxxx, or 0xxx
    Diamonds/non-Generic WP name--> regular WP on route
    Diamonds/Generic WP name------> non-visible WP on route
    Empty-------------------------> non-visible WP on route
    Circle------------------------> Harbor
    Service-Marina----------------> Harbor
    Anchorage---------------------> Mooring / Anchorage

The program computes the Time, Speed, and Etmals between WPs that
contain a <desc></desc> tag with these entry options:
    arrival 2019-09-25 19:30    (arrival date/time at this WP)
    departure 2019-09-26 09:37  (departure date/time from this WP)
    timedleg 2019-09-26 09:37   (arrival and departure at/from this WP)
    poi                         (Point of Interest on route not being listed)
    homeport                    (designates the Waypoint from which a round-trip
                                 toern originates. Add departure and arrival
                                 times using the above keywords in add'l lines)

Yellowbrick Google Earth files are available at "yb.tl/racenamexxxx.kml"
--------------------------------------------------------------------------------
"""
try:
    import sys
    import wx
    import wx.adv
    import os
    from bs4 import BeautifulSoup
    from tabulate import tabulate
    from datetime import datetime
    from uploadMySQL import uploadMySQLfile
    from NavToolsLib import NavTools
except ImportError as e:
    print(f"Import error: {str(e)}\nAborting the program {__app__}")
    sys.exit()

# --------------------------------------------------------------------------------------------
# main class NavigationTools using a SplitterWindowContainer
# --------------------------------------------------------------------------------------------


class NavigationTools(wx.Frame):
    """  main Class for the Navigation Tools - builds the GUI"""

    def __init__(self, settings, navTools):
        today = datetime.now()
        self.settings = settings
        self.navTools = navTools
        self.cwd = settings["cwd"]
        self.pathGPX = settings["gpxPath"]
        self.pathSQLite = settings["sqlitePath"]
        self.filename = settings["lastRoute"]
        self.toernDirectory = settings["toernDirectory"]
        self.extension = {}
        self.extension["gpx"] = ".gpx"
        self.extension["sql"] = ".sql"
        self.extension["txt"] = ".txt"
        self.extension["spot"] = ".spot"
        self.log = (
            f"==> {__app__} launched: "
            f"{today.strftime('%Y/%m/%d at %H:%M:%S')}"
        )
        self.log += f"\nUsing data from the file '{self.pathGPX}\{self.filename}'"
        self.log += f"\n{__doc__}"
        self.font = wx.Font(11, wx.MODERN, wx.NORMAL,
                            wx.NORMAL, False, u"Consolas")

        appWidth = 1100
        appHeight = 600

        # create the app window
        wx.Frame.__init__(
            self,
            None,
            wx.ID_ANY,
            title=__app__,
            pos=(10, 60),
            size=(appWidth, appHeight),
        )

        self.panel = wx.Panel(self)

        icon = os.path.join(self.cwd, "icons/sailing_fav.ico")
        favicon = wx.Icon(icon, wx.BITMAP_TYPE_ICO, 16, 16)
        wx.Frame.SetIcon(self, favicon)

        self.statusBar = self.CreateStatusBar()
        self.statusBar.SetStatusText(
            f"GPX Route: '{self.filename}'    at: '{self.pathGPX}'"
        )

        leftWidth = 170
        self.leftPanel = wx.Panel(self.panel, size=(leftWidth, appHeight))
        self.rightPanel = wx.TextCtrl(
            self.panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_BESTWRAP | wx.TE_RICH2,
        )

        self.horizontal = wx.BoxSizer()

        self.horizontal.Add(self.leftPanel)
        self.horizontal.Add(self.rightPanel, proportion=1, flag=wx.EXPAND)

        self.vertical = wx.BoxSizer(wx.VERTICAL)
        self.vertical.Add(self.horizontal, proportion=1, flag=wx.EXPAND)
        self.panel.SetSizerAndFit(self.vertical)
        self.Show()

        self.rightPanel.SetFont(self.font)
        self.rightPanel.SetBackgroundColour(wx.LIGHT_GREY)
        self.rightPanel.SetValue(self.log)

        # setup the Menus
        menubar = wx.MenuBar()

        # FILE menu options
        fileMenu = wx.Menu()
        menubar.Append(fileMenu, "&File")
        file_directory = fileMenu.Append(
            wx.ID_ANY, "Select &Route File\tAlt-R")
        file_exit = fileMenu.Append(wx.ID_EXIT, "E&xit\tAlt-X")
        self.Bind(wx.EVT_MENU, self.onSelectRouteFile, file_directory)
        self.Bind(wx.EVT_MENU, self.onTimeToExit, file_exit)

        # CONVERT menu options
        convertMenu = wx.Menu()
        menubar.Append(convertMenu, "&Convert")
        convert_GPX_MySQL = convertMenu.Append(
            wx.ID_ANY, "Parse &GPX->MySQL File\tAlt-G"
        )
        convert_MySQL_GPX = convertMenu.Append(
            wx.ID_ANY, "Parse &MySQL->GPX File\tAlt-M"
        )
        convert_SPOT_MySQL = convertMenu.Append(
            wx.ID_ANY, "Parse &SPOT->MySQL File\tAlt-S"
        )
        convert_Expedition_GPX = convertMenu.Append(
            wx.ID_ANY, "Parse &Expedition->GPX File\tAlt-E"
        )
        convert_KML_GPX = convertMenu.Append(
            wx.ID_ANY, "Parse &KML->GPX File\tAlt-K")
        convert_uploadMySQL = convertMenu.Append(
            wx.ID_ANY, "&Upload MySQL File to Sites\tAlt-U"
        )
        convert_addImagesToRoute = convertMenu.Append(
            wx.ID_ANY, "Add &Image to Route\tAlt-I"
        )
        self.Bind(wx.EVT_MENU, self.onParseGPXtoSQLRouteFile, convert_GPX_MySQL)
        self.Bind(wx.EVT_MENU, self.onParseSQLtoGPXRouteFile, convert_MySQL_GPX)
        self.Bind(wx.EVT_MENU, self.onParseSPOTRouteFile, convert_SPOT_MySQL)
        self.Bind(wx.EVT_MENU, self.onParseExpeditionRouteFile,
                  convert_Expedition_GPX)
        self.Bind(wx.EVT_MENU, self.onParseKMLRouteFile, convert_KML_GPX)
        self.Bind(wx.EVT_MENU, self.onUploadMySQLFile, convert_uploadMySQL)
        self.Bind(wx.EVT_MENU, self.onAddImagesToRoute,
                  convert_addImagesToRoute)

        # ANALYZE menu options
        analyzeMenu = wx.Menu()
        menubar.Append(analyzeMenu, "&Analyze")
        analyzeRoute = analyzeMenu.Append(
            wx.ID_ANY, "&Compute Distances\tAlt-C")
        self.Bind(wx.EVT_MENU, self.onComputeDistances, analyzeRoute)

        # HELP menu options
        helpMenu = wx.Menu()
        menubar.Append(helpMenu, "&Help")
        about = helpMenu.Append(wx.ID_ABOUT, "&About\tAlt-A")
        self.Bind(wx.EVT_MENU, self.onHelpAbout, about)

        self.SetMenuBar(menubar)

        blength = 130
        bheight = 30
        lstart = 20
        yoffset = 50
        y = 15
        b1 = wx.Button(
            self.leftPanel,
            wx.ID_ANY,
            "Select Route File",
            (lstart, y),
            (blength, bheight),
        )
        self.Bind(wx.EVT_BUTTON, self.onSelectRouteFile, b1)
        b1.SetToolTipString(
            "Select the navigation route\nfile to be processed.\n")
        y = y + yoffset

        b5 = wx.Button(
            self.leftPanel,
            wx.ID_ANY,
            "Parse GPX->MySQL",
            (lstart, y),
            (blength, bheight),
        )
        self.Bind(wx.EVT_BUTTON, self.onParseGPXtoSQLRouteFile, b5)
        b5.SetToolTipString(
            "Parse the route and waypoint information \n"
            "from an OpenCPN .gpx file to MySQL-query file.\n"
        )
        y = y + yoffset

        b6 = wx.Button(
            self.leftPanel,
            wx.ID_ANY,
            "Parse MySQL->GPX",
            (lstart, y),
            (blength, bheight),
        )
        self.Bind(wx.EVT_BUTTON, self.onParseSQLtoGPXRouteFile, b6)
        b6.SetToolTipString(
            "Parse the route and waypoint information \n"
            "from a MySQL-query file to an OpenCPN .gpx file.\n"
        )
        y = y + yoffset

        b7 = wx.Button(
            self.leftPanel,
            wx.ID_ANY,
            "Parse SPOT->MySQL",
            (lstart, y),
            (blength, bheight),
        )
        self.Bind(wx.EVT_BUTTON, self.onParseSPOTRouteFile, b7)
        b7.SetToolTipString(
            "Parse the route and waypoint information \n"
            "from a SPOT file to a MySQL-query file.\n"
        )
        y = y + yoffset

        b8 = wx.Button(
            self.leftPanel,
            wx.ID_ANY,
            "Parse Expedition->GPX",
            (lstart, y),
            (blength, bheight),
        )
        self.Bind(wx.EVT_BUTTON, self.onParseExpeditionRouteFile, b8)
        b8.SetToolTipString(
            "Parse the route and waypoint information \n"
            "from an Expedition gpx file to an OpenCPN gpx file.\n"
        )
        y = y + yoffset

        b9 = wx.Button(
            self.leftPanel,
            wx.ID_ANY,
            "Parse YB KML->GPX",
            (lstart, y),
            (blength, bheight),
        )
        self.Bind(wx.EVT_BUTTON, self.onParseKMLRouteFile, b9)
        b9.SetToolTipString(
            "Parse the route and waypoint information \n"
            "from a Yellowbrick Tracker kml file to an OpenCPN gpx file.\n"
        )
        y = y + yoffset

        b10 = wx.Button(
            self.leftPanel,
            wx.ID_ANY,
            "Upload MySQL to Sites",
            (lstart, y),
            (blength, bheight),
        )
        self.Bind(wx.EVT_BUTTON, self.onUploadMySQLFile, b10)
        b10.SetToolTipString(
            "Upload a MySQL-query file \n" "to the two A2 MySQL website DBs.\n"
        )
        y = y + yoffset

        # b10 = wx.Button(self.leftPanel, wx.ID_ANY, "Add Images", (lstart,y), (blength,bheight))
        # self.Bind(wx.EVT_BUTTON, self.onAddImagesToRoute, b10)
        # b10.SetToolTipString("Add Images to Route using the image geo tags\n")
        # y = y + yoffset

        b11 = wx.Button(
            self.leftPanel,
            wx.ID_ANY,
            "Compute Distances",
            (lstart, y),
            (blength, bheight),
        )
        self.Bind(wx.EVT_BUTTON, self.onComputeDistances, b11)
        b11.SetToolTipString(
            "Compute Distances, Speed, and Etmals between Waypoints \n"
        )
        y = y + yoffset + 20

        b12 = wx.Button(
            self.leftPanel, wx.ID_ANY, "Exit App", (
                lstart, y), (blength, bheight)
        )
        self.Bind(wx.EVT_BUTTON, self.onTimeToExit, b12)

    # --------------------------------------------------------------------------
    # Event handler to add images to Route Waypoints
    # https://www.sylvaindurand.org/gps-data-from-photos-with-python/
    # --------------------------------------------------------------------------
    def onAddImagesToRoute(self, event):
        """ add images to Route Waypoints using the geo tags from the immages"""
        pass

    # --------------------------------------------------------------------------
    # Event handler to Compute Distances, Speed, and Etmals between Waypoints
    # --------------------------------------------------------------------------
    def onComputeDistances(self, event):
        """ compute distances, speed, and Etmals between Waypoints """

        try:
            file = os.path.join(
                self.pathGPX, self.filename + self.extension["gpx"])
            inputfile = open(file, "r")
            xml = inputfile.read()
            inputfile.close()
        except:
            print(f"Error opening file: '{file}'")

        msg = self.navTools.ComputeRouteDistances(
            xml, verbose=False, skipWP=True, noSpeed=False)
        # wx.MessageBox(msg, "Route Analysis Results", wx.OK | wx.ICON_NONE)
        msg = "==> Evaluated route %s\n\n" % self.filename + msg
        self.log = msg + "\n\n" + self.log
        self.rightPanel.SetValue(self.log + "\n\n")
        return

    # --------------------------------------------------------------------------
    # Event handler to Select an OpenCPN or MySQL route file to be parsed
    # --------------------------------------------------------------------------
    def onSelectRouteFile(self, event):
        """ select a route file from disk to work on next """

        filters = "OpenCPN route files (*.gpx)|*.gpx|MySQL route file (*.sql)|*.sql|All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self,
            "Choose an OpenCPN .gpx route file:",
            wildcard=filters,
            style=wx.FD_OPEN,
        )
        dlg.SetDirectory(self.pathGPX)
        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it.
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if os.path.isfile(path):
                filename = os.path.basename(path).split('.')
                self.filename = filename[0]
                extension = filename[1].upper()
                self.pathGPX = os.path.splitext(os.path.dirname(path))[0]
                self.statusBar.SetStatusText(
                    f"{extension} Route: '{self.filename}'    at: '{self.pathGPX}'"
                )
                self.log = (
                    "==> Set route file to: "
                    + os.path.join(self.pathGPX, self.filename)
                    + "\n\n"
                    + self.log
                )
                self.navTools.saveConfig(self.cwd, self.filename)
                if extension == 'GPX':
                    msg = self.navTools.verifyGPXRouteFile(
                        self.pathGPX, self.filename+".gpx")
                    self.log = msg + self.log
            else:
                msg = f"==> File '{path}' not found. Couldn't update Route file.\n\n"
                self.log = msg + self.log
            self.rightPanel.SetValue(self.log + "\n\n")

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()

    # --------------------------------------------------------------------------
    # Event handler to parse the waypoint and route information from the .gpx
    # file into a MySQL query file
    # --------------------------------------------------------------------------
    def onParseGPXtoSQLRouteFile(self, event):
        """ parse a GPX route file into a MySQL route file """

        self.log = (
            self.navTools.parseSQLRouteFile(self.pathGPX, self.pathSQLite,
                                            self.filename) + self.log
        )
        self.rightPanel.SetValue(self.log + "\n\n")

    # --------------------------------------------------------------------------
    # Event handler to parse the waypoint and route information from the MySQL
    # file into a OpenCPN .gpx file
    # --------------------------------------------------------------------------
    def onParseSQLtoGPXRouteFile(self, event):
        """ parse a MySQL route file into a GPX route file """

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

        try:
            filename = self.filename + self.extension["sql"]
            inputfile = open(os.path.join(self.pathSQLite, filename), "r")
            xml = inputfile.read()
            inputfile.close()

        except:
            print("Error opening file: %s" % self.pathSQLite)

        values = ") VALUES"
        if values in xml:
            # print (xml.index(values))
            xml = xml[xml.index(values) + len(values):]
            xml = xml.replace(");", "),")
            wps = xml.split("),")
        else:
            msg = (
                "==> "
                + today.strftime("%Y-%m-%d  %H:%M:%S ")
                + " MySQL Route Parsing Function"
            )
            msg = (
                msg
                + "\nDidn't find any waypoints in		MySQL - missing '"
                + values
                + "' string."
            )
            msg = msg + " in the MySQL route file " + self.pathSQLite + "\n\n"
            log_msg = msg + log_msg
            self.log = log_msg + "\n\n" + self.log
            self.rightPanel.SetValue(self.log + "\n\n")
            return

        filename = self.filename + self.extension["gpx"]
        # print(os.path.join(self.pathGPX, filename2))
        OutputFile = open(os.path.join(
            self.settings['sqlitePath'], filename), "w")

        output = gpx_header.replace("Route Name", self.filename)

        wp_ctr = 1
        for wp in wps:
            wp_data = wp.split(", ")
            # print (len(wp_data), wp)
            if len(wp_data) > 3:
                lat = wp_data[3].replace("'", "")
                lon = wp_data[4].replace("'", "")
                name = wp_data[2].replace("'", "")
                output += '<rtept lat="' + lat + '" lon="' + lon + '">\n'
                output += "<time></time>\n"
                output += "<name>" + name + "</name>\n"
                if wp_data[2].startswith("WP0"):
                    output += "<sym>empty</sym>\n"
                elif len(wp_data) > 5:
                    output += "<sym>" + \
                        wp_data[5].replace("'", "") + "</sym>\n"
                else:
                    output += "<sym>empty</sym>\n"

                output += "<type>WPT</type>\n"
                output += (
                    "<extensions><opencpn:guid>717ab0000-eb25-48bc-930a-%012d" % wp_ctr
                )
                output += "</opencpn:guid>\n<opencpn:viz>0</opencpn:viz>\n<opencpn:viz_name>0</opencpn:viz_name>\n</extensions>\n</rtept>\n"
                wp_ctr += 1

        output += "</rte>\n</gpx>\n"
        # print(output)

        OutputFile.write(output)
        OutputFile.close()

        msg = (
            "==> "
            + today.strftime("%Y-%m-%d  %H:%M:%S ")
            + " MySQL Route Parsing Function"
        )
        msg = msg + "\nDone! Converted " + str(wp_ctr - 1) + " waypoints in"
        msg = msg + " from the MySQL route file "
        msg = msg + os.path.join(self.pathSQLite,
                                 self.filename + self.extension["sql"]) + " to a "
        msg = (
            msg + os.path.join(self.pathGPX, self.filename +
                               self.extension["gpx"]) + " file.\n\n"
        )
        log_msg = msg + log_msg
        self.log = log_msg + "\n\n" + self.log
        self.rightPanel.SetValue(self.log + "\n\n")
        return

    # --------------------------------------------------------------------------
    # Event handler to parse the waypoint and route information from a
    # Google Earth KML file into an OpenCPN gpx file
    # --------------------------------------------------------------------------
    def onParseKMLRouteFile(self, event):
        today = datetime.now()
        filename = self.filename.split(".")[0]
        boatname = "ZigZag"
        dlg = wx.TextEntryDialog(self, "Please enter boat name", "Boat name")
        dlg.SetValue(boatname)
        if dlg.ShowModal() == wx.ID_OK:
            boatname = dlg.GetValue()
        dlg.Destroy()

        msg = (
            "\n\n==> "
            + today.strftime("%Y-%m-%d        %H:%M:%S ")
            + " KML->GPX Route Parsing Function\n\n"
        )

        dlg = MyDialog(self, "Crunching data, please wait...")
        dlg.Show()

        msg += self.navTools.parseKMLRouteFile(
            self.pathGPX, filename, boatname)

        dlg.Destroy()

        self.log = msg + "\n\n" + self.log
        self.rightPanel.SetValue(self.log + "\n\n")

        return

    # --------------------------------------------------------------------------
    # Event handler to parse the waypoint and route information from the
    # Expedition gpx file into an OpenCPN gpx file
    # --------------------------------------------------------------------------

    def onParseExpeditionRouteFile(self, event):
        """ parse an Expedition route file into a GPX route file """

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

        try:
            filename = self.filename
            # print("read ", os.path.join(self.pathGPX, filename))
            inputfile = open(os.path.join(self.pathGPX, filename), "r")
            xml = inputfile.read()
            inputfile.close()
        except:
            print(
                f"Error opening file: {os.path.join(self.pathGPX, filename)}")
            return

        wps = ""
        soup = BeautifulSoup(xml, "xml")
        #wps = soup.find_all("trkpt")
        wps = soup.find_all("wpt")

        if wps is None:
            values = "???"
            msg = (
                "==> "
                + today.strftime("%Y-%m-%d	 %H:%M:%S ")
                + " Expedition Route Parsing Function"
            )
            msg += (
                f"\nDidn't find any waypoints in Expedition gpx file"
                f" - missing '{values}' string."
                f" in the Expedition route file {self.pathGPX} \n\n"
            )

            log_msg = msg + log_msg
            self.log = log_msg + "\n\n" + self.log
            self.rightPanel.SetValue(self.log + "\n\n")
            return

        fname = filename.replace(self.extension['txt'], "")
        filename = fname + self.extension["gpx"]
        # print(os.path.join(self.pathGPX, filename))
        OutputFile = open(os.path.join(self.pathGPX, filename), "w")

        output = gpx_header.replace("Route Name", fname)

        wp_ctr = 1
        for wp in wps:
            wp_time = wp.find_all("time")
            # print ("wp	 : %s" %wp)
            # print ("lat: %s" %wp['lat'])
            # print ("lon: %s" %wp['lon'])
            # print ("time: %s" %wp_time[0])

            new_wp = f"<rtept lat='{wp['lat']}' lon='{wp['lon']}'>\n"
            if isinstance(wp_time, list) and len(wp_time) > 0:
                new_wp += f"{wp_time[0]}\n"
            else:
                new_wp += f"<time>2022-01-01T00:00:00Z</time>\n"
            new_wp += f"<name>ExpWP{str(wp_ctr).zfill(4)}</name>\n"
            new_wp += f"<sym>empty</sym>\n"
            new_wp += f"<type>WPT</type>\n<extensions>"
            new_wp += f"<opencpn:guid>717ab0000-eb25-48bc-930a-{wp_ctr:012d}"
            new_wp += f"</opencpn:guid>\n<opencpn:viz>0</opencpn:viz>\n<opencpn:viz_name>0</opencpn:viz_name>\n</extensions>\n</rtept>\n"

            output += new_wp
            # print("WP %i\n%s" %(wp_ctr,new_wp))

            wp_ctr += 1

        output += "</rte>\n</gpx>\n"
        # print(output)

        OutputFile.write(output)
        OutputFile.close()

        msg = (
            f"==> {today.strftime('%Y-%m-%d %H:%M:%S}')}"
            f" Expedition Route Parsing Function"
            f"\nDone! Converted {(wp_ctr - 1)} waypoints"
            f" from the Expedition route file format"
            f"'{os.path.join(self.pathGPX, fname+self.extension['txt'])}'"
            f" to the GPX file format "
            f"'{os.path.join(self.pathGPX, fname+self.extension['gpx'])}'\n\n"
        )

        self.filename = fname + self.extension["gpx"]
        log_msg = msg + log_msg
        self.log = log_msg + "\n\n" + self.log
        self.rightPanel.SetValue(self.log + "\n\n")
        return

    # --------------------------------------------------------------------------
    # Event handler to parse the waypoint and route information from the SPOT
    # file into a MySQL query file
    # --------------------------------------------------------------------------
    def onParseSPOTRouteFile(self, event):
        """ parse a SPOT route file into a SQLite route file """

        today = datetime.now()
        log_msg = ""
        rows = []

        try:
            filename = self.filename + self.extension["spot"]
            inputfile = open(os.path.join(self.pathGPX, filename), "r")
            xml = inputfile.read()
            inputfile.close()
        except:
            print(
                f"Error opening file: {os.path.join(self.pathGPX, filename)}")

        soup = BeautifulSoup(xml, "xml")
        wps = soup.find_all("trkpt")

        filename = self.filename + self.extension["sql"]
        path2 = os.path.join(self.pathSQLite, filename)
        OutputFile = open(path2, "w")

        output = self.navTools.sql_header.replace("Table_Name", self.filename)

        ctr = 0
        wp_ctr = 1
        for wp in wps:
            # print wp.contents	  # converts BeautifulSoup content to list
            name = wp.contents[3].string
            time = wp.contents[1].string
            name = "WP" + str(wp_ctr).zfill(3)
            wp_ctr += 1
            lat = wp["lat"]
            lon = wp["lon"]
            if ctr == 0:
                output += (
                    f"({ctr}, '{name}', '{name}', '{lat}', '{lon}'"
                    f", 'harbor', ''),\n"
                )
                route = "harbor"
                first_lat = lat
                first_lon = lon
                old_name = name
            if ctr > 0:
                """
                -----------------------------------------------------------------
                in OpenCPN mark Waypoints as follows:
                Diamonds for "regular WP on route"
                Circle for "Harbor"
                Anchorage for "Mooring / Anchorage"
                ------------------------------------------------------------------
                """
                if lat == first_lat and lon == first_lon:
                    route = "harbor"
                else:
                    route = "route"
                output += (
                    f"({ctr}, '{old_name}', '{name}', '{lat}', '{lon}'"
                    f"', '{route}', '', ''),\n"
                )
                old_name = name
            rows.append([name, time, lat, lon, route])
            # print("==> WP ", ctr, "  ", name, "  lat: ", lat, "   lon: ", lon)
            ctr += 1
        output = output[:-2] + ";"
        OutputFile.write(output)
        OutputFile.close()
        print(
            tabulate(
                rows,
                headers=["Name", "Time", "Latitude", "Longitude", "Route"],
                floatfmt=",.4f",
                numalign="right",
            )
        )

        msg = (f"==> {today.strftime('%Y-%m-%d  %H:%M:%S')}"
               f" Route Parsing Function"
               f"\nDone, parsed a total of {ctr} waypoints"
               f" from the SPOT route file '{self.pathGPX}'\n\n")
        log_msg = msg + log_msg
        self.log = log_msg + "\n\n" + self.log
        self.rightPanel.SetValue(self.log + "\n\n")

    # --------------------------------------------------------------------------
    # Event handler to upload a MySQL-query file to the website MySQL DB
    # --------------------------------------------------------------------------
    def onUploadMySQLFile(self, event):
        """ Upload data from a MySQL query to my two websites """

        dlg = wx.ProgressDialog(
            "MySQL Query Upload", "Processing route data....", 100)

        dlg.Update(33)

        msg1 = uploadMySQLfile(self.toernDirectory, False)
        if not msg1:
            msg1 = "\nError in uploadMySQL('ToernDirectoryTable.sql')!\n"
            # print (msg1)
        else:
            msg1 = msg1["Insert"]["msg"]
            # print("\n%s table ToernDirectoryTable.sql" %msg1)

        dlg.Update(67)
        filename = self.filename + self.extension["sql"]
        msg2 = uploadMySQLfile(os.path.join(self.pathSQLite, filename), False)
        if not msg2:
            msg2 = f"\nError in uploadMySQL('{filename}')!\n"
            # print (msg2)
        else:
            msg2 = msg2["Insert"]["msg"]
            # print("\n%s table %s" %(msg2, filename))

        today = datetime.now()
        msg = (
            f"==> today.strftime('%Y-%m-%d  %H:%M:%S')"
            f" upload MySQL file to Website."
            f"\nResults for ToernDirectoryTable.sql: {msg1}"
            f"\nResults for {filename}: {msg2} \n\n")

        if isinstance(dlg, wx.ProgressDialog):
            dlg.Destroy()

        self.log = msg + self.log
        self.rightPanel.SetValue(self.log + "\n\n")

    # --------------------------------------------------------------------------
    # Event handler for Exit this Program
    # --------------------------------------------------------------------------
    def onTimeToExit(self, event):
        """Event handler for the button Close this Program."""

        dlg = wx.MessageDialog(
            None,
            "Do you really want to quit this App?",
            "OK to Quit this App",
            wx.YES_NO | wx.ICON_QUESTION,
        )
        quitApp = False
        if dlg.ShowModal() == wx.ID_YES:
            today = datetime.now()
            l = "\n================================================="
            l1 = (
                l
                + "\nFile Renamer App ended: "
                + today.strftime("%Y/%m/%d at %H:%M:%S ")
            )
            self.log = l1 + l + "\n\n" + self.log
            logfilename = os.path.join(self.cwd, "NavigationTools_log.log")
            try:
                FILE = open(logfilename, "r")
                old_log = FILE.read()
                FILE.close()
            except:
                old_log = ""
            self.log = self.log + old_log
            FILE = open(logfilename, "w")
            FILE.writelines(self.log)
            FILE.close()
            # print("Logfile: %s" %logfilename)
            quitApp = True

        dlg.Destroy()
        if quitApp:
            self.Close()

    # --------------------------------------------------------------------------
    # Event handler for the About Menu item
    # --------------------------------------------------------------------------
    def onHelpAbout(self, event):
        """ Help Dialog """

        # First we create and fill the info object
        year = datetime.now().strftime("%Y")
        info = wx.adv.AboutDialogInfo()
        info.SetName(__app__)
        info.SetVersion(__version__)
        info.SetCopyright(f"(C) 2011-{year} Volker Petersen")
        info.SetDescription(__doc__)
        info.SetWebSite(
            "http://kaiserware.bplaced.net", "Volker Petersen's Sailing Trips"
        )
        info.AddDeveloper(__author__)
        info.SetLicence(__license__)

        # Then we call wx.AboutBox giving it that info object
        wx.adv.AboutBox(info)


# -----------------------------------------------------------------------------------


class MyDialog(wx.Dialog):
    def __init__(self, parent, title):
        super(MyDialog, self).__init__(
            parent,
            title=title,
            size=(280, 50),
            style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT,
        )
        wx.Panel(self, wx.ID_ANY)


# --------------------------------------------------------------------------------------------
# Starting point for this program
# --------------------------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"\nStarting {__app__}")
    print(__doc__)
    try:
        # =======================================================================
        # get the device configuration data. This function is utilized by these scripts
        # 	 RouteConvertUpload.py
        # 	 OpenCPN_Route_Analyzer.py
        # 	 Navigation_Route_Analyzer.pyw
        # returns a dictionary with these keys:
        # {cwd, gpxPath, sqlitePath, LastRoute, skipWP, noSpeed, verbose, error}
        # =======================================================================
        navtools = NavTools()
        settings = navtools.getConfig(verbose=True)
        if settings["error"] is True:
            os.chdir(settings["gpxPath"])
        else:
            raise Exception(
                f"Error reading from configuration file ('{settings['error']}')")
    except:
        print("Error opening the configuration file. Terminating program now.")
        sys.exit(1)

    # launch the WX app
    app = wx.App(redirect=True)
    frame = NavigationTools(settings, navtools)
    app.MainLoop()
