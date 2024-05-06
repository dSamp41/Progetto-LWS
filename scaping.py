import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pandas as pd

from scrapingUtils import setup_driver

URL = 'https://www.walletexplorer.com'
pools = ['Eligius', 'DeepBit', 'BitMinter', 'BTCGuild']

addresses = []

driver = setup_driver()
driver.get(URL)

for pool in pools:
    text_input = driver.find_element(By.XPATH, '/html/body/div[2]/form/p/label/input')
    search_button = driver.find_element(By.XPATH, '/html/body/div[2]/form/p/input')
    
    text_input.send_keys(pool)
    search_button.click()

    driver.implicitly_wait(5)
    viewAddress = driver.find_element(By.CSS_SELECTOR, '.showother > a:last-child')
    viewAddress.click()


    pages = driver\
        .find_element(By.XPATH, '/html/body/div[2]/div[1]')\
        .text.split(' ')
    
    totPages = int(pages[5])

    #TODO: more clean if going from last to first
    if totPages != 1:
        currentPage = 1

        while(currentPage < totPages):
            print(f'curr: {currentPage}')
            
            # scrape addresses
            rows = driver.find_elements(By.TAG_NAME, 'tr')[1:]
            addresses += [{'pool': pool, 'address': row.find_element(By.XPATH, 'td[1]').text} for row in rows]
            
            # go to next page
            driver.implicitly_wait(5)
            try:
                nextButton = driver.find_element(By.XPATH, '//a[text()="Next…"]')
                nextButton.click()
            except NoSuchElementException:
                break

            currentPage += 1

        print('out of while')
        driver.implicitly_wait(3)
        lastButton = driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/a[3]')
        lastButton.click()

        rows = driver.find_elements(By.TAG_NAME, 'tr')[1:]
        addresses += [{'pool': pool, 'address': row.find_element(By.XPATH, 'td[1]').text} for row in rows]


    time.sleep(5)

    homeAnchor = driver.find_element(By.XPATH, '/html/body/div[1]/h1/a')
    homeAnchor.click()

    #TODO: longer wait

driver.quit()

addressDf = pd.DataFrame.from_records(addresses, columns=['pool', 'address'])
addressDf.to_csv('poolAddresses.csv', index=False, header=False)
