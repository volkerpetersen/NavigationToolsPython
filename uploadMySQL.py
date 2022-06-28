#!/usr/bin/env python
# -- coding: utf-8 --
# from __future__ import unicode_literals
__doc__ = """
---------------------------------------------------------------------------
Program to upload MySQL data to the MySQL DB for the websites at
kaiserware.bplaced.net and www.southmerochorale.org/toerns

Developed (c) 2017 by Volker Petersen
---------------------------------------------------------------------------
"""
__date__ = "Jul 17 2017"
__author__ = "Volker Petersen"
__copyright__ = "Copyright (c) 2017 Volker Petersen"
__license__ = "GNU General Public License, published by the Free Software Foundation"
__version__ = "version 1.5, Python 3.7"
__app__ = "uploadMySQL.py"

navtools = None
try:
    # import python system modules
    import os
    import ast
    import sys
    import pymysql.cursors
    import urllib.request
    import urllib.error
    import urllib.parse
    import warnings
    import sqlite3
    import ftplib
    from NavToolsLib import NavTools

    warnings.filterwarnings("ignore")
except ImportError as e:
    msg = "Import error: " + str(e) + "\nAborting the program " + __version__
    raise Exception(msg)

# %%


def upload_to_sqlite(DBfile, query):
    """
    |------------------------------------------------------------------------------------------
    | function to execute queries in the sqlite DB 'toernsDB.sqlite' 
    |
    | @param      - DBfile path/filename of the SQLite DB
    | @param      - query string with the MySQL query to be executes
    | @ret        - # of records if successful or False if connection or query failed
    |------------------------------------------------------------------------------------------
    """

    try:
        db = sqlite3.connect(DBfile)
        cursor = db.cursor()
        cursor.execute(query)
        rec = cursor.rowcount
        db.commit()
        db.close()

        msg = "Updated %s records in the SQlite DB using Python." % rec
        ret = {"msg": msg, "status": "success"}

    except Exception as e:
        msg = "Error accessing the SQLite DB '%s':\n%s." % (DBfile, str(e))
        ret = {"msg": msg, "status": "failure"}

    return ret


def upload_to_mysql(host, query):
    """
    |------------------------------------------------------------------------------------------
    | function to connect to the mysql DB 'map' at A2 Hosting SouthMetroChorale
    | and execute the query
    |
    | this function doesn't work for the bplaced site since it doesn't allow external
    | access to the MySQL DB.  We're now using the upload_to_mysql_via_php() for the
    | kaiserware.bplaced.net site and upload_to_mysql() for A2 Hosting.
    |
    | @param      - website host
    | @param      - query string with the MySQL query to be executes
    | @ret        - # of records if successful or False if connection or query failed
    |------------------------------------------------------------------------------------------
    """

    # print("\na2hosting in '%s' = %d" %(host.lower(),  ("a2hosting" in host.lower())))
    if "a2hosting" in host.lower():
        db_host = "a2ss54.a2hosting.com"
        db_user = "southme1_sudo"
        db_pass = "Vesret7713"
        db_name = "southme1_map"
    else:
        # bplaced.net doesn't allow external access to MySQL DB
        msg = "MySQL DB connection on host '%s' not implemented!" % host
        msg += " Error code: authentication error"
        ret = {"msg": msg, "status": "failure"}
        return ret
    try:
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            db=db_name,
            cursorclass=pymysql.cursors.DictCursor,
        )
        # print ("Connected to MySQL DB '%s' on host '%s' (%s)" %(db_name, host, db_host))
    except Exception as e:
        msg = "Failed to connect to DB '%s' on host '%s' (%s)" % (
            db_name,
            host,
            db_host,
        )
        msg += " Error code: %s." % str(e)
        ret = {"msg": msg, "status": "failure"}
        return ret

    try:
        with connection.cursor() as cursor:
            rec = cursor.execute(query)
        connection.commit()
        # print ("%s record(s) updated using the query:\n '%s'\n" %(rec, query))
        connection.close()
    except Exception as f:
        msg = "Failed to execute the query:\n '%s'.\n" % query
        msg += " Error code: %s." % str(f)
        ret = {"msg": msg, "status": "failure"}
        return ret

    msg = "Updated %s records in the MySQL DB using Python." % rec
    ret = {"msg": msg, "status": "success"}
    return ret


