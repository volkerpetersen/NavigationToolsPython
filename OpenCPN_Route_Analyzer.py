#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals
#--------------------------------------------------------------------------------------------
__author__ = "Volker Petersen <volker.petersen01@gmail.com>"
__version__ = "OpenCPN_Route_Analyzer.py (ver 2.1.0)"
__date__ = "Date: 2016/06/15"
__copyright__ = "Copyright (c) 2016 Volker Petersen"
__license__ = "Python 2.7 | GPL http://www.gnu.org/licenses/gpl.txt"
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
   stored in the settings file 'OpenCPN_Route_Analyzer.json'.

   If the WPs are named in the datetime format 'yyyy_mm_dd_HHMM' this
   program will also compute the Time, Speed, and Etmals between such WPs.
-------------------------------------------------------------------------------
"""

try:
    import sys
    import os
    import inspect
    from bs4 import BeautifulSoup
    from Navigation_Route_Parser import ComputeRouteDistances, read_json

except ImportError as e:
    print("Import error: %s\nAborting the program %s" % (str(e), __version__))
    sys.exit()

"""
|------------------------------------------------------------------------------------------
| main
|------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
    print("\nStarting %s" % __version__)
    print(__doc__)
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

    # configuration data
    supported_devices = {"My Documents", "VolkerPetersen"}
    #                     Dell Desktop    Dell Laptop

    # fetch the content from the default settings file
    cwd = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    default_settings = os.path.join(cwd, 'OpenCPN_Route_Analyzer_Settings.json')
    try:
        settings = read_json(default_settings)
        path = settings['lastGPX']
        lastRoute = settings['lastRoute']
        verboseTxt = settings['verbose']
        skipWPTxt = settings['skipWP']
        noSpeedTxt = settings['noSpeed']
        unsupported_device = True
        for device in supported_devices:
            if (device in cwd):
                path = path.replace("VolkerPetersen", device)
                unsupported_device = False
        if (unsupported_device):
            print("\nUnknown computer and root file system.  Terminating now.\n")
            sys.exit()

    except Exception as e:
        path = os.getcwd()
        lastRoute = "None"
        verboseTxt = ""
        skipWPTxt = ""
        noSpeedTxt = ""
        print("\nUsing default path and route name.  Error:\n'%s'\nreading the config file." % str(e))

    # the program parameters have preference over the settings file parameters
    if (routeName == ""):
        routeName = lastRoute
    if (fileName != ""):
        path = fileName
    if (verbose == ""):
        verbose = (verboseTxt == "verbose")
    if (skipWPsFlag == ""):
        skipWPsFlag = (skipWPTxt == "True")
    if (noSpeed is not False):
        noSpeed = (noSpeedTxt == "True")
    if (path == ""):
        path = "C:\\ProgramData\\opencpn\\navobj.xml"

    #
    # test parameters
    #
    #routeName = "2012 Atlantic Crossing"
    #path = "D:\\VolkerPetersen\\Google Drive\\Sailing\\OpenCPN_Routes\\2012_06_AtlanticCrossing.gpx"

    # routeName="2017_08_TransSuperiorRace"
    #path = "D:\\VolkerPetersen\\Google Drive\\Sailing\\OpenCPN_Routes\\2017_08_TransSuperiorRace.gpx"
    #noSpeed = False
    #
    # end of test parameters
    #

    # read the route file and find the various routes stored in it.  If a
    # route matches the routName, pass the data to the ComputeRouteDistance
    # method to compute the distances between the WP in that route
    try:
        inputfile = open(path, "r")
        xml = inputfile.read()
        inputfile.close()

        soup = BeautifulSoup(xml, "xml")
        routeFlag = False
        routes = soup.find_all('rte')
        for route in routes:
            if (routeName in route.find('name').text):
                tmp = " Route '" + route.find('name').text + "' Summary "
                print("\t%s" % tmp)
                print("\t" + "=" * len(tmp) + "\n")
                routeFlag = True
                ComputeRouteDistances(route.encode("latin-1"), verbose, skipWPsFlag, noSpeed)

        print("\nReading data from file '%s'\n" % path)
        if (not routeFlag):
            print("The Route '%s' is not found in the above route file." % routeName)
        print("\nProgram is done.")
    except Exception as e:
        print("\nProgram ended with error: %s\n" % str(e))
