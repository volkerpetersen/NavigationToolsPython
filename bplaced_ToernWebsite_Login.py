#!/usr/bin/env python
# -*- coding: utf-8 -*-
__doc__ = """
---------------------------------------------------------------------------
 Script to log into the bplaced.net and pythonanywhere.com client areas 
 and retrieve the date/time of last login.  This script is used by the
 Desktop computer Task Scheduler to log into these accounts every three
 weeks to make sure the account doesn't lapsed due to inactivity.
---------------------------------------------------------------------------
"""
__date__ = "17/23/2017"
__author__ = "Volker Petersen"
__copyright__ = "Copyright (c) 2017 Volker Petersen"
__license__ = "Python 3.8 | GPL http://www.gnu.org/licenses/gpl.txt"
__version__ = "kaiserware.bplace.net web scraping app"

try:
    # import python system modules
    import sys
    import os
    import pathlib
    from datetime import datetime
    from time import sleep
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError as e:
    print("Import error: %s\nAborting the program %s" % (e, __version__))
    sys.exit()


def init_driver():
    driver = webdriver.Firefox()
    driver.wait = WebDriverWait(driver, 2)

    return driver


def web_login(browser, url, username, password):

    # print(browser, url, username, password)
    browser.get(url)
    try:
        if "pythonanywhere" in url:
            browser.wait.until(
                EC.presence_of_element_located((By.ID, "id_next")))
            # print ("found login link at '%s' ..." %url)

            field = browser.find_element(By.NAME, "auth-username")
            # print("found user field")
            field.send_keys(username)

            field = browser.find_element(By.NAME, "auth-password")
            # print("found password field")
            field.send_keys(password)

            field = browser.find_element(By.ID, "id_next")
            # print("found login button")
            field.click()
            # print("logging into '%s' user account '%s' now..." % (url, username))

            browser.wait.until(
                EC.presence_of_element_located((By.ID, "id_web_app_link"))
            )

            field = browser.find_element(By.ID, "id_web_app_link")
            # print("found WEB page link")
            field.click()

            browser.implicitly_wait(15)  # wait for up to 15 seconds for DOM

            field = browser.find_element(By.CLASS_NAME, "webapp_extend")
            field.click()

            field = browser.find_element(By.CLASS_NAME, "webapp_expiry")
            text = field.text
        else:
            browser.wait.until(
                EC.presence_of_element_located((By.ID, "login")))
            # print ("found login link at '%s' ..." %url)

            field = browser.find_element(By.NAME, "credentials_user")
            # print ("found user field")
            field.send_keys(username)

            field = browser.find_element(By.NAME, "credentials_pass")
            # print ("found password field")
            field.send_keys(password)

            field = browser.find_element(By.CLASS_NAME, "button_action")
            # print ("found login button")
            field.click()
            print("logging into '%s' user account '%s' now..." %
                  (url, username))

            sleep(60)

            field = browser.find_element(By.CLASS_NAME, "menu_nav_lastlogin")
            # print ("browser.findElement By.CLASS_NAME(): %s" %field.text)
            # file = open("browser.txt", 'w')
            # file.write(browser.page_source)
            # file.close()
            # print ("browser content written to file")
            text = field.text

        browser.quit()

    except Exception as e:
        text = "Selenium browser error: '" + str(e) + "'."
        print("\n%s", text)

    return text


def login(url, username, password, filename):
    browser = init_driver()
    login_msg = web_login(browser, url, username, password)

    today = datetime.now()
    login = "login into '%s' with user account '%s' yielded:" % (url, username)

    login_msg = "\n%s %s\n%s\n" % (
        today.strftime("%Y-%m-%d %H:%M:%S"),
        login,
        login_msg,
    )

    FILE = open(filename, "a")
    FILE.writelines(login_msg)
    FILE.close()

    return login_msg


"""
|------------------------------------------------------------------------------------------
| main
|------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
    print(__doc__)

    print("\nlaunching Firefox browser...")

    url = "https://my.bplaced.net/php"
    cwd = pathlib.Path(__file__).parent.absolute()
    filename = "bplaced_login.log"
    logFile = os.path.join(cwd, filename)

    username = "volker.petersen01@gmail.com"
    password = "vesret2204"
    login_msg = login(url, username, password, logFile)
    print("\n%s" % login_msg)

    username = "volker.petersen@outlook.com"
    password = "Reklov7713,./"
    login_msg = login(url, username, password, logFile)
    print("\n%s" % login_msg)

    url = "https://www.pythonanywhere.com/login/?next=/login/"
    username = "volkersailing"
    password = "OZhzDVNTZk7xVBwI02ZN"
    login_msg = login(url, username, password, logFile)
    print("\n%s" % login_msg)

    print("\n\nDone!\n")
