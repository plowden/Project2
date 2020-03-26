# Start mongodb with this command before running this code: 
# mongod --config /usr/local/etc/mongod.conf

# Dependencies
from splinter import Browser
from bs4 import BeautifulSoup as bs
from flask import Flask, render_template, redirect
from flask_pymongo import PyMongo
#import pandas as pd
import pymongo
import requests
import time
import calendar
import datetime
import re

# Create variable for Webex data dictionary
webex_data = {}

# Calculates the hours in a month.
# Usage: get_hours("January 2020") or get_hours("Current")
def get_hours(month):
    months = ["January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"]
    month_list = re.split(r'\s', month)
    month = month_list[0]
    if month == "Current":
        year = datetime.datetime.today().strftime("%Y")
        days = int(datetime.datetime.today().strftime("%d"))
    else:
        year = month_list[1]
        days = calendar.monthrange(int(year),int(months.index(month))+1)[1]
    hours = days * 24
    return hours

def init_browser():
    #executable_path = {"executable_path": "/usr/local/bin/geckodriver"}
    #return Browser("firefox", **executable_path, headless=False)
    executable_path = {'executable_path': '/usr/local/bin/chromedriver'}
    return Browser('chrome', **executable_path, headless=False)


def scrape_webex():
    browser = init_browser()

    # Visit https://map.webex.com/
    url = "https://map.webex.com/"
    browser.visit(url)

    # Give time for dynamic content to load
    time.sleep(5)

    # Scrape page into Soup
    html = browser.html
    soup = bs(html, "html.parser")

    month_ids = ['last2Month', 'lastMonth', 'nowMonth']
    months = []
    hosts_commas = []
    hosts = []
    participants_commas = []
    participants = []
    countries = []
    meetings_commas = []
    meetings = []
    minutes = []

    for month_id in month_ids:
        with browser.get_iframe('meetingMap') as iframe:
            iframe.click_link_by_id(month_id)
            time.sleep(5)
            iframe_html = iframe.html
            iframe_soup = bs(iframe_html, "html.parser")
            months.append(iframe_soup.find('span', id=month_id).get_text())
            hosts_commas.append(re.search('title=\"(.*)\"', str(iframe_soup.find('span', id='hostData'))).group(1))
            participants_commas.append(re.search('title=\"(.*)\"', str(iframe_soup.find('span', id='participantData'))).group(1))
            countries.append(re.search('title=\"(.*)\"', str(iframe_soup.find('span', id='countryData'))).group(1))
            meetings_commas.append(re.search('title=\"(.*)\"', str(iframe_soup.find('span', id='meetingData'))).group(1))
            
            mins = []
            num = 11
            while num > 0:
                a = str(iframe_soup.find('div', id='num' + str(num)))
                b = re.search(r'<span>(\d*)', a).group(1)             
                mins.append(b)
                num = num - 1
            mins_string = ''.join(map(str, mins))
            minutes.append(mins_string)
                
    hosts =[s.replace(',', '') for s in hosts_commas]
    participants = [s.replace(',', '') for s in participants_commas]
    meetings = [s.replace(',', '') for s in meetings_commas]
    
    webex_days = {
        "months": months,
        "hosts": hosts,
        "participants": participants,
        "countries": countries,
        "meetings": meetings,
        "minutes": minutes
    }
    webex_hours = {
        "months": [],
        "hosts": [],
        "participants": [],
        "countries": [],
        "meetings": [],
        "minutes": []
    }
    
    # Close the browser after scraping
    browser.quit()

    # Convert to hours
    hours = []
    for i in webex_days["months"]:
        hours_month = get_hours(i)
        hours.append(int(hours_month))

    for i in range(3):
        webex_hours["hosts"].append(round(int(webex_days["hosts"][i]) / hours[i]))
        webex_hours["participants"].append(round(int(webex_days["participants"][i]) / hours[i]))
        webex_hours["meetings"].append(round(int(webex_days["meetings"][i]) / hours[i]))
        webex_hours["minutes"].append(round(int(webex_days["minutes"][i]) / hours[i]))

    webex_hours["countries"] = webex_days["countries"]
    webex_hours["months"] = webex_days["months"]

    # Return results
    return webex_hours

# Create an instance of Flask
app = Flask(__name__)

# Use PyMongo to establish Mongo connection
mongo = PyMongo(app, uri="mongodb://localhost:27017/webex")

# Route to render index.html template using data from Mongo
@app.route("/")
def home():

    # Find one record of data from the mongo database
    #destination_data = mongo.db.collection.find_one()
    webex_data = mongo.db.collection.find_one()

    print(f'{webex_data}')
    # Return template and data
    return render_template("index.html", webex_data=webex_data)

# Route that will trigger the webex function
@app.route("/webex")

def webex():

    # Run the webex function and store it in the dictionary
    webex_data = scrape_webex()

    webex_data = { 
      'months': webex_data['months'],
      'hosts': webex_data['hosts'],
      'participants': webex_data['participants'],
      'countries': webex_data['countries'],
      'meetings': webex_data['meetings'],
      'minutes': webex_data['minutes']
    }

    # Update the Mongo database using update and upsert=True
    mongo.db.collection.update({}, webex_data, upsert=True)

    # Redirect back to home page
    return redirect("/", code=302)

if __name__ == "__main__":
    app.run(debug=True)

