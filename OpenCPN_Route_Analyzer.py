#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals
#--------------------------------------------------------------------------------------------
__author__    = "Volker Petersen <volker.petersen01@gmail.com>"
__app__       = "RouteAnalyzer.py"
__version__   = "version 2.3.0, Python 3.7"
__date__      = "Date: 2016/06/15"
__copyright__ = "Copyright (c) 2016 Volker Petersen"
__license__   = "GNU General Public License, published by the Free Software Foundation"
__doc__ = """
-------------------------------------------------------------------------------
   Program parameters:
     'file=yyyyyy':  name of the gpx file to analyze.  If the path/file name
                     contains a space, substitute a "|", eg: 'D:/My|Documents'.
     'route=xxxxxx': name of the route within the gpx file
     'verbose':      run the program in verbose mode (full output)
     'quiet':        run the program in quiet mode
     'noSpeed':      True/False - don't/do compute speed and time between waypoints
     'skipWP':       skip output for all WPs that are marked with label 'empty'

   If no parameters are supplied, this program will use the parameters
   stored in the settings file 'NavConfig.ini' and read by the script 'NavConfig.py'.

   The program will compute the Time, Speed, and Etmals between WPs that contain
   a <desc></desc> tag/field with these entry options:
     arrival 2019-09-25 19:30    (arrival date/time at this WP)
     departure 2019-09-26 09:37  (departure date/time from this WP)
     timedleg 2019-09-26 09:37   (arrival and departure at/from this WP)
     poi                         (Point of Interest on route not being listed)
     homeport                    (designates the Waypoint from which a round-trip
                                  toern originates. Add departure and arrival
                                  times using the above keywords in add'l lines)
-------------------------------------------------------------------------------
"""

try:
    import sys
    import os
    import NavToolsLib as nt

except ImportError as e:
    print("Import error: %s\nAborting the program %s" % (str(e), __version__))
    sys.exit()


def processRoute(name, route, verbose, skipWPsFlag, noSpeed):
    tmp = " Route '" + name + "' Summary "
    print("\n\t%s" % tmp)
    print("\t" + "=" * len(tmp) + "\n")
    nt.ComputeRouteDistances(route.encode("latin-1"), verbose, skipWPsFlag, noSpeed)
    return True

"""
|------------------------------------------------------------------------------------------
| main
|------------------------------------------------------------------------------------------
"""
def main():
    #
    # fetch the supplied program parameters
    #
    verbose = ""
    skipWPsFlag = ""
    routeName = ""
    fileName = ""
    noSpeed = False
    noSpeedTxt = ""

    for val in sys.argv[1:]:
        if (val.find("route=") != -1):
            route = val.split("=")
            routeName = route[1]
        elif (val.find("file=") != -1):
            filen = val.split("=")
            fileName = filen[1].replace("|", " ")
        elif (val.lower() == "verbose"):
            verbose = True
        elif (val.lower() == "quiet"):
            verbose = False
        elif (val.lower() == "nospeed"):
            noSpeed = True
        elif (val.lower() == "skipWP"):
            skipWPsFlag = True

    try:
        #=======================================================================
        # get the device configuration data. This function is utilized by these scripts
        #    RouteConvertUpload.py
        #    OpenCPN_Route_Analyzer.py
        #    Navigation_Route_Analyzer.pyw
        # returns a dictionary with these keys:
        # {cwd, gpxPath, sqlPath, lastGPX, lastRoute, skipWP, noSpeed, verbose, error}
        #=======================================================================
        settings = nt.getNavConfig(verbose=False)
        if (settings['error'] is True):
            cwd = settings['cwd']
            gpxPath = settings['gpxPath']
            sqlPath = settings['sqlPath']
            lastRoute = settings['lastRoute']
            skipWPTxt = settings['skipWP']
            noSpeedTxt = settings['noSpeed']
            verboseTxt = settings['verbose']
        else:
            raise Exception("Error reading from configuration file ('{}')".format(settings['error'])) 

    except Exception as e:
        openCPNroutes = os.getcwd()
        lastRoute = "None"
        verboseTxt = ""
        skipWPTxt = ""
        noSpeedTxt = ""
        print("\nUsing default path and route name. Error:\n'%s'\nreading the config file." % str(e))

    # the program parameters have preference over the settings file parameters
    if (routeName == ""):
        routeName = lastRoute
    if (fileName != ""):
        openCPNroutes = fileName
    if (verbose == ""):
        verbose = (verboseTxt == "verbose")
    if (skipWPsFlag == ""):
        skipWPsFlag = (skipWPTxt == "True")
    if (noSpeed is not False):
        noSpeed = (noSpeedTxt == "True")

    print("OpenCPN routes.: '%s'" %gpxPath)
    print("Route..........: '%s'" %lastRoute)
    print("skip WPs.......: %s" %skipWPsFlag)
    print("compute speed..: %s" %(not noSpeed))

    try:
        routeFlag = False
        path = os.path.join(gpxPath, lastRoute+".gpx")
        try:
            inputfile = open(path, "r")
            route = inputfile.read()
            inputfile.close()
            routeFlag = processRoute(routeName, route, verbose, skipWPsFlag, noSpeed)
        except:
            print("\nThe Route '%s.gpx' is not found in the archived OpenCPN routes files." % routeName)
    
        if (not routeFlag):
            print("\nTerminating program since the route file couldn't be found anywhere.")
    
        print("\nProgram is done.")
    except Exception as e:
        print("\nProgram ended with error: %s\n" % str(e))


"""
|------------------------------------------------------------------------------------------
| program launch point
|------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
    print("\nStarting %s" % __app__)
    print(__doc__)
    main()
