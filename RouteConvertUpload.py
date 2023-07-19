
#!/usr/bin/env python
# -- coding: utf-8 --
# from __future__ import unicode_literals
# --------------------------------------------------------------------------------------------
__author__ = "Volker Petersen <volker.petersen01@gmail.com>"
__app__ = "RouteConvertUpload.py"
__version__ = "version 2.1.0, Python 3.7"
__date__ = "Date: 2016/06/15"
__copyright__ = "Copyright (c) 2017 Volker Petersen"
__license__ = "GNU General Public License, published by the Free Software Foundation"
__doc__ = """
-------------------------------------------------------------------------------
   Program parameters:
     route=name of the route to upload to the MYSQL database
     fixRouteDates fixes the dates/time of all routes (when empty)
	               or only for specified route if fixRouteDates=name

   This program will use the parameters stored in the settings file
   'NavConfig.ini' and read by the script 'NavConfig.py'.

   It will convert the 'last route' specified in the json, append a '.gpx'
   to that route name and convert that gpx file to a sql file of the same
   name.  The resulting sql file will be uploaded together with the
   'Toern_Directory.sql' to the southmetrochorale.org and kaiserware.bplaced.net
   mysql databases.

-------------------------------------------------------------------------------
"""
navtools = None

try:
    import sys
    import os
    from datetime import datetime, timedelta
    from shutil import copyfile
    from bs4 import BeautifulSoup
    from NavToolsLib import NavTools
    from uploadSQLquery import uploadMySQLfile, upload_to_mysql_via_php, upload_to_mysql

except ImportError as e:
    print("Import error: %s \nAborting the program %s" % (e, __version__))
    sys.exit()


def fixRouteDates(fileName, pathSQL, maptable, fixStartDate=True, verbose=False):
    """--------------------------------------------------------------------------
        fixRouteDates adjusts the <time> entries in specified gpx files.  The first
        harbor WP must contain the actual start date of the trip. The following
        WP <time> entries will be computed from the start time plus distance/5kts
        the first WP after the a harbor/anchorage/mooring WP will start next day
        at 9am local time
    Args:
        fileName (string):    xml file
        pathSQL (string):     path to the SQL file(s)
        maptable (string):    file name for the maptable
        fixStartDate (bool):  fix the start route date when True
        verbose (bool):       print function results

    Returns:
        none
    """

    speed = 5.0  # average speed utilized to compute time between waypoints
    dateFormat = "%Y-%m-%dT%H:%M:%SZ"
    layover = {			# dictionary with the names of route layovers
        'harbor': 1,
        'service-marina': 2,
        'anchorage': 3,
        'mooring': 4,
        'mooring bouy': 5,
    }

    try:
        backupFile = fileName.replace(".gpx", "_old.gpx")
        if not os.path.isfile(backupFile):
            copyfile(fileName, backupFile)

        inputfile = open(fileName, "r")
        xml = inputfile.read()
        inputfile.close
    except:
        print("Error opening file: %s" % fileName)
        return

    soup = BeautifulSoup(xml)
    wps = soup.find_all('rtept')
    lastHarbor = ""
    startDate = ""
    endDate = ""
    startHour = 8
    legStart = 0
    lastLAT = 0
    lastLON = 0
    distance = 0
    flag = False
    for wp in wps:
        lat = float(wp['lat'])
        lon = float(wp['lon'])
        name = wp.find('name').text
        time = wp.find('time').text
        symbol = (wp.find('sym').text).lower()

        if flag:
            time = legStart.strftime(dateFormat)

        if isinstance(legStart, datetime):
            if lastLAT != 0:
                distance = navtools.calc_distance(lastLAT, lastLON, lat, lon)
            else:
                distance = 0
            elapsedTime = distance / speed		# time in hrs
            arrivalTime = legStart + timedelta(hours=elapsedTime)
            wp.find('time').string = arrivalTime.strftime(dateFormat)
            # print("at %s %s distance %.2f" %(name, arrivalTime.strftime("%m/%d %H:%M:S"), distance))
        if (lastHarbor != "") and (not isinstance(legStart, datetime)):
            print("invalid time format ('%s') at WP '%s'. Skipping WP" %
                  (time, name))

        if "diamond" in symbol or "empty" in symbol:
            wp.find('sym').string = symbol.title()

        if symbol in layover:
            if symbol == 'harbor':
                wp.find('sym').string = 'Service-Marina'
                print("Updated %s to %s." % (name, wp.find('sym').text))

            distance = 0
            lastLAT = lat
            lastLON = lon
            if lastHarbor == "":
                if verbose:
                    print('departed from: %s at %s' % (name, time))
                newDate = True
                while newDate and fixStartDate:
                    c = input(
                        "Update departure time, skip route ('s') or accept current time (<Enter>): ")
                    if not c:
                        newDate = False
                    elif c == 's':
                        return
                    else:
                        test = datetime.strptime(c, dateFormat)
                        if isinstance(test, datetime):
                            newDate = False
                            time = c
                            wp.find('time').string = time
                        else:
                            if verbose:
                                print("invalid date/time: '%s'" % c)

                lastHarbor = name
                legStart = datetime.strptime(time, dateFormat)
                startHour = legStart.hour
                startDate = datetime.strptime(
                    time, dateFormat).strftime("%Y/%m/%d")
                if verbose:
                    print("set start hour to %d UTC" % startHour)
            else:
                if verbose:
                    print('arrived at:    %s at %s' %
                          (name, arrivalTime.strftime('%Y-%m-%d %H:%M')))
                legStart = arrivalTime + timedelta(days=1)
                legStart = legStart.replace(hour=startHour)
                legStart = legStart.replace(minute=0)
                legStart = legStart.replace(second=0)
                endDate = arrivalTime.strftime("%Y/%m/%d")
                flag = True

    xml = str(soup)
    inputfile = open(fileName, "w")
    inputfile.write(xml)
    inputfile.close()

    if verbose:
        print("Updating 'ToernDirectoryTable.sql' with start (%s) and end dates (%s)" % (
            startDate, endDate))
    inputfile = open(os.path.join(pathSQL, "ToernDirectoryTable.sql"), 'r')
    xml = inputfile.read()
    inputfile.close()

    maptable = maptable.replace(".gpx", "")
    query = "Update ToernDirectoryTable SET `startDate`='" + \
        startDate+"', `endDate`='"+endDate
    query += "' WHERE `maptable`='"+maptable+"' LIMIT 1;"
    # print(query)
    bplaced = upload_to_mysql_via_php("bplaced", query)
    a2hosting = upload_to_mysql("a2hosting", query)
    if bplaced['status'] != "success":
        print("Error updating bplaced:   '%s'" % bplaced['msg'])
    if a2hosting['status'] != "success":
        print("Error updating a2hosting: '%s'" % a2hosting['msg'])


