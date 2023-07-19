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
    navtools = NavTools()

except ImportError as e:
    msg = "Import error: " + str(e) + "\nAborting the program " + __version__
    raise Exception(msg)

# %%


def upload_to_sqlite(DBfile, query):
    """
    |------------------------------------------------------------------------------------------
    | function to execute queries in the sqlite DB 'toernsDB.sqlite3'
    |
    | @param      - DBfile path/filename of the SQLite DB
    | @param      - query string with the SQL query to be executes
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

        msg = f"Updated {rec} records in the SQlite DB using Python."
        ret = {"msg": msg, "status": "success"}

    except Exception as e:
        msg = f"Error accessing the SQLite DB '{DBfile}':\n{str(e)}."
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
        msg = f"MySQL DB connection on host '{host}' not implemented!"
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
        msg = (f"Failed to connect to DB '{db_name}' on"
               f" host '{host}' ({db_host})"
               f" Error code: {str(e)}.")
        ret = {"msg": msg, "status": "failure"}
        return ret

    try:
        with connection.cursor() as cursor:
            rec = cursor.execute(query)
        connection.commit()
        # print ("%s record(s) updated using the query:\n '%s'\n" %(rec, query))
        connection.close()
    except Exception as e:
        msg = (f"Failed to execute the query:\n '{query}'.\n"
               f" Error code: {str(e)}.")
        ret = {"msg": msg, "status": "failure"}
        return ret

    msg = f"Updated {rec} records in the MySQL DB using Python."
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
        print(f"\n{msg}")
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
        msg = (f"The server could not fulfill the request."
               f" Error code: {str(e.code)}")
        print(msg)
        ret = {"msg": msg, "status": "failure"}
    except urllib.error.URLError as e:
        msg = (f"We failed to reach a server."
               f" Error code: {str(e.reason)}")
        print(msg)
        ret = {"msg": msg, "status": "failure"}
    except Exception as e:
        msg = (f"We encountered an undefined urllib error."
               f" Error code: {str(e)}")
        print(msg)
        ret = {"msg": msg, "status": "failure"}

    return ret


def uploadSQLiteFile(sql_file, verbose=True):
    settings = navtools.getConfig()

    if("sqlite_files\\ToernDirectoryTable.sql" in sql_file):
        sqliteFile = os.path.normpath(settings['toernDirectory'])
    else:
        sqliteFile = os.path.normpath(sql_file.replace("gpx", "sql"))

    if verbose:
        print(f"uploadMySQLFile sqlite:.'{sqliteFile}'")

    try:
        with open(sqliteFile, "r") as file:
            sqliteCreate = ""
            sqliteTruncate = ""
            sqliteInsert = ""
            for line in file:
                line = line.replace("\t", "")
                line = line.replace("\n", "")
                line = line.replace("\\", "")
                if ("DROP TABLE" in line):
                    sqliteTruncate = line

                if (("CREATE TABLE" in line or sqliteCreate != "") 
                    and ("INSERT INTO" not in line)
                    and (sqliteInsert == "")
                ):
                    sqliteCreate += line

                if (("INSERT INTO" in line or sqliteInsert != "")
                    and ("CREATE TABLE" not in line)
                    and ("--" not in line)
                ):
                    sqliteInsert += line

    except IOError as e:
        print(
            f"\nUnable to open the sql query file '{sql_file}'"
            f" (error: '{e.strerror}').  Terminating now.")
        return False

    except:
        print(f"Unexpected Error: '{sys.exc_info()[0]}'")
        return False

    #print(f"\nCreate: {sqliteCreate}")
    #print(f"\nTruncate: {sqliteTruncate}")
    #print(f"\nInsert: {sqliteInsert}")

    if sqliteInsert == "":
        print(
            f"\nUnable to extract the sql query from the file "
            f"'{sql_file}'.  Terminating now."
        )
        return False

    ret = {}

    r = upload_to_sqlite(settings["sqliteDB"], sqliteTruncate)
    ret["Truncate"] = r

    r = upload_to_sqlite(settings["sqliteDB"], sqliteCreate)
    ret["Create"] = r

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
    ret = ftp_server.storbinary(f"STOR {filename}", fh_sqlite)
    ftp_server.close()

    return ret


# %%
"""
|------------------------------------------------------------------------------------------
| main
|------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
    print(f"\nStarting {__app__}")
    print(__doc__)

    # load configuration data
    settings = navtools.getConfig(False)

    path = settings['toernDirectory']

    # r = upload_to_sqlite(settings['sqlitePath'], "test")

    msg = uploadSQLiteFile(path)

    if not msg:
        print("\nError in uploadSQLiteFile()!")
    else:
        print(f"\nuploadMySQL return:\n{msg}")

    #FTPupload()

    print("\nAll Done!")
