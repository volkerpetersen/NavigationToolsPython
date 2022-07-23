#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals
# --------------------------------------------------------------------------------------------
__author__ = "Volker Petersen <volker.petersen01@gmail.com>"
__app__ = "RouteAnalyzer.py"
__version__ = "version 2.3.0, Python 3.7"
__date__ = "Date: 2016/06/15"
__copyright__ = "Copyright (c) 2016 Volker Petersen"
__license__ = "GNU General Public License, published by the Free Software Foundation"
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
navtools = None

try:
    import sys
    import os
    import argparse
    from NavToolsLib import NavTools

except ImportError as e:
    print(f"Import error: {str(e)}\nAborting the program {__version__}")
    sys.exit()


def processRoute(name, route, verbose, skipWPsFlag, noSpeed):
    tmp = " Route '" + name + "' Summary "
    print(f"\n\t{tmp}")
    print(f"\t" + "=" * len(tmp) + "\n")
    msg = navtools.ComputeRouteDistances(route.encode("latin-1"),
                                         verbose, skipWPsFlag, noSpeed)
    print(msg)


"""
|------------------------------------------------------------------------------------------
| program launch point
|------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
    print(f"\nStarting {__app__}")
    print(__doc__)

    #
    # fetch the supplied program parameters
    #
    verbose = True
    skipWPsFlag = False
    routeName = ""
    fileName = ""
    noSpeed = False
    noSpeedTxt = ""

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="run in verbose mode",
                        default=False, action="store_true")
    parser.add_argument("-n", "--noSpeed", help="don't compute speed along the route",
                        default=False, action="store_true")
    parser.add_argument("-s", "--skipWP", help="skip Waypoints",
                        default=False, action="store_true")
    parser.add_argument("-file", help="route file name",
                        type=str, default="")
    parser.add_argument("-route", help="route name",
                        type=str, default="")

    args = parser.parse_args()

    try:
        # =======================================================================
        # get the device configuration data. This function is utilized by these scripts
        #    RouteConvertUpload.py
        #    OpenCPN_Route_Analyzer.py
        #    Navigation_Route_Analyzer.pyw
        # returns a dictionary with these keys:
        # {cwd, gpxPath, sqlPath, lastGPX, lastRoute, skipWP, noSpeed, verbose, error}
        # =======================================================================
        navtools = NavTools()
        settings = navtools.getConfig(verbose=False)
        if (settings['error'] is True):
            cwd = settings['cwd']
            gpxPath = settings['gpxPath']
            sqlPath = settings['sqlitePath']
            lastRoute = settings['lastRoute']
            skipWPTxt = settings['skipWP']
            noSpeedTxt = settings['noSpeed']
            verboseTxt = settings['verbose']
        else:
            raise Exception(
                f"Error reading from configuration file ('{settings['error']}')")

    except Exception as e:
        lastRoute = "None"
        verboseTxt = ""
        skipWPTxt = ""
        noSpeedTxt = ""
        print(
            f"\nUsing default path and route name. Error:\n'{str(e)}'\nreading the config file.")

    print(args.verbose)

    # the program parameters have preference over the settings file parameters
    if args.verbose:
        verbose = args.verbose
    else:
        verbose = (verboseTxt == "verbose")
    if args.noSpeed:
        noSpeed = args.noSpeed
    else:
        noSpeed = (noSpeedTxt == "True")
    if args.skipWP:
        skipWPsFlag = args.skipWP
    else:
        skipWPsFlag = (skipWPTxt == "True")
    if args.route != "":
        routeName = args.route
    else:
        routeName = lastRoute
    if args.file != "":
        openCPNroutes = args.file
    else:
        openCPNroutes = fileName

    print(f"OpenCPN routes.: '{gpxPath}'")
    print(f"Route..........: '{lastRoute}'")
    print(f"skip WPs.......: {skipWPsFlag}")
    print(f"compute speed..: {(not noSpeed)}")
    print(f"verbose........: {(verbose)}")

    try:
        path = os.path.join(gpxPath, lastRoute+".gpx")
        inputfile = open(path, "r")
        route = inputfile.read()
        inputfile.close()
    except:
        print(
            f"\nThe Route '{routeName}.gpx' is not found in the archived OpenCPN routes files.")

    processRoute(
        routeName, route, verbose, skipWPsFlag, noSpeed)

    print("\nProgram is done.")
