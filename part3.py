import time
from typing import List

from matplotlib import pyplot as plt
import numpy as np

from addressScraping import setup_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement #typing
from selenium.common.exceptions import NoSuchElementException

import networkx as nx

ID_START = 'c82c10925cc3890f1299'
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
        
        #print(tokens)
        
        full_txid = we.find_element(By.PARTIAL_LINK_TEXT, tokens[5])\
            .get_dom_attribute('href')\
            .replace('/txid/', '')
        
        if tokens[2] == 'address)':
            next_wallet = None
        else:
            next_wallet = tokens[2]

        to = {'nextAddress': tokens[1], 'nextWallet': next_wallet, 'amount': float(tokens[3]), 'currentTxId': current_id, 'nextTxId': full_txid}
        res.append(to)

    return res


def recursiveTransactionPath(driver, ID: str, N: int, g: nx.DiGraph, wallet:str = 'CB', address='CB'):
    if(N == 0):
        return 
    
    #print(f'recursiveTransactionPath iteration#{N}')

    # go to tx_id=ID page 
    try:
        text_input = driver.find_element(By.XPATH, '/html/body/div[1]/form/input[1]')
        search_button = driver.find_element(By.XPATH, '/html/body/div[1]/form/input[2]')

        text_input.clear()
        text_input.send_keys(ID)
        search_button.click()
        print(f'Actually at id: {ID}')        
    except NoSuchElementException:
        print('Error with text bar or search button')
        return 
    
    g.add_node(ID, color=N, wallet=wallet, address=address) #TODO: fix CB label for every node until N-th layer

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
        #print(d)
        
        if d['nextWallet'] is None:
            node_wallet = d['nextAddress']
        else:
            node_wallet = d['nextWallet']

        g.add_node(d['nextTxId'], color=N-1, wallet=node_wallet, address=d['nextAddress'])
        g.add_edge(ID, d['nextTxId'], weight=d['amount'])

        time.sleep(5)
        recursiveTransactionPath(driver, d['nextTxId'], N-1, g, node_wallet, d['nextAddress'])



recursiveTransactionPath(driver, ID_START, K, g)
driver.quit()


# graph drawing

#https://stackoverflow.com/questions/21978487/improving-python-networkx-graph-layout
pos = nx.multipartite_layout(g, subset_key='color')
#nx.nx_agraph.graphviz_layout(g, prog="fdp")


node_colors = [abs(node[1]['color'] - K) for node in g.nodes(data=True)]

ec = nx.draw_networkx_edges(g, pos, alpha=0.3)
nc = nx.draw_networkx_nodes(g, pos, nodelist=g.nodes(), node_color=node_colors, cmap=plt.get_cmap('cubehelix'), edgecolors='black')

# node labels
node_labels = {node[0]:node[1]['address'] for node in g.nodes(data=True)}
nx.draw_networkx_labels(g, pos, node_labels, font_size=6)


#edge labels
edge_amount = {(edge[0], edge[1]): edge[2]['weight'] for edge in g.edges(data=True)}
nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_amount)

for n in g.nodes(data=True):
    print(n)

plt.colorbar(nc)
#plt.show()


# degree distribution
vk = dict(g.out_degree())

values = list(vk.values())
#print('vk', values)

# remove ending points (out_degree == 0)
num_ending_nodes = 0
while(0 in values):
    values.remove(0)
    num_ending_nodes += 1

#print(f"num_ending_nodes: {num_ending_nodes}")

meanDegree = np.mean(values)
#print(f'Mean degree: {meanDegree}')


# plotting distribution
plt.figure()
plt.hist(values)

plt.title("Degree distribution")
plt.xlabel("Degree")
plt.ylabel("#nodes")

plt.show()
