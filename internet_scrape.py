# Start mongodb with this command before running this code: 
# mongod --config /usr/local/etc/mongod.conf

# Dependencies
from splinter import Browser
from bs4 import BeautifulSoup as bs
from flask import Flask, render_template, redirect
from flask_pymongo import PyMongo
import pandas as pd
import pymongo
import requests
import time
import re

# Create variable for Mars data dictionary
mars_data = {}

# Create variable for hemispheres list
hemispheres = []

def init_browser():
    executable_path = {"executable_path": "/usr/local/bin/chromedriver"}
    return Browser("chrome", **executable_path, headless=False)

def scrape_mars_news():
    browser = init_browser()

    # Visit https://mars.nasa.gov/news/
    url = "https://mars.nasa.gov/news/"
    browser.visit(url)

    # Give time for dynamic content to load
    time.sleep(5)

    # Scrape page into Soup
    html = browser.html
    soup = bs(html, "html.parser")

    # Get the title
    scrape_title = soup.find(class_='content_title')
    title = scrape_title.find_all('a')[0].text

    # Get the teaser
    scrape_teaser = soup.find('div', class_='article_teaser_body')
    teaser = scrape_teaser.get_text()

    # Store data in a dictionary
    scrape_mars_news = {
        "title": title,
        "teaser": teaser
    }

    # Close the browser after scraping
    browser.quit()

    # Return results
    return scrape_mars_news

def scrape_featured_image():
    browser = init_browser()

    # Visit https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars
    url = "https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars"
    base_url = "https://www.jpl.nasa.gov"
    browser.visit(url)

    # Give time for dynamic content to load
    time.sleep(2)

    # Scrape page into Soup
    html = browser.html
    soup = bs(html, "html.parser")

    # Get the title
    scraped_url = soup.find('a', id='full_image')
    
    results = []

    for tmp in soup.find_all('a', {'class':'button fancybox'}):
        results.append(tmp['data-fancybox-href'])

    featured_image_url = base_url + results[0] 
    
    # Close the browser after scraping
    browser.quit()

    # Return results
    return featured_image_url

def scrape_tweet():
    browser = init_browser()

    # Visit https://twitter.com/marswxreport?lang=en
    url = "https://twitter.com/marswxreport?lang=en"
    browser.visit(url)

    # Give time for dynamic content to load
    time.sleep(3)

    # Scrape page into Soup
    html = browser.html
    soup = bs(html, "html.parser")

    scraped_tweet = soup.find_all(text=True)

    tweet = ''
    for text in scraped_tweet:
        if re.search(r'^InSight', text):
            tweet = text
            break
        
    # Close the browser after scraping
    browser.quit()

    # Return results
    return tweet

def scrape_facts():
    # Visit https://space-facts.com/mars/ 
    url = "https://space-facts.com/mars/"

    # Read in tables.
    tables = pd.read_html(url)

    # Convert first table to dataframe.
    df = tables[0]

    # Store dataframe as an HTML table string.
    html_table = df.to_html(classes=("table", "table-bordered"))

    # Strip newline characters.
    html_table = html_table.replace('\n', '')

    return html_table

def scrape_hemispheres():
    browser = init_browser()

    # Visit https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars 
    url = "https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars"
    browser.visit(url)

    # Give time for dynamic content to load
    time.sleep(5)
    
    # HTML object
    html = browser.html
    # Parse HTML with Beautiful Soup
    soup = bs(html, 'html.parser')
    # Retrieve all elements that contain hemisphere information
    hemispheres_tmp = soup.find_all('div', class_='description')

    hemisphere_list = []
    hemisphere_dict = {}
    
    # Iterate through each hemisphere
    for hemisphere in hemispheres_tmp:
        # Use Beautiful Soup's find() method to navigate and retrieve attributes
        link = hemisphere.find('a')
        title = link.find('h3').text.strip()
        href = re.search('\/(.*)\"', str(link)).group(1)
        link = 'https://astrogeology.usgs.gov/' + href
    
        browser.visit(link)

        # Give time for dynamic content to load
        time.sleep(3)

        # HTML object
        html = browser.html

        # Parse HTML with Beautiful Soup
        soup = bs(html, 'html.parser')
        div = soup.find('div', class_='downloads')
        a = div.find('a')
        img_url = a['href']

        hemisphere_dict = {'title': title, 'img_url': img_url}
        hemisphere_list.append(hemisphere_dict)
        print(f'hemisphere_dict: {hemisphere_dict}')
        
    # Close the browser after scraping
    browser.quit()

    return hemisphere_list

# Create an instance of Flask
app = Flask(__name__)

# Use PyMongo to establish Mongo connection
mongo = PyMongo(app, uri="mongodb://localhost:27017/mission_to_mars")

# Route to render index.html template using data from Mongo
@app.route("/")
def home():

    # Find one record of data from the mongo database
    #destination_data = mongo.db.collection.find_one()
    mars_data = mongo.db.collection.find_one()

    print(f'{mars_data}')
    # Return template and data
    return render_template("index.html", mars_data=mars_data)

# Route that will trigger the mars_news function
@app.route("/scrape")

def scrape():


    # Run the mars_news function and store it in the dictionary
    mars_news_data = scrape_mars_news()

    # Run the scrape_featured_image function and store it in the dictionary
    featured_image_url = scrape_featured_image()

    # Run the scrape_tweet function and store it in the dictionary
    tweet = scrape_tweet()

    # Run the scrape_facts function and store it in the dictionary
    facts = scrape_facts()

    # Run the scrape_hemispheres function and store it in the dictionary
    hemispheres = scrape_hemispheres()

    mars_data = { 
      'mars_news_title': mars_news_data['title'],
      'mars_news_teaser': mars_news_data['teaser'],
      'featured_image_url': featured_image_url,
      'tweet': tweet,
      'facts': facts,
      'hemispheres': hemispheres
    }

    # Update the Mongo database using update and upsert=True
    mongo.db.collection.update({}, mars_data, upsert=True)

    # Redirect back to home page
    return redirect("/", code=302)

if __name__ == "__main__":
    app.run(debug=True)