def fixAllRouteDates(pathGPX, pathSQL):
    """--------------------------------------------------------------------------
        fix all Route Dates
    Args:
        pathGPX (string): path to the GPX file(s)
        pathSQL (string): path to the SQL file(s)

    Returns:
        none
    """
    excludeList = {		# don't work on the files in this dictionary
        '2012_AtlanticCrossing.gpx': 1,
        '2013_03_Miami_Annapolis.gpx': 2,
        '2013_04_Cabo_LA.gpx': 3,
        '2013_05_SJD_KingHarbor.gpx': 4,
        '2013_07_Hawaii_LA.gpx': 5,
        '2014_11_Irvington_Beaufort.gpx': 6,
        '2016_06_Jacksonville_Bermuda.gpx': 7,
        '2016_06_Jacksonville_France.gpx': 8,
        '2017_05_LA_SanJuanIslands.gpx': 9,
        '2013_03_Miami_Annapolis_GulfStream.gpx': 10,
        '2013_03_Miami_Annapolis_Shortest.gpx': 11,
        '2017_08_TransSuperiorRace': 12
    }

    fileList = os.listdir(pathGPX)
    for fileName in fileList:
        if not (fileName in excludeList) and (".gpx" in fileName) and not ("_old" in fileName):
            print("\nworking on '%s'" % fileName)
            fixRouteDates(os.path.join(pathGPX, fileName), pathSQL,
                          fileName, fixStartDate=False, verbose=False)


