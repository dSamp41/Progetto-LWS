from typing import Dict, TypeAlias
from selenium.webdriver.common.by import By

from scrapingUtils import setup_driver

Address: TypeAlias = str
Wallet: TypeAlias = str


def get_wallet(addresses: list[Address]) -> Dict[Address, Wallet]:
    URL = 'https://www.walletexplorer.com'
    wallet = {}

    driver = setup_driver()
    driver.get(URL)

    for address in addresses:
        text_input = driver.find_element(By.XPATH, '/html/body/div[1]/form/input[1]')
        search_button = driver.find_element(By.XPATH, '/html/body/div[1]/form/input[2]')

        text_input.send_keys(address)
        search_button.click()

        driver.implicitly_wait(5)
        h2 = driver.find_element(By.XPATH, '/html/body/div[2]/h2')
        wallet_id = h2.text.split(' ')[1].replace('[', '').replace(']', '')
        
        wallet.update({address: wallet_id})

    driver.quit()
    return wallet

if __name__ == '__main__':
    ads = ['1811f7UUQAkAejj11dU5cVtKUSTfoSVzdm', '1Baf75Ferj6A7AoN565gCQj9kGWbDMHfN9', '1KUCp7YP5FP8ViRxhfszSUJCTAajK6viGy', '151z2eoe2D9f6cohGNNU96GsKAqLfYP8mN']
    print(get_wallet(ads))