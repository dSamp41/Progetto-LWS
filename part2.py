import pandas as pd
import numpy as np
import matplotlib.pylab as plt

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
    .drop(columns=['timestamp', 'txPos'])
print(merged_tx_output.columns)


# associate pool with address (better, id) of transactions 
merged_pool_id = pd.merge(pool, mappings, on='address')\
    .drop('address', axis=1)
print(merged_pool_id.columns)
assert merged_pool_id['addressId'].unique().size == len(merged_pool_id.index)   # assert no double address <-> pool relation


# de-anonymize
deanonymized_tx = pd.merge(merged_tx_output, merged_pool_id, on='addressId', how='outer')


print(merged_tx_output)
print(merged_pool_id)
print(deanonymized_tx)

print(f'{len(deanonymized_tx.index)} == {len(merged_tx_output.index)}')


'''stil_anon_cond = ~merged_tx_output['txId'].isin(deanonymized_tx['txId'])
anonymous_tx = merged_tx_output[stil_anon_cond]
print(anonymous_tx)

print(f' {len(deanonymized_tx.index) + len(anonymous_tx.index)} == {len(merged_tx_output.index)}')
assert len(deanonymized_tx.index) + len(anonymous_tx.index) == len(merged_tx_output.index)'''

