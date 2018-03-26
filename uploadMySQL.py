#!/usr/bin/env python
# -- coding: utf-8 --
#from __future__ import unicode_literals
"""
---------------------------------------------------------------------------
Program to upload MySQL data to the MySQL DB for the websites at
kaiserware.bplaced.net and www.southmerochorale.org/toerns

Developed (c) 2017 by Volker Petersen
---------------------------------------------------------------------------
"""
__date__      = "Jul 17 2017"
__author__    = "Volker Petersen"
__copyright__ = "Copyright (c) 2017 Volker Petersen"
__license__   = "Python 3.6 | GPL http://www.gnu.org/licenses/gpl.txt"
__version__   = "uploadMySQL.py ver 1.0"

try:
    # import python system modules
    import os
    import ast
    import pymysql.cursors
    import urllib.request
    import urllib.error
    import urllib.parse
except ImportError as e:
    msg = "Import error: "+str(e)+"\nAborting the program " + __version__
    raise Exception(msg)

def upload_to_mysql(host, query):
    """
    |------------------------------------------------------------------------------------------
    | function to connect to the mysql DB 'map' at Hostmonster SouthMetroChorale
    | and execute the query
    |    
    | this function doesn't work for the bplaced site since it doesn't allow external
    | access to the MySQL DB.  We're now using the upload_to_mysql_via_php() for both
    | the southmetrochorale.org and kaiserware.bplaced.net sites
    |
    | @param      - website host
    | @param      - query string with the MySQL query to be executes
    | @ret        - # of records if successful or False if connection or query failed
    |------------------------------------------------------------------------------------------
    """
    rec = False
    
    if "hostmonster" in host.lower():
        db_host = 'southmetrochorale.org'
        db_user = 'southme1_sudo'
        db_pass = 'Vesret7713'
        db_name = 'southme1_map'
    else:
        # bplaced.net doesn't allow external access to MySQL DB
        print ("\nMySQL DB conection on host '%s' not implemented!" %host)
        return False
    try:
        connection = pymysql.connect(host=db_host, 
                          user=db_user, 
                          password=db_pass, 
                          db=db_name,
                          cursorclass=pymysql.cursors.DictCursor)
        #print ("Connected to MySQL DB '%s' on host '%s' (%s)" %(db_name, host, db_host))
    except:
        print ("\nFailed to connect to DB '%s' on host '%s' (%s)" %(db_name, host, db_host))
        return False
    
    
    try:
        with connection.cursor() as cursor:
            rec = cursor.execute(query)
        connection.commit()
        #print ("%s record(s) updated using the query:\n '%s'\n" %(rec, query))
        connection.close()
    except:
        print ("\nFailed to execute the query:\n '%s'.\n" %query)       
        return False
    
    return rec


def upload_to_mysql_via_php(host, query):
    """
    |------------------------------------------------------------------------------------------
    | function to execute the MySQL query 'query' at the website 'host'
    | using a php script at that site.  The query is packaged as json. 
    |
    | @param      - website host
    | @param      - query string with the MySQL query to be executes
    | @ret        - # of records if successful or False if connection or query failed
    |------------------------------------------------------------------------------------------
    """
    if "bplaced" in host.lower():
        db_host = 'http://kaiserware.bplaced.net/update_mysql.php'
        db_pass = 'vesret2204'
    elif "hostmonster" in host.lower():
        db_host = 'https://www.southmetrochorale.org/toerns/update_mysql.php'
        db_pass = 'ostsee'
    else:
        print ("\nMySQL DB conection on host '%s' not implemented!" %host)
        return False

    values = {'pw': db_pass, 'query': query}
    try:    
        data = urllib.parse.urlencode(values).encode("utf-8")
        req = urllib.request.Request(db_host, data)
        response = urllib.request.urlopen(req)
        ret = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print ("The server couldn\'t fulfill the request.")
        print ("Error code: %s" %str(e.code))
        ret = False
    except urllib.error.URLError as e:
        print ("We failed to reach a server.")
        print ("Reason: %s" %str(e.reason))
        ret = False
    except Exception as e:
        print ("We encountered an undefined urllib error.")
        print ("Reason: %s" %str(e))
        ret = False
    
    #print(ret)
    
    return ret

def uploadMySQLfile(sql_file,verbose=True):
    sql_file = os.path.normpath(sql_file.replace("gpx", "sql"))
    if (verbose):
        print ("uploadMySQLFile('%s')" %sql_file)

    try:
        with open(sql_file, 'r') as f:
            create = ""
            truncate = ""
            insert = ""
            for line in f:
                if ("CREATE TABLE" in line or create is not "") and "TRUNCATE" not in line and ("INSERT" not in line and insert is ""):
                    create += line
                elif "TRUNCATE" in line:
                    truncate = line
                elif ("INSERT INTO" in line or insert is not "") and truncate is not "":
                    insert += line
    except:
        print ("\nUnable to open the sql query file '%s'.  Terminating now." %(sql_file))
        return False
        
    #print ("\nCreate: ",create)
    #print ("\nTruncate: ",truncate)
    #print ("\nInsert: ",insert)

    if insert is "":
        print ("\nUnable to extract the sql query from the file '%s'.  Terminating now." %sql_file)
        return False
    
    ret = {}
    ret['Hostmonster'] = {}    
    ret['bplaced'] = {} 

    r = upload_to_mysql_via_php('Hostmonster', create)
    ret['Hostmonster']['Create'] = ast.literal_eval(r)
    r = upload_to_mysql_via_php('bplaced', create)
    ret['bplaced']['Create'] = ast.literal_eval(r)

    r = upload_to_mysql_via_php('Hostmonster', truncate)
    ret['Hostmonster']['Truncate'] = ast.literal_eval(r)
    r = upload_to_mysql_via_php('bplaced', truncate)
    ret['bplaced']['Truncate'] = ast.literal_eval(r)

    r = upload_to_mysql_via_php('Hostmonster', insert)
    ret['Hostmonster']['Insert'] = ast.literal_eval(r)
    r = upload_to_mysql_via_php('bplaced', insert)
    ret['bplaced']['Insert'] = ast.literal_eval(r)
        
    return ret

"""
|------------------------------------------------------------------------------------------
| main
|------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
    print (__doc__)
    
    working_directory1 = "D:/My Documents/Dropbox"  # Dell Descktop
    working_directory2 = "D:/VolkerPetersen"        # Dell Laptop
    if (os.path.exists(working_directory1) == True):
         # Home Desktop Dell XPS computer setup parameters
         cwd = working_directory1
    elif (os.path.exists(working_directory2) == True):
         # Volker's laptop computer
         cwd = working_directory2
    else:
        print ("\nUnknown computer and root file system.  Terminating now.")
        exit(0)

    path = os.path.join(cwd, "Dropbox/ProgramCode/PHP_Projects/toerns/sql_files")
    
    path2 = os.path.join(path, "ToernDirectoryTable.sql")
    path2 = os.path.normpath(path2)

    #msg = uploadMySQLfile(os.path.join(path, "2017_09_Baltic.sql"))
    msg = uploadMySQLfile(path2)

    if (not msg):
        print ("\nError in uploadMySQLfile()!")
    else:    
        if msg['bplaced']['Truncate']['status'] == "success" \
            and msg['bplaced']['Insert']['status'] == "success" \
            and msg['Hostmonster']['Truncate']['status'] == "success" \
            and msg['Hostmonster']['Insert']['status'] == "success":
                msg = msg['bplaced']['Insert']['msg']
    
        print ("\nuploadMySQL return: %s " %msg)
    
    print ("\nAll Done!")
