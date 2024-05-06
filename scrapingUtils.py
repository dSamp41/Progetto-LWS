import random
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from fake_useragent import UserAgent

# Funzione per la estrazione dei proxy da sslproxies.org
def generate_proxies():
    ua = UserAgent() 
    
    proxies = []
    
    proxies_req = Request('https://www.sslproxies.org/')
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urlopen(proxies_req).read().decode('utf8')
    soup = BeautifulSoup(proxies_doc, 'html.parser')
    
    proxies_table = soup.find('table', class_='table table-striped table-bordered')
    
    # Salvo i proxy nella lista proxies
    for row in proxies_table.tbody.find_all('tr'):
        td = row.find_all('td')
        proxies.append(f'{td[0].string}:{td[1].string}')
    
    return proxies


#TODO: fake user agent [https://stackoverflow.com/questions/62490495/how-to-change-the-user-agent-using-selenium-and-python]
def setup_driver(executable_path='/home/dan/Università/Info/3/LWS/progetto/geckodriver'):
    
    #rotate proxy ip
    proxies = generate_proxies()
    proxy_server_url = random.choice(proxies)
    
    options = Options()
    options.add_argument('--headless') #TODO: remove comment
    options.add_argument(f'--proxy-server={proxy_server_url}')
    options.add_argument(f'user-agent={UserAgent().random}')

    service = webdriver.FirefoxService(executable_path=executable_path)
    driver = webdriver.Firefox(service=service, options=options)

    return driver

#print(generate_proxies())