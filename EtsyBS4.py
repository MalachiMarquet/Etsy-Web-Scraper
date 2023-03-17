from bs4 import BeautifulSoup
import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import etree
import soupsieve as sv
import time


#Starting webdriver and navigating to last result page for seachers.
options = Options()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--start-maximized')
options.add_argument("window-size=1200x600")
options.add_argument('--headless')
s = Service(executable_path="C:\Program Files\Google\Chrome\Application\chromedriver.exe")
driver = webdriver.Chrome(service=s, options=options)
search_queury = 'https://www.etsy.com/search?q=wood+furniture&ref=pagination&page=250'
driver.get(search_queury)

#Window we branch form.
##I never use this. driver.switch_to.window(driver.window_handles[0]) works just fine.
original_window = driver.current_window_handle


#List to check if seller's page has already beeen scraped. If so it skips them next time their name comes up in the page search
seller = []
#Catalogue of scraped items grouped into sellers name 
catalogue = {}
#Search pages to loop. 250 is maximum search pages.
search_pages = 250

while search_pages > 0:
    #Getting DOM
    page_source = driver.page_source
    #Parsing info to find sellers name
    soup = BeautifulSoup(page_source, "lxml")
    seller_name = soup.find_all('div', {'class': 'wt-text-caption wt-text-truncate wt-text-grey wt-mb-xs-1 min-height'})
    for x in  seller_name:
        #stripping code to regular text (Got to be a better way)
        seller_text = x.text
        seller_strip = seller_text.strip('\n').replace('Ad vertisement by Etsy seller\n', '',1)
        #Checking if seller has already been scraped.
        if seller_strip not in seller:
            seller.append(seller_strip)
            print('--Working on a new Seller--') 
        else:
            print('--Already In Data Banks--')
            continue
        #Opens seller's page
        driver.get('https://www.etsy.com/shop/{}'.format(seller_strip))
        #Pushes button for last page in seller's catalogue
        try:
            ul_grab = driver.find_element(By.CLASS_NAME, 'wt-action-group.wt-list-inline.wt-flex-no-wrap.wt-flex-no-wrap.wt-pt-xl-2.wt-pb-xl-4')
            li_list = ul_grab.find_elements(By.TAG_NAME, 'li')
            next_button = li_list[-2]
            ActionChains(driver).move_to_element(next_button).click(next_button).perform()
            print('--Opening Sellers page--')
            driver.implicitly_wait(2)
        #Need to add the selenium error for precision and clarity, but I haven't had a problem. Can I use selenium erros in try, except?
        except:
            print('Only One Store Page')
            
        
        #Finding total number of product pages by using current url.
        ##I was too tired to read regex doccumentation, so I'm navigating the url backwards to find how many pages there are.
        body = driver.find_element(By.TAG_NAME, 'body')
        body.send_keys(Keys.CONTROL + 'r')
        #Implicit waits or EC waits didn't work for some reason. Got to read more doccumentation and see what I  missed.
        time.sleep(1)
        last_page = driver.current_url
        numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        count = 0
        page = []
        total_pages = 0
        for i in range(len(last_page)):
            didgit = last_page[-i]
            if didgit == '=':
                break
            if didgit in numbers:
                page.insert(0, didgit)
        for s in page:
            s = int(s)
            total_pages *= 10 * count
            total_pages += s
            count += 1


        #setting up sellers page to navigate to each items page
        catalogue_source = driver.page_source
        catalogue_soup = BeautifulSoup(catalogue_source, 'lxml')


        
        #This is the general store page info scrape
        sales = catalogue_soup.find('div', {'class': 'wt-mt-lg-5 wt-pt-lg-2 wt-bt-xs-1'})
        #This has both sales and admirers numbers
        sales = sales.text
        sales = sales.strip('\n')
        #Removing white space missed by strip
        ##How much does this slow down the program. Seems like it could be a lot of extra work.
        sales = ' '.join(sales.split())

        #Making a nested dictionary to store all seller info in one dictionary
        print('--Adding ' + str(seller_strip) + ' Info--')
        catalogue[seller_strip] = {}
        catalogue[seller_strip]['Sales'] = {sales}
        

        #print tracker and used to check if an item what item number the tracker is on.
        product_loop = 1


        product_pages = driver.find_elements(By.CLASS_NAME, 'listing-link.wt-display-inline-block')
        #This while loop is from a previous attempt to iterate through product pages by checking if the above Class Name was clickable.
        ##I built a break in that navigates to the last store page and uses the URL page number to navigate backwards.
        ###Should I bother changes this? How can I make it more clear what my loop is checking for.
        while product_pages != None:
            print('__--Starting ' + str(seller_strip) + ' Page ' + str(total_pages) + '--__')
            for item in product_pages:
                #There can be up to four honeypot items that cannont be clicked. That is was this try is for. I should make my except only for that selenium error. Can I use selenium erros that way?
                #Opens product in new window
                try:
                    ActionChains(driver).move_to_element(item).click(item).perform()
                except:
                    print('Most likely a honeypot element.')
                    continue
                #Implicit waits or EC waits didn't work for some reason. I need to read more doccumentation and see what I  missed.
                time.sleep(1)
                #switch driver to tab opened by clicking item
                driver.switch_to.window(driver.window_handles[1])
                #Making the soup
                item_source = driver.page_source
                item_soup = BeautifulSoup(item_source, 'lxml')
                #There are four pieces of information in this loop I'm finding. Item name, item price, item variations, and description.
                item_name = item_soup.find('h1', {'class': 'wt-text-body-01 wt-line-height-tight wt-break-word wt-mt-xs-1'})
                item_name = item_name.text
                item_name = item_name.strip('\n')
                #Removing extra white space and characters missed by strip
                item_name = ' '.join(item_name.split())
                item_price = item_soup.find('p', {'class': 'wt-text-title-03 wt-mr-xs-1'})
                item_price = item_price.text
                item_price = item_price.strip('\n')
                item_price = ' '.join(item_price.split())
                item_variations = item_soup.find('div', {'data-selector': 'listing-page-variations'})
                item_variations = item_variations.text
                item_variations = item_variations.strip('\n')
                #Removes extra white space and characters missed in strip
                item_variations = ' '.join(item_variations.split())
                item_description = item_soup.find('div', {'data-id': 'description-text'})
                item_description = item_description.text
                item_description = item_description.strip('\n')
                item_description = ' '.join(item_description.split())
                #Adding item info to a dictionary seller's key
                catalogue[seller_strip][item_name] =  {'Price': item_price, 'Variations': item_variations, 'Description': item_description}
                #Closes window
                body = driver.find_element(By.TAG_NAME, 'body')
                body.send_keys(Keys.CONTROL + 'w')
                driver.close()
                #Return Selenium back to origianl window
                driver.switch_to.window(driver.window_handles[0])
                print('__--Finished ' + str(seller_strip) + ' Page ' + str(total_pages) + ' Item ' + str(product_loop) + '--__')
                #How many items on the page that have been scraped.
                product_loop += 1

            

            
            
            
            

            #Setting up for the next sellers page / checking if first page was reached.
            if total_pages <= 1:
                total_pages = 0
                break
            total_pages -= 1
            driver.get('https://www.etsy.com/shop/{}?ref=shop_sugg_market&page={}#items'.format(seller_strip, total_pages))
            #Implicit waits or EC waits didn't work for some reason. Got to read more doccumentation and see what I  missed.
            time.sleep(1)
            product_pages = driver.find_elements(By.CLASS_NAME, 'listing-link.wt-display-inline-block')
            product_loop = 1


        
        #Resetting for next seller page
        product_loop = 1
        
        
    #tracker for seach pages. 250 maximum result, like the sellers page we are navigating backwards here to. We subtract one and plug it into the url.
    search_page -= 1
    driver.get('https://www.etsy.com/search?q=wood+furniture&ref=pagination&page={}'.format(search_page))
    time.sleep(1)
    
    
    








        






                




