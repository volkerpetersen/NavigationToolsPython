#!/usr/bin/env python
# -- coding: utf-8 --
# -----------------------------------------------------------------------------
"""
    script to convert MySQL query files to SQLite queries
"""
__author__ = "Volker Petersen"
__version__ = "SQLIte_converter.py 2.0.0"
__date__ = "Date: 2022/01/02"
__copyright__ = "Copyright (c) 2022 Volker Petersen"
__license__ = "Python 3.8.5 | GPL http://www.gnu.org/licenses/gpl.txt"
__doc__ = """
script to convert MySQL query files to SQLite queries
"""
navtools = None
try:
    import os
    import sys
    from NavToolsLib import NavTools
except ImportError as e:
    print("Import error: '%s' - %s\nAborting the program" %
          (str(e), __version__))
    quit(1)


header = """-- phpMyAdmin SQL Dump
-- version 3.3.9
-- http://www.phpmyadmin.net

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

-- Database: `map`"""

id = "`id` int(11) DEFAULT NULL,"
lat = "`lat` text,"
lon = "`lon` text,"
end = """`notes` VARCHAR(80) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;"""


def convert_sql_query(inputFile, outputFile):
    if "_Backup" in inputFile:
        print("skipped file")
    elif "ToernDirectoryTable" in inputFile:
        #print("Directory %s" %inputFile)
        pass
    else:
        #print("Route %s" %inputFile)
        with open(inputFile, 'r') as file:
            query = file.read()

        query = query.replace(header, "")
        text = '"id" INTEGER,'
        query = query.replace(id, text)
        text = '"lat" REAL,'
        query = query.replace(lat, text)
        text = '"lon" REAL,'
        query = query.replace(lon, text)
        text = '"notes" TEXT, PRIMARY KEY("id"));'
        query = query.replace(end, text)
        query = query.replace("`", '"')
        query = query.replace("text", 'TEXT')
        query = query.replace("TRUNCATE", 'DELETE FROM')

        with open(outputFile, 'w') as file:
            file.write(query)

    return


if __name__ == "__main__":
    """---------------------------------------------------------------------
        Script starting point
    """
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    rootPath = os.path.dirname(scriptPath)

    print("\nStarting %s\n%s" % (__version__, __doc__))

    navtools = NavTools()
    settings = navtools.getConfig()
    sqlPath = settings['sqlPath']
    sqlitePath = settings['sqlitePath']

    print("\nSQL path:....'%s'" % sqlPath)
    print("\nSQLite path:.'%s'" % sqlitePath)
    print("\nSQLite DB:...'%s'" % settings['sqliteDB'])

    for file in os.listdir(sqlPath):
        if file.endswith(".sql"):
            inputFile = os.path.join(sqlPath, file)
            outputFile = os.path.join(sqlitePath, file)
            convert_sql_query(inputFile, outputFile)
