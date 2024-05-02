import time
from typing import List

from matplotlib import pyplot as plt

from addressScraping import setup_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement #typing
from selenium.common.exceptions import NoSuchElementException

import networkx as nx

ID = 'c82c10925cc3890f1299'
URL = 'https://www.walletexplorer.com'

# create graph
g: nx.DiGraph = nx.DiGraph()
K: int = 5

driver = setup_driver()
driver.get(URL)


def elaborateOutput(lst: List[WebElement], current_id: str):
    res = []
    for we in lst:
        tokens = we.text.split(' ')

        if tokens[2] == '(change':
            tokens.remove('(change')
        if tokens.__contains__(''):
            tokens = [t for t in tokens if t != '']
        
        if tokens.__contains__('unspent'):
            continue
        
        full_txid = we.find_element(By.PARTIAL_LINK_TEXT, tokens[5])\
            .get_dom_attribute('href')\
            .replace('/txid/', '')

        to = {'nextAddress': tokens[1], 'amount': int(tokens[3].replace('.', '')), 'currentTxId': current_id, 'nextTxId': full_txid}
        res.append(to)

    return res


def recursiveTransactionPath(driver, ID: str, N: int, g: nx.DiGraph):
    if(N == 0):
        return 
    
    #print(f'recursiveTransactionPath iteration#{N}')

    try:
        text_input = driver.find_element(By.XPATH, '/html/body/div[1]/form/input[1]')
        search_button = driver.find_element(By.XPATH, '/html/body/div[1]/form/input[2]')

        text_input.clear()
        text_input.send_keys(ID)
        search_button.click()
        #print(f'Actually at id: {ID}')        
    except NoSuchElementException:
        print('Error with text bar or search button')
        return 
    
    g.add_node(ID, color=N) 

    try:
        driver.implicitly_wait(7)

        outputs_rows = driver\
            .find_element(By.XPATH, '/html/body/div[2]/table[2]/tbody/tr[2]/td[2]/table/tbody')\
            .find_elements(By.TAG_NAME, 'tr')
    except NoSuchElementException:
        print(f'Can\'t find tr @<Id: {ID}>')
        return 

    outputs = elaborateOutput(outputs_rows, ID)
    #print(outputs_rows)

    for d in outputs:
        g.add_node(d['nextTxId'], color=N-1) 
        #g.add_edge(ID, d['nextTxId'], weight=d['amount'])
        g.add_edge(ID, d['nextTxId'], weight=d['amount'])

        time.sleep(5)
        recursiveTransactionPath(driver, d['nextTxId'], N-1, g)



recursiveTransactionPath(driver, ID, K, g)

driver.quit()


# graph drawing
node_colors = [abs(node[1]['color'] - K) for node in g.nodes(data=True)]
edge_amount = {(edge[0], edge[1]): edge[2]['weight'] for edge in g.edges(data=True)}


pos = nx.multipartite_layout(g, subset_key='color')
#nx.spiral_layout(g)
#nx.circular_layout(g)


ec = nx.draw_networkx_edges(g, pos, alpha=0.3)
nc = nx.draw_networkx_nodes(g, pos, nodelist=g.nodes(), node_color=node_colors, cmap=plt.get_cmap('cubehelix'), edgecolors='black')

#nx.draw_networkx_labels(g, pos, font_size=6)
nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_amount)


plt.colorbar(nc)
plt.show()