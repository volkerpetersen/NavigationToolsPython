#!/usr/bin/env python
# -*- coding: utf-8 -*-
__doc__ = """
---------------------------------------------------------------------------
 Script to log into the 'kaiserware' bplaced.net client area and
 retrieve the date/time of last login.  This script is used by the
 Desktop computer Task Scheduler to log into bplaced every three
 weeks to make sure the account doesn't lapsed due to inactivity.
---------------------------------------------------------------------------
"""
__date__ = "17/23/2017"
__author__ = "Volker Petersen"
__copyright__ = "Copyright (c) 2017 Volker Petersen"
__license__ = "Python 3.6 | GPL http://www.gnu.org/licenses/gpl.txt"
__version__ = "kaiserware.bplace.net web scraping app"

try:
    # import python system modules
    import sys
    from datetime import datetime
    from time import sleep
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
except ImportError as e:
    print ("Import error: %s\nAborting the program %s" %(e, __version__))
    sys.exit()


def init_driver():
    driver = webdriver.Chrome()
    driver.wait = WebDriverWait(driver, 2)

    return driver

def web_login(browser, url, username, password):

    print(browser, url, username, password)
    browser.get(url)
    try:
        browser.wait.until(EC.presence_of_element_located((By.ID, "login")))
        print ("found login link at '%s' ..." %url)

        field = browser.find_element_by_name('username')
        field.send_keys(username)

        field = browser.find_element_by_name('passphrase')
        field.send_keys(password)

        field = browser.find_element_by_name('login')
        field.click()
        print ("logging into '%s' user account '%s' now..." %(url, username))

        sleep(5)

        field = browser.find_element_by_id('bar')
        text = field.text

        browser.quit()

    except Exception as e:
        print ("\nLink not found on page / selenium browser error: %s" %str(e))
        text = " "

    return text
"""
|------------------------------------------------------------------------------------------
| main
|------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
    print (__doc__)

    print ("\nlaunching Chrome browser...")
    url = "http://www.bplaced.net/"
    username = "kaiserware"
    password = "vesret2204"
    filename = "bplaced_login.log"

    browser = init_driver()
    login_msg = web_login(browser, url, username, password)

    today = datetime.now()
    login = "login into '%s' user account '%s' yielded:" %(url, username)

    login_msg = "\n%s %s\n%s\n" %(today.strftime("%Y-%m-%d %H:%M:%S"), login, login_msg)

    FILE = open(filename, "a")
    FILE.writelines(login_msg)
    FILE.close()

    print ("\nretrieved login message:\n%s" %login_msg)

    print ("\n\nDone!\n")
