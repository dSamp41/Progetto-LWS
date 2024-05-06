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

# load input dataset
inputs = pd.read_csv(
    base + "inputs.csv",
    names=['txId', 'prevTxId', 'prevTxPos'],
    dtype={'txId': np.uint32, 'prevTxId': np.uint32, 'prevTxPos': np.uint16},
)

# load output dataset
outputs = pd.read_csv(
    base + "outputs.csv",
    names=['txId', 'txPos', 'addressId', 'amount', 'scriptType'],
    dtype={'txId': np.uint32, 'txPos': np.uint16, 'addressId': np.uint32, 'amount': np.uint64, 'scriptType': np.uint8}
)


# Script table/dict
scripts_dict = {0: 0, 1:153, 2:180, 3:291}



# Analisi fee rispetto a congestione
transactions_ncb = transactions[transactions['isCoinbase'] == 0].drop(columns=['blockId', 'isCoinbase'])

# Merge transactions with inputs; then calculate size of inputs
merged_tx_inputs = pd.merge(transactions_ncb, inputs.drop(columns=['prevTxId', 'prevTxPos']), on='txId', how='inner')
size_inputs = merged_tx_inputs.groupby('txId').size().reset_index(name='num_inputs')

# Merge transactions with outputs; then calculate size of outputs
merged_tx_outputs = pd.merge(transactions_ncb, outputs.drop(columns=['txPos', 'addressId']), on='txId', how='inner')
merged_tx_outputs['scriptSize'] = merged_tx_outputs['scriptType'].replace(scripts_dict)

size_outputs = merged_tx_outputs.groupby('txId').agg({'amount': 'count','scriptSize': 'sum'}).reset_index()
size_outputs.rename(columns={'amount': 'num_outputs'}, inplace=True)


# Merge the sizes with transactions
merged_transactions = pd.merge(transactions_ncb, size_inputs, on='txId', how='left')
merged_transactions = pd.merge(merged_transactions, size_outputs, on='txId', how='left')

INPUT_SIZE = 40
OUTPUT_SIZE = 9

# Calculate size of each transaction
merged_transactions['transaction_size'] = merged_transactions['num_inputs'] * INPUT_SIZE + merged_transactions['num_outputs'] * OUTPUT_SIZE + merged_transactions['scriptSize']
merged_transactions = merged_transactions.drop(columns=['num_inputs', 'num_outputs', 'scriptSize'])

print(merged_transactions)

tt = merged_transactions.groupby('timestamp').agg({'fee': 'mean', 'transaction_size': 'sum'}).reset_index()
tt = tt.rename(columns={'fee': 'avgFee', 'transaction_size': 'congestion'})

print(tt)

tt.plot.scatter(x='timestamp', y='avgFee', title='Andamento avgFee nel tempo')
tt.plot.line(x='timestamp', y='congestion', title='Andamento congestione nel tempo')
plt.show()


print(transactions_ncb.nlargest(5, 'fee'))
print(tt.nlargest(5, 'avgFee'))

'''
Come si nota dai grafici, nonostante nel tempo la congestione della blockchain sia aumentata di qualche ordine di grandezza, lo stesso non si può dire per la fee media. Nonostante alcuni outlier, generalmente è rimasta al di sotto del valore 2500
'''

# Analisi script usati in transazioni
merged_tx_outputs = pd.merge(
    transactions.drop(columns=['blockId', 'fee', 'isCoinbase']), 
    outputs.drop(columns=['txPos', 'addressId', 'amount']), 
    on='txId', how='inner')

script_groups = merged_tx_outputs.pivot_table(index='timestamp', columns='scriptType', aggfunc='size', fill_value=0).reset_index()
script_groups.columns = ['timestamp', 'scriptType_0', 'scriptType_1', 'scriptType_2', 'scriptType_3']



#script_groups.set_index('timestamp')
script_groups['timestamp'] = pd.to_datetime(script_groups['timestamp'], unit='s')
print(script_groups.info())

# downsample df
print("\ndownsampling")
script_groups = script_groups.resample('1h', on='timestamp').sum().reset_index()
print(script_groups.info())
print(script_groups)



'''script_groups = script_groups.sample(n=10, random_state=46)
print(script_groups)

plt.bar(script_groups['timestamp'], script_groups['scriptType_1'], label='scriptType_1')
plt.bar(script_groups['timestamp'], script_groups['scriptType_3'], bottom=script_groups['scriptType_1'], label='scriptType_3')

plt.legend()
plt.show()'''


# percentage

sc_pcg = script_groups
sc_pcg['total_count'] = sc_pcg[['scriptType_0', 'scriptType_1', 'scriptType_2', 'scriptType_3']].sum(axis=1)

# Calculate percentage of each script type
sc_pcg['scriptType_0_percent'] = (sc_pcg['scriptType_0'] / sc_pcg['total_count']) #* 100
sc_pcg['scriptType_1_percent'] = (sc_pcg['scriptType_1'] / sc_pcg['total_count']) #* 100
sc_pcg['scriptType_2_percent'] = (sc_pcg['scriptType_2'] / sc_pcg['total_count']) #* 100
sc_pcg['scriptType_3_percent'] = (sc_pcg['scriptType_3'] / sc_pcg['total_count']) #* 100

# Drop the total_count column
sc_pcg = sc_pcg.drop(columns=['total_count', 'scriptType_0', 'scriptType_1', 'scriptType_2', 'scriptType_3'])


sc_pcg = sc_pcg.sample(n=1500, random_state=46)
#print(sc_pcg)

sc_pcg = sc_pcg.dropna()    # hours with no transactions will produce NaN => drop
#print(f'drop nan: {sc_pcg.info()}\n{sc_pcg}')


#plt.bar(sc_pcg['timestamp'], sc_pcg['scriptType_1_percent'], label='scriptType_1')
#plt.bar(sc_pcg['timestamp'], sc_pcg['scriptType_2_percent'], bottom=sc_pcg['scriptType_1_percent'], label='scriptType_2')

fig, ax = plt.subplots(figsize=(10, 6))  # Adjust figure size as needed

ax.bar(sc_pcg['timestamp'], sc_pcg['scriptType_0_percent'], label='script 0')
ax.bar(sc_pcg['timestamp'], sc_pcg['scriptType_1_percent'], bottom=sc_pcg['scriptType_0_percent'], label='script 1')
ax.bar(sc_pcg['timestamp'], sc_pcg['scriptType_2_percent'], bottom=sc_pcg['scriptType_0_percent']+sc_pcg['scriptType_1_percent'], label='script 2')
ax.bar(sc_pcg['timestamp'], sc_pcg['scriptType_3_percent'], bottom=sc_pcg['scriptType_0_percent']+sc_pcg['scriptType_1_percent']+sc_pcg['scriptType_2_percent'], label='script 3')
#plt.xticks(rotation=45)

ax.legend(loc='upper center', ncol=2)
fig.suptitle("Andamento (relativo) degli script nel tempo")
plt.tight_layout()  # Adjust layout to prevent overlapping labels
plt.savefig(fname='script_time.png')
#plt.show()

'''
Come si osserva dal grafico, inizialmente la quasi totalità delle transazioni usava lo script di tipo 0, ma a partire da metà 2010, c'è stato un enorme switch a favore del tipo 2.
Nei primi 3 anni, gli script di tipo 0 e 3 sono praticamente assenti. 
'''