from config import * 

from selenium import webdriver 
from selenium.webdriver.firefox.options import Options 
import pymongo
import os
from time import sleep
from datetime import datetime 
import json
from pathlib import Path 


client = pymongo.MongoClient(f"mongodb+srv://{mongo_username}:{mongo_pass}@{mongo_url}")
db = client.quotes

try:
    current_path = os.path.dirname(os.path.abspath(__file__))
except:
    current_path = '.'
    
def init_driver (gecko_driver,load_images=True,user_agent='',is_headless = Headless): 
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference ('domipc.plugins.enabled.libflashplayer',False)
    firefox_profile.set_preference ('media.volume_scale',"0.0")
    firefox_profile.set_preference ("dom.webnotifications.enabled",False)
    
    if not load_images: 
        firefox_profile.set_preference ('permission.default.image',2)
    if user_agent != '':
        firefox_profile.set_preference("general.useragent.override",user_agent)
    
    options = Options ()
    options.headless = is_headless
    driver = webdriver.Firefox(executable_path = f"{current_path}/{gecko_driver}",
                               firefox_profile = firefox_profile,
                               options = options)
    
    return driver 

def get_url (page_url,driver):
    driver.get(page_url)
    sleep(page_load_timeout)
    
def get_quotes (driver):
    quotes = driver.find_elements_by_css_selector('.quote')

    Quotes_select = []
    for quote in quotes:
        quote_text = ''
        if len (quote.find_elements_by_css_selector('.quoteText')) > 0:
             quote_text = quote.find_elements_by_css_selector('.quoteText')[0].text
        if len (quote_text) > 280 or quote_text == '':
            continue
       
    
        q_info = {
            'quote_text':quote_text,
            'inserted_at':datetime.now(),
            'published_at':False 
        }
        if db.quotes.count_documents ( {'quote_text':quote_text}) == 0:
            db.quotes.insert_one(q_info)
        Quotes_select.append( quote_text )
    return Quotes_select

def load_cookies(driver):
    driver.get (twitter_url)
    sleep(10)
    cookies = ''
    cookie_file = f"{current_path}/{twitter_cookies_path}"
    if Path(cookie_file).is_file():
        with open (cookie_file,'r',encoding = 'utf8') as ck_file:
            cookies = ck_file.read()
    
    if cookies != '':
        cookies = json.loads(cookies)
        if len (cookies) > 0: 
            for cookie in cookies:
                driver.add_cookie(cookie)
        sleep(5)
        
        driver.get(f"{twitter_url}/settings/account")
        if len (driver.find_elements_by_css_selector('.r-30o5oe')) > 2:
            open (cookie_file,'w').truncate()
            return False
        else:
            return True
    
    return False

def twitter_login(driver):
    driver.get (twitter_login_page)
    sleep(10)
    Email_Pass = driver.find_elements_by_css_selector('.r-30o5oe') 
    if len(Email_Pass) > 0:
        print(Email_Pass)
        Email_Pass[0].clear() #Clear Email field 
        Email_Pass[1].clear() #clear Password field
        sleep(2)
        Email_Pass[0].send_keys(twitter_email) #set Email field 
        Email_Pass[1].send_keys(twitter_pass) #set Password field
        sleep(2)
        login_button = driver.find_elements_by_css_selector('.r-1awozwy')
        login_button[2].click()
        sleep (5)

        cookies_list = driver.get_cookies()
        ck_file = open(f"{current_path}/{twitter_cookies_path}",'w',encoding = 'utf8')
        ck_file.write (json.dumps(cookies_list))
        ck_file.close()
        
def publish_quote (driver,quote):
        driver.get(twitter_url)
        sleep(5)
        if len (driver.find_elements_by_css_selector(".notranslate.public-DraftEditor-content")) > 0:
                tweet_box  = driver.find_elements_by_css_selector(".notranslate.public-DraftEditor-content")[0]
                tweet_box.click()
                sleep(2)

                quo = f""" 
                        {quote['quote_text']}
                """
                quo = quo.replace('\n','').strip()
                tweet_box  = driver.find_elements_by_css_selector(".notranslate.public-DraftEditor-content")[0]
                tweet_box.send_keys(quo)
                sleep(3)
                if len (driver.find_elements_by_css_selector(".r-bcqeeo")) > 0: 
                    tweet_button = driver.find_elements_by_css_selector(".r-bcqeeo")
                    tweet_button[57].click()
                    db.quotes.update_one( {'_id':quote['_id']},{'$set':{'published_at':datetime.now()}})
                    return True
        return False