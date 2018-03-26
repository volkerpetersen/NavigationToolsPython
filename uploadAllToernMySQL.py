#!/usr/bin/env python
# -- coding: utf-8 --
#from __future__ import unicode_literals
"""
---------------------------------------------------------------------------
Program to upload all MySQL data files for the TOERN website to the MySQL DB
for the websites at kaiserware.bplaced.net and www.southmerochorale.org/toerns

Developed (c) 2017 by Volker Petersen
---------------------------------------------------------------------------
"""
__date__      = "Sept 17 2017"
__author__    = "Volker Petersen"
__copyright__ = "Copyright (c) 2017 Volker Petersen"
__license__   = "Python 2.7 | GPL http://www.gnu.org/licenses/gpl.txt"
__version__   = "uploadAllToernMySQL.py ver 1.0"

try:
    # import python system modules
    import os
    from uploadMySQL import uploadMySQLfile 
except ImportError as e:
    msg = "Import error: "+str(e)+"\nAborting the program " + __version__
    raise Exception(msg)


def uploadAllSqlFiles(path):
    """
    |------------------------------------------------------------------------------------------
    | function to 
    |
    | @param      - 
    | @ret        -
    |------------------------------------------------------------------------------------------
    """
    fileList = os.listdir(path)
    for fileName in fileList:
        name, extension = os.path.splitext(fileName)
        if "sql" in extension:
            print "ready to upload file %s." %fileName
        else:
            print "skipping file %s '%s'." %(fileName, extension)
    ret = ""    
    #print "\nuploadAllSqlFiles() path: %s" %path
    return ret

"""
|------------------------------------------------------------------------------------------
| main
|------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
    print __doc__
    
    working_directory1 = "D:/My Documents"     # Dell Descktop
    working_directory2 = "D:/VolkerPetersen"   # Dell Laptop
    if (os.path.exists(working_directory1) == True):
         # Home Desktop Dell XPS computer setup parameters
         cwd = working_directory1
    elif (os.path.exists(working_directory2) == True):
         # Volker's laptop computer
         cwd = working_directory2
    else:
        print "\nUnknown computer and root file system.  Terminating now."
        exit(0)

    path = os.path.join(cwd, "Google Drive/ProgramCode/PHP_Projects/toerns/sql_files/")
    
    #print path

    msg = uploadAllSqlFiles(path)

    if (not msg):
        print "\nError in uploadAllSqlFiles(path)!"
    else:    
        print "\nuploadAllSqlFiles(path) return: %s " %msg
    
    print "\nAll Done!"
