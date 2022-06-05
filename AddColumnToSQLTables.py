#!/usr/bin/env python
# -- coding: utf-8 --
#from __future__ import unicode_literals
#--------------------------------------------------------------------------------------------
__author__	  = "Volker Petersen <volker.petersen01@gmail.com>"
__version__	  = "AddColumnToSQLTables.py (ver 2.1.0)"
__date__	  = "Date: 2018/12/04"
__copyright__ = "Copyright (c) 2017 Volker Petersen"
__license__	  = "Python 3.6 | GPL http://www.gnu.org/licenses/gpl.txt"
__doc__		  = """
-------------------------------------------------------------------------------
  Program parameters:
	route - none

  Adding a column to the a2hosting.org and kaiserware.bplaced.net 
  MYSQL database route tables.

-------------------------------------------------------------------------------
"""

try:
	import sys, os, inspect
	from datetime import datetime
	from NavConfig import getNavConfig
	from uploadMySQL import upload_to_mysql_via_php
	from uploadMySQL import upload_to_mysql
except ImportError as e:
	print("Import error: %s \nAborting the program %s" %(e, __version__))
	sys.exit()

def addColumnToAllSqlFiles(pathSQL):
	"""
	|------------------------------------------------------------------------------------------
	| function to add a column to all SQL files
	|
	| @param	pathSQL - path to the SQL files
	| @ret		status msg
	|------------------------------------------------------------------------------------------
	"""

	sqlExists = "SHOW COLUMNS FROM `Table_Name` LIKE 'notes';"
	sqlAdd = "ALTER TABLE `Table_Name` ADD `notes` VARCHAR (80) AFTER `image`;"
	
	fileList = os.listdir(pathSQL)
	ctrBplaced = 0;
	ctrA2host = 0;
	ctr = 0;
	success = 0
	for fileName in fileList:
		name, extension = os.path.splitext(fileName)
		if "sql" in extension and "ToernDirectoryTable" not in name:
			flag = True
			print("working on table '%s'....." %name, end="")
			sqlExists = sqlExists.replace("Table_Name", name)
			sqlAdd = sqlAdd.replace("Table_Name", name)
			
			msg=upload_to_mysql("a2hosting", sqlExists)
			if ("success" in msg["status"] and "Updated 0 records" in msg["msg"]):
				msg=upload_to_mysql("a2hosting", sqlAdd)
				ctrA2host = ctrA2host + 1
				if ("failure" in msg["status"]):
					print("Error (%s) adding the column to '%s'" %(msg["msg"], name))
					ctrA2host = ctrA2host - 1
					flag = False

			sqlExists1 = sqlExists.replace(name, "kaiserware."+name)
			msg=upload_to_mysql_via_php("bplaced", sqlExists1)
			if ("success" in msg["status"] and "Updated 0 records" in msg["msg"]):
				sqlAdd1 = sqlAdd.replace(name, "kaiserware."+name)
				msg=upload_to_mysql("bplaced", sqlAdd1)
				ctrBplaced = ctrBplaced + 1
				if ("failure" in msg["status"]):
					print("Error (%s) adding the column to '%s'" %(msg["msg"], name))
					ctrBplaced = ctrBplaced + 1
					flag = False
				
			ctr = ctr + 1
			if (flag):
				print(" OK")
			else:
				print(" Error")
		else:
			print("skipping file '%s'." %fileName)
	
	return ("Added %d columns in A2Hosting DB and %d in bplaced DB for %d SQL tables" %(ctrBplaced, ctrA2host, ctr))
	
"""
|------------------------------------------------------------------------------------------
| main
|------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
	print("\nStarting %s" %__version__)
	print(__doc__)

	# configuration data
	(cwd, pathGPX, pathSQL) = getNavConfig(False)
	
	ret = addColumnToAllSqlFiles(pathSQL)
	
	"""
	sqlAdd = "ALTER TABLE `ToernDirectoryTable` DROP `notes`;"
	ret=upload_to_mysql("a2hosting", sqlAdd)
	print(ret)
	ret=upload_to_mysql("bplaced", sqlAdd)
	print(ret)
	"""
	
	print("%s\n\nProgram is done." %ret)

