#!/usr/bin/env python
# -- coding: utf-8 --
#from __future__ import unicode_literals
#--------------------------------------------------------------------------------------------
__author__    = "Volker Petersen <volker.petersen01@gmail.com>"
__version__   = "Route_ConverUpload.py (ver 2.1.0)"
__date__      = "Date: 2016/06/15"
__copyright__ = "Copyright (c) 2017 Volker Petersen"
__license__   = "Python 3.6 | GPL http://www.gnu.org/licenses/gpl.txt"
__doc__       = """
-------------------------------------------------------------------------------
   Program parameters:
       no program parameters supported

   This program will use the parameters stored in the settings file
   'OpenCPN_Route_Analyzer_Settings.json'.

   It will convert the 'last route' specified in the json, append a '.gpx'
   to that route name and convert that gpx file to a sql file of the same
   name.  The resulting sql file will be uploaded together with the
   'Toern_Directory.sql' to the southmetrochorale.org and kaiserware.bplaced.net
   mysql databases.

-------------------------------------------------------------------------------
"""

try:
    import sys, os, inspect
    from datetime import datetime
    from Navigation_Route_Parser import read_json, parseSQLRouteFile
    from uploadMySQL import uploadMySQLfile

except ImportError as e:
    print("Import error: %s \nAborting the program" %(e, __version__))
    sys.exit()

"""
|------------------------------------------------------------------------------------------
| main
|------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
    print("\nStarting %s" %__version__)
    print(__doc__)

    # configuration data
    supported_devices = {'Desktop': ["D:\VolkerPetersen", "D:\My Documents\Google Drive"],
                           'Laptop': ["D:\VolkerPetersen","D:\VolkerPetersen\Google Drive"]}

    # fetch the content from the default settings file
    cwd = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    cwd = os.path.normpath(cwd)
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
            if (os.path.exists(supported_devices[device][1])):
                path = path.replace("D:\VolkerPetersen\Google Drive", supported_devices[device][1])
                root = supported_devices[device][0]
                unsupported_device = False
        if (unsupported_device):
            msg = "Unknown computer and root file system"
            raise Exception(msg)

    except Exception as e1:
        print("\nTerminating now due to error:\n'%s'\nreading the config file." %str(e1))
        sys.exit(1)

    try:
        pathGPX = os.path.normpath(os.path.join(root, "Google Drive/Sailing/OpenCPN_Routes/"))
        filename = lastRoute+'.gpx'

        old = "Python_Projects/NavigationTools".replace("/", os.path.sep)
        new = "PHP_Projects/Toerns/sql_files".replace("/", os.path.sep)
        pathSQL = cwd.replace(old, new)

        #print(filename)
        #print(old, " | ", new)
        #print(pathGPX)
        #print(pathSQL)

        flag = True
        temp = os.path.join(pathSQL, filename.replace(".gpx", ".sql"))
        print(temp, os.path.isfile(temp))
        if (os.path.isfile(temp)):
            print("\nThe route '%s' has already been parsed into the SQL file '%s'."
                  %(lastRoute, temp))
            c = input("Do you want to replace it ('r') or skip ('s' or <Enter>) it? ")
            if not (c is 'r' or c is 'R'):
                flag = False

        if (flag):
            log = parseSQLRouteFile(pathGPX, pathSQL, filename)
        else:
            log = "==> Skipped parsing the route '%s'" %lastRoute
        # end of if-statement

        #print(log)
        filename = filename.replace(".gpx", ".sql")
        #print(filename)

        log_msg = ""
        msg1 = uploadMySQLfile(os.path.join(pathSQL, "ToernDirectoryTable.sql"), False)

        if "Error code" in msg1:
            msg1 = "\nError in uploadMySQL('ToernDirectoryTable.sql')!\n"
            print(msg1)
        else:
            if msg1['bplaced']['Truncate']['status'] == "success" \
                and msg1['bplaced']['Insert']['status'] == "success" \
                and msg1['Hostmonster']['Truncate']['status'] == "success" \
                and msg1['Hostmonster']['Insert']['status'] == "success":
                    msg1 = msg1['bplaced']['Insert']['msg']
            #print "\n%s table ToernDirectoryTable.sql" %msg1


        msg2 = uploadMySQLfile(os.path.join(pathSQL, filename), False)
        if "Error code" in msg2:
                msg2 = "\nError in uploadMySQL('%s')!\n" %filename
                print(msg2)
        else:
            if msg2['bplaced']['Truncate']['status'] == "success" \
                and msg2['bplaced']['Insert']['status'] == "success" \
                and msg2['Hostmonster']['Truncate']['status'] == "success" \
                and msg2['Hostmonster']['Insert']['status'] == "success":
                    msg2 = msg2['bplaced']['Insert']['msg']
        #print "\n%s table %s" %(msg1, filename)

        today = datetime.now()
        msg = "==> "+today.strftime("%Y-%m-%d  %H:%M:%S ") + " upload MySQL file to Website."
        msg = msg + "\nResults for ToernDirectoryTable.sql: %s"
        msg = msg + "\nResults for %s: %s"
        msg = msg %(msg1, filename, msg2)
        log_msg = msg + log_msg

        print(log_msg)

        print("\nProgram is done.")
    except Exception as e2:
        print("\nProgram ended with error: %s\n" %str(e2))

