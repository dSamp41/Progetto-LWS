from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from addressScraping import get_wallet

base: str = "./datasets/"

# load transactions dataset
transactions = pd.read_csv(
    base + "transactions.csv",
    names=['timestamp', 'blockId', 'txId', 'isCoinbase', 'fee'],
    dtype={'timestamp': np.uint32, 'blockId': np.uint32, 'txId': np.uint32, 'isCoinbase': np.uint8},
)

# load output dataset
outputs = pd.read_csv(
    base + "outputs.csv",
    names=['txId', 'txPos', 'addressId', 'amount', 'scriptType'],
    dtype={'txId': np.uint32, 'txPos': np.uint16, 'addressId': np.uint32, 'amount': np.uint64, 'scriptType': np.uint8}
)

# load output dataset
mappings = pd.read_csv(
    base + "mappings.csv",
    names=['address', 'addressId'],
    dtype={'address': pd.StringDtype(), 'addressId': np.uint32}
)


# load pool dataset
pool = pd.read_csv(
    "poolAddresses.csv",
    names=['pool', 'address'],
    dtype={'pool': pd.StringDtype(), 'address': pd.StringDtype()}
)



transactions_cb = transactions[transactions['isCoinbase'] == 1]\
    .drop(columns=['isCoinbase', 'fee'])    # max fee == 0 => drop 'fee'


merged_tx_output = pd.merge(transactions_cb, outputs, on='txId')\
    .drop(columns=['txPos'])


# associate pool with address (better, id) of transactions 
merged_pool_id = pd.merge(pool, mappings, on='address')\
    .drop('address', axis=1)

assert merged_pool_id['addressId'].unique().size == len(merged_pool_id.index)   # assert no double address <-> pool relation


# de-anonymize
deanonymized_tx = pd.merge(merged_tx_output, merged_pool_id, on='addressId', how='left')
deanonymized_tx.fillna(value='Other', inplace=True)

#print(deanonymized_tx)

assert len(deanonymized_tx.index) == len(merged_tx_output.index)



#find top 4 miners
others = deanonymized_tx[deanonymized_tx['pool'] == 'Other']

#print(others)
#print(f'unique addresses: {others["addressId"].unique().size}')

addressTxCount = others.groupby('addressId').agg(txCount=('txId', 'size')).reset_index()
#print(addressTxCount.nlargest(4, 'txCount'))

assert len(addressTxCount.index) == others["addressId"].unique().size
assert addressTxCount['txCount'].sum() == len(others.index)

top4Miner = addressTxCount.nlargest(4, 'txCount')\
    .merge(mappings, on='addressId')\
    .drop(columns=['addressId'])

top4MinerAddresses = top4Miner['address'].to_numpy()
#print(list(top4MinerAddresses))

addr_wallets = get_wallet(list(top4MinerAddresses))

# convert address to addressId
id_wallets = {}

for addr, wallet in addr_wallets.items():
    id = mappings[mappings['address'] == addr]
    id_wallets.update({id['addressId'].values[0]: wallet})


# update deanonymized_tx with top4 miner wallet
def update_pool(row):
    if row['addressId'] in id_wallets:
        return id_wallets[row['addressId']]
    else:
        return row['pool']

deanonymized_tx['pool'] = deanonymized_tx.apply(update_pool, axis=1)



# analizzare le Coinbase deanonimizzate:
#   numero di blocchi minati sia globalmente, che mostrando l’andamento temporale dei blocchi minati, per intervalli temporali di due mesi
#   distribuzione delle reward totali ricevute da ogni mining pool, sia globalmente che mostrandone l'andamento temporale

interest_df = deanonymized_tx[deanonymized_tx['pool'] != 'Other']\
    .drop(columns=['txId', 'addressId', 'scriptType'])

nBlocks_grouped = interest_df.groupby('pool').agg({'blockId': 'size', 'amount': 'sum'})\
    .reset_index()
nBlocks_grouped.columns = ['pool', 'blockCount', 'totalAmount']


# controllo: non si sono perse righe
assert nBlocks_grouped['blockCount'].sum() == len(interest_df.index)
assert nBlocks_grouped['totalAmount'].sum() == interest_df['amount'].sum()

#print(nBlocks_grouped)
rows = nBlocks_grouped['pool'].unique().size

figBar, axsBar = plt.subplots(1, 2, figsize=(10, 12), sharex=True)
axsBar[0].bar(nBlocks_grouped['pool'], nBlocks_grouped['blockCount'])
axsBar[0].set_title('Blocchi minati globalmente')
axsBar[0].set_xticklabels(nBlocks_grouped['pool'], rotation=45)

axsBar[1].bar(nBlocks_grouped['pool'], nBlocks_grouped['totalAmount'])
axsBar[1].set_title('Reward globali')
axsBar[1].set_xticklabels(nBlocks_grouped['pool'], rotation=45)


def autopct_format(values):
    def my_format(pct):
        total = sum(values)
        val = int(round(pct*total/100.0))
        return '{:.1f}%\n({v:d})'.format(pct, v=val)
    return my_format

figPie, axsPie = plt.subplots(1, 2, figsize=(10, 12), sharex=True)
axsPie[0].pie(x=nBlocks_grouped['blockCount'], labels=nBlocks_grouped['pool'], autopct=autopct_format(nBlocks_grouped['blockCount']))
axsPie[0].set_title('Percentuale blocchi minati')
axsPie[0].set_aspect('equal')

axsPie[1].pie(x=nBlocks_grouped['totalAmount'], labels=nBlocks_grouped['pool'], autopct='%1.1f%%',)
axsPie[1].set_title('Percentuale reward globali')
axsPie[1].set_aspect('equal')

''' statistiche globali
             pool  blockCount     totalAmount
       019a46b8d8        1741   8713619305387
       01a990df75        1738   7416681029411
       3e486bf1d3        2587  12696869155524
         BTCGuild        1162   4203649145799
        BitMinter        2024   9413281313194
EclipseMC.com-old        1919   8772777983863
          Eligius        1439    671414768803
'''

interest_df['timestamp'] = pd.to_datetime(interest_df['timestamp'], unit='s')

rows = nBlocks_grouped['pool'].unique().size
#fig, axs = plt.subplots(rows, 2, figsize=(10, 12), sharex=True)
plt.subplots_adjust(hspace=0.5)

i = 0
for p in nBlocks_grouped['pool']:
    df = interest_df[interest_df['pool'] == p]\
        .drop(columns=['pool'])\
        .resample('2ME', on='timestamp')\
        .agg({'blockId': 'count', 'amount': 'sum'}).reset_index()
    
    df.columns = ['timestamp', 'blockCount', 'totalAmount']
    
    #assert df['totalAmount'] == nBlocks_grouped[nBlocks_grouped['pool'] == p]
    #print(p)
    #print(df)

    fig, axs = plt.subplots(2, 1, figsize=(10, 12), sharex=True)
    axs[0].bar(df['timestamp'], df['blockCount'])
    axs[0].set_title(f'{p}: andamento blocchi minati')

    axs[1].bar(df['timestamp'], df['totalAmount'])
    axs[1].set_title(f'{p}: andamento reward')
        
    '''axs[i, 0].bar(df['timestamp'], df['blockCount'])
    axs[i, 0].set_title(f'{p}: andamento blocchi minati')
    axs[i, 0].set_yscale('log')

    axs[i, 1].bar(df['timestamp'], df['totalAmount'])
    axs[i, 1].set_title(f'{p}: andamento reward')'''

    #i += 1

    
plt.show()