# %%
def upload_to_mysql_via_php(host, query):
    """
    |------------------------------------------------------------------------------------------
    | function to execute the MySQL query 'query' at the website 'host'
    | using a php script at that site.  The query is packaged as json.

    | Since the bplaced site doesn't allow external access to the MySQL DB,
    | we're using the upload_to_mysql_via_php() for the kaiserware.bplaced.net
    | site.
    |
    | @param      - website host
    | @param      - query string with the MySQL query to be executes
    | @ret        - # of records if successful or False if connection or query failed
    |------------------------------------------------------------------------------------------
    """
    if "bplaced" in host.lower():
        db_host = "http://kaiserware.bplaced.net/update_mysql.php"
        db_pass = "vesret2204"
    elif "a2hosting" in host.lower():
        db_host = "https://www.southmetrochorale.org/toerns/update_mysql.php"
        db_pass = "Vesret7713"
    else:
        msg = "MySQL DB connection on host '%s' not implemented!" % host
        print("\n%s" % msg)
        ret = {"msg": msg, "status": "failure"}
        return ret

    values = {"pw": db_pass, "query": query}
    try:
        data = urllib.parse.urlencode(values).encode("utf-8")
        req = urllib.request.Request(db_host, data)
        response = urllib.request.urlopen(req)
        ret = response.read().decode("utf-8")
        ret = ast.literal_eval(ret)  # convert the string to dictionary
    except urllib.error.HTTPError as e:
        msg = "The server could not fulfill the request."
        msg += " Error code: %s" % str(e.code)
        print(msg)
        ret = {"msg": msg, "status": "failure"}
    except urllib.error.URLError as e:
        msg = "We failed to reach a server."
        msg += " Error code: %s" % str(e.reason)
        print(msg)
        ret = {"msg": msg, "status": "failure"}
    except Exception as e:
        msg = "We encountered an undefined urllib error."
        msg += " Error code: %s" % str(e)
        print(msg)
        ret = {"msg": msg, "status": "failure"}

    return ret


def uploadMySQLfile(sql_file, verbose=True):
    FTP_HOST = "kaiserware.bplaced.net"
    FTP_USER = "kaiserware"
    FTP_PW = "vesret2204"
    settings = navtools.getConfig()

    if("sqlite_files\\ToernDirectoryTable.sql" in sql_file):
        sqliteFile = os.path.normpath(settings['toernDirectory'])
    else:
        sqliteFile = os.path.normpath(sql_file.replace("gpx", "sql"))

    if verbose:
        print("uploadMySQLFile sqlite:.'%s'" % sqliteFile)

    try:
        with open(sqliteFile, "r") as file:
            sqliteCreate = ""
            sqliteTruncate = ""
            sqliteInsert = ""
            for line in file:
                line = line.replace("\t", "")
                line = line.replace("\n", "")
                line = line.replace("\\", "")
                if (
                    ("CREATE TABLE" in line or sqliteCreate != "")
                    and (sqliteTruncate == "")
                    and (sqliteInsert == "")
                    and ("DELETE FROM" not in line)
                    and ("INSERT INTO" not in line)
                    and ("--" not in line)
                ):
                    sqliteCreate += line
                if ("DELETE FROM" in line):
                    sqliteTruncate = line
                if (
                    ("INSERT INTO" in line or sqliteInsert != "")
                    and ("CREATE TABLE" not in line)
                    and ("--" not in line)
                ):
                    sqliteInsert += line

    except IOError as e:
        print(
            "\nUnable to open the sql query file '%s' (error: '%s').  Terminating now." % (
                sql_file, e.strerror)
        )
        return False

    except:
        print("Unexpected Error: '%s'" % (sys.exc_info()[0]))
        return False

    # print ("\nCreate: ",sqliteCreate)
    # print ("\nTruncate: ",sqliteTruncate)
    # print ("\nInsert: ",sqliteInsert)

    if sqliteInsert == "":
        print(
            "\nUnable to extract the sql query from the file '%s'.  Terminating now."
            % sql_file
        )
        return False

    ret = {}

    r = upload_to_sqlite(settings["sqliteDB"], sqliteCreate)
    ret["Create"] = r

    r = upload_to_sqlite(settings["sqliteDB"], sqliteTruncate)
    ret["Truncate"] = r

    r = upload_to_sqlite(settings["sqliteDB"], sqliteInsert)
    ret["Insert"] = r

    return ret


def FTPupload():
    FTP_HOST = "kaiserware.bplaced.net"
    FTP_USER = "kaiserware"
    FTP_PW = "vesret2204"
    settings = navtools.getConfig()

    ftp_server = ftplib.FTP(FTP_HOST, FTP_USER, FTP_PW)
    ftp_server.cwd("www")
    fh_sqlite = open(settings["sqliteDB"], 'rb')
    filename = os.path.basename(settings["sqliteDB"])
    ret = ftp_server.storbinary('STOR %s' % filename, fh_sqlite)
    ftp_server.close()

    return ret


# %%
"""
|------------------------------------------------------------------------------------------
| main
|------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
    print("\nStarting %s" % __app__)
    print(__doc__)

    # load configuration data
    navtools = NavTools()
    settings = navtools.getConfig(False)

    path = settings['toernDirectory']

    #r = upload_to_sqlite(settings['sqlitePath'], "test")

    msg = uploadMySQLfile(path)

    if not msg:
        print("\nError in uploadMySQLfile()!")
    else:
        print("\nuploadMySQL return:\n%s " % msg)

    FTPupload()

    print("\nAll Done!")