"""
|------------------------------------------------------------------------------------------
| main
|------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
    print("\nStarting %s" % __app__)
    print(__doc__)

    try:
        # =======================================================================
        # get the device configuration data. This function is utilized by these scripts
        #	RouteConvertUpload.py
        #	OpenCPN_Route_Analyzer.py
        #	Navigation_Route_Analyzer.pyw
        # returns a dictionary with these keys:
        # {cwd, gpxPath, sqlPath, lastGPX, lastRoute, skipWP, noSpeed, verbose, error}
        # =======================================================================
        navtools = NavTools()
        settings = navtools.getConfig(verbose=False)
        if (settings['error'] is True):
            cwd = settings['cwd']
            pathGPX = settings['gpxPath']
            pathSQL = settings['sqlPath']
            lastRoute = settings['lastRoute']
            skipWPTxt = settings['skipWP']
            noSpeedTxt = settings['noSpeed']
            verboseTxt = settings['verbose']
        else:
            raise Exception(
                "Error reading from configuration file ('{}')".format(settings['error']))

        print("GPX files......: '%s'" % pathGPX)
        print("SQL files......: '%s'" % pathSQL)
        print("skip WPs.......: %s" % skipWPTxt)
        # print("OpenCPN Routes.: '%s'" %lastRoutes)
        print("OpenCPN Route..: '%s'" % lastRoute)

    except Exception as e1:
        print("\nTerminating now due to error:\n'%s'\nreading the config file." % str(e1))
        sys.exit(1)

    # overwrite the lastRoute value is we have a program parameter input
    for val in sys.argv[1:]:
        if (val.find("route=") != -1):
            lastRoute = val.split("=")[1]

        if (val.find("fixRouteDates") != -1):
            if (val.find("fixRouteDates=") != -1):
                fileName = val.split("=")[1]
                print("working on '%s'" % fileName)
                fixRouteDates(os.path.join(pathGPX, fileName), pathSQL,
                              fileName, fixStartDate=False, verbose=True)
            else:
                fixAllRouteDates(pathGPX, pathSQL)
            print("\nProgram is done.")
            sys.exit(1)

    # provide option to work on another SQL route file
    c = input(
        "Do you want to parse another SQL route file instead ('y' / 'n' or <Enter>)? ")
    if (c == 'y' or c == 'Y'):
        lastRoute = input(
            "Please enter the SQL route file name (w/o extension): ")
        print("New Route......: '%s'" % lastRoute)
        c = input("Do you want to update the Config file ('y' / 'n' or <Enter>)? ")
        if (c == 'y' or c == 'Y'):
            navtools.saveConfig(lastRoute)

    try:
        flag = True
        if (os.path.isfile(os.path.join(pathSQL, lastRoute+'.sql'))):
            print("\nThe route '%s' has already been parsed into the SQL file '%s'."
                  % (lastRoute, os.path.join(pathSQL, lastRoute+'.sql')))
            c = input(
                "Do you want to replace it ('r') or skip ('s' or <Enter>) it? ")
            if not (c == 'r' or c == 'R'):
                flag = False

        if (flag):
            log = navtools.parseSQLRouteFile(
                pathGPX, pathSQL, lastRoute+'.gpx')
        else:
            log = "==> Skipped parsing the route '%s'" % lastRoute
        # end of if-statement

        log_msg = ""
        msg1 = uploadMySQLfile(os.path.join(
            pathSQL, "ToernDirectoryTable.sql"), False)

        if "Error code" in msg1:
            msg1 = "\nError in uploadMySQL('ToernDirectoryTable.sql')!\n"
            print(msg1)
        else:
            if msg1['bplaced']['Truncate']['status'] == "success" \
                    and msg1['bplaced']['Insert']['status'] == "success" \
                    and msg1['Hostmonster']['Truncate']['status'] == "success" \
                    and msg1['Hostmonster']['Insert']['status'] == "success":
                msg1 = msg1['bplaced']['Insert']['msg']
            # print "\n%s table ToernDirectoryTable.sql" %msg1

        msg2 = uploadMySQLfile(os.path.join(pathSQL, lastRoute+'.sql'), False)
        if "Error code" in msg2:
            msg2 = "\nError in uploadMySQL('%s')!\n" % (lastRoute+'.sql')
            print(msg2)
        else:
            if msg2['bplaced']['Truncate']['status'] == "success" \
                    and msg2['bplaced']['Insert']['status'] == "success" \
                    and msg2['Hostmonster']['Truncate']['status'] == "success" \
                    and msg2['Hostmonster']['Insert']['status'] == "success":
                msg2 = msg2['bplaced']['Insert']['msg']

        today = datetime.now()
        msg = "==> "+today.strftime("%Y-%m-%d  %H:%M:%S ") + \
            " upload MySQL file to Website."
        msg = msg + "\nResults for ToernDirectoryTable.sql: %s"
        msg = msg + "\nResults for %s: %s"
        msg = msg % (msg1, (lastRoute+'.sql'), msg2)
        log_msg = msg + log_msg

        print(log_msg)

        print("\nProgram is done.")
    except Exception as e2:
        print("\nProgram ended with error: %s\n" % str(e2))
