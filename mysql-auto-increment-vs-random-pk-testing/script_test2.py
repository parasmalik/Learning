import mysql.connector
import uuid
import random
import string

tuuid = 'uuid_pk7'
tseq = 'seq_pk7'
conn = mysql.connector.connect(
    host="localhost",
    user="paras.mal",
    password="password",
    database="test",
    autocommit=True
)
cur = conn.cursor()

BATCH = 100_000
TOTAL = 1_000_000   # reduce for testing

def rand_payload():
    return ''.join(random.choices(string.ascii_letters, k=2))

def rand_pk():
    return random.randint(0, 9_000_000_000_000_000_000)


rows_all2 = sorted([(rand_pk(), rand_payload()) for _ in range(TOTAL)], key=lambda x: x[0])
for i in range(0, TOTAL, BATCH):
    rows = [(rand_payload(),) for _ in range(BATCH)]
    cur.executemany(
        f"INSERT INTO {tseq} (payload) VALUES (%s)",
        rows
    )
    print("seq inserted", i)

for i in range(0, TOTAL, BATCH):
    rows = rows_all2[i: (i+BATCH)]
    
    cur.executemany(
        f"INSERT INTO {tuuid} (id, payload) VALUES (%s, %s)",
        rows
    )
    print("uuid inserted", i)



cur.execute(f'select id from {tuuid};')
        # Fetch all results from the current query
query_results = cur.fetchall()
        # Store or process the results as needed (e.g., using the query string as a key)
uuid = set([x[0] for x in query_results])
cur.execute(f'select id from {tseq};')
        # Fetch all results from the current query
query_results = cur.fetchall()
        # Store or process the results as needed (e.g., using the query string as a key)
seq = set([x[0] for x in query_results])




import csv
import json
b = 1000

import threading 
counter_lock = threading.Lock()

def insert_seq(cur, values, counter):
    
    
    c = 0
    while c == 0:
        c = c + 1
        payloads = [(rand_payload(), ) for _ in range(b)]
        cur.executemany(
            f"INSERT INTO {tseq} (payload) VALUES (%s)",
            payloads
        )
        values.update([counter + i for i in range(b)])
        counter = counter + b
    return counter


def insert_uuid(cur, values):
    
    c = 0
    while c == 0:
        c = c + 1
        r = [{'id': rand_pk(), 'p': rand_payload()} for _ in range(b)]
        cur.callproc("insert_rows_json2", [tuuid, json.dumps(r)])
        values.update([k2['id'] for k2 in r])
        


def delete_seq(cur, values):
    
    c = 0
    while c == 0:
        c = c + 1
        with counter_lock:
            r = random.sample(values, b)
            values.difference_update(r)
        r = sorted(r)
        cur.callproc("delete_by_ids_json", [tseq, json.dumps(r)])


def delete_uuid(cur, values):
    
    c = 0
    while c == 0:
        c = c + 1
        with counter_lock:
            r = random.sample(values, b)
            values.difference_update(r)
        r = sorted(r)
        cur.callproc("delete_by_ids_json", [tuuid, json.dumps(r)])



log_file = open('activity_file2.csv', mode='a', newline='') 
writer = csv.writer(log_file)
writer.writerow('table_name,data_mb,counter,op_count,pages_merged,splits,estimated_new_pages,leaf_index_pages,total_index_pages,insert_time,delete_time'.split(","))

def log_event(data):
    global writer
    writer.writerow(data)
    
    log_file.flush() 
    
logs = []


def log(name, i_merged_pages, i_splits, times):
    conn = mysql.connector.connect(
        host="localhost",
        user="paras.mal",
        password="password",
        database="test",
        autocommit=True
    )
    cur = conn.cursor()
    
    queries = [f'ANALYZE TABLE {name};',
    f"SELECT   table_name, data_length / 1024 / 1024 AS data_mb, index_length / 1024 / 1024 AS index_mb FROM information_schema.tables WHERE table_schema = 'test' and table_name = '{name}';",
    
    f"select count(1) from {name};",
    "SELECT name, count FROM information_schema.innodb_metrics WHERE name LIKE '%index_page_merge_successful%';"
    ]
    results = {}
    for query in queries:
            cur.execute(query)
            query_results = cur.fetchall()
            results[query] = query_results
            
    
    seq_pk7 = [x[1] for x in results[f"SELECT   table_name, data_length / 1024 / 1024 AS data_mb, index_length / 1024 / 1024 AS index_mb FROM information_schema.tables WHERE table_schema = 'test' and table_name = '{name}';"]] #if x[0] == tseq]
    seq_count = results[f"select count(1) from {name};"][0][0]
    merged_pages = results["SELECT name, count FROM information_schema.innodb_metrics WHERE name LIKE '%index_page_merge_successful%';"][0][1]
    f_splits = splits(cur)
    number_of_records_per_page = 430
    index = index_stats(cur, name)
    row = [name, float(seq_pk7[0]), seq_count, times[0], merged_pages-i_merged_pages, f_splits - i_splits, int((times[0] - TOTAL)/number_of_records_per_page), index['n_leaf_pages'], index['size'], times[1], times[2]] 
    
    log_event(row)
    logs.append(row)
    print(float(seq_pk7[0]), seq_count, times[0], merged_pages - i_merged_pages, f_splits - i_splits, int((times[0] - TOTAL)/number_of_records_per_page), times[1], times[2])
    

counter = max(seq) + 1
counter2 = max(seq) + 1



import time

def get_time(start_time):
    end_time = time.perf_counter()
    return end_time - start_time


def index_stats(cur, table):
        q = f"SELECT  stat_name,   stat_value FROM mysql.innodb_index_stats WHERE table_name = '{table}'   AND stat_name IN ('size', 'leaf_pages', 'n_leaf_pages');"
        cur.execute(q)
        query_results = cur.fetchall()
        leaf_pages = {x[0]:x[1] for x in query_results}
        return leaf_pages
    


def mp(cur):
    q = "SELECT name, count FROM information_schema.innodb_metrics WHERE name LIKE '%index_page_merge_successful%';"
    cur.execute(q)
    query_results = cur.fetchall()
    return query_results[0][1]



def splits(cur):
    q = "SELECT name, count FROM information_schema.innodb_metrics WHERE name LIKE '%index_page_splits%';"
    cur.execute(q)
    query_results = cur.fetchall()
    return query_results[0][1]

def run_uuid(uuid_values):
    global b
    global counter2
    curcounter = counter2
    conn = mysql.connector.connect(
        host="localhost",
        user="paras.mal",
        password="password",
        database="test",
        autocommit=True
    )
    cur = conn.cursor()
    i = 0
    merged_pages = mp(cur)
    i_splits = splits(cur)
    while i<1000:
        i = i + 1
        curcounter = curcounter + b
        start_time = time.perf_counter()
        insert_uuid(cur, uuid_values)
        i_time_uuid = get_time(start_time)
        start_time = time.perf_counter()
        delete_uuid(cur, uuid_values)
        d_time_uuid = get_time(start_time)
        log(tuuid, merged_pages, i_splits, [curcounter, i_time_uuid, d_time_uuid])

def run_seq(seq_values):
    global counter
    global b
    conn = mysql.connector.connect(
        host="localhost",
        user="paras.mal",
        password="password",
        database="test",
        autocommit=True
    )
    cur = conn.cursor()
    merged_pages = mp(cur)
    i_splits = splits(cur)
    i = 0
    while i<1000:
        i = i + 1
        with counter_lock:
            local_counter = counter
            counter += b
        
        start_time = time.perf_counter()
        insert_seq(cur, seq_values, local_counter)
        i_time_seq = get_time(start_time)
        start_time = time.perf_counter()
        delete_seq(cur, seq_values)
        d_time_seq = get_time(start_time)
    
        log(tseq, merged_pages, i_splits, [counter, i_time_seq, d_time_seq])





run_seq(seq)
run_uuid(uuid)

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("activity_file2.csv")
df["merge-split"] = df["pages_merged"] - df["splits"]

WINDOW = 50

metrics = [
    "data_mb",
    "insert_time",
    "delete_time",
    "pages_merged",
    "leaf_index_pages",
    "total_index_pages",
]

titles = [
    "Data Size (MB)",
    "Insert Time",
    "Delete Time",
    "Number of index pages merges",
    "Number of index pages (Leaf)",
    "Number of index pages (Total)"
]

fig, axes = plt.subplots(2, 3, figsize=(18, 9))
axes = axes.flatten()  # make indexing easy

tables = df.table_name.unique()

for idx, metric in enumerate(metrics):
    ax = axes[idx]

    for table in tables:
        subset = (
            df[df.table_name == table]
            .sort_values("op_count")
            .copy()
        )

        subset[titles[idx]] = subset[metric].rolling(
            window=WINDOW,
            min_periods=1
        ).mean()

        ax.plot(
            subset.op_count,
            subset[titles[idx]],
            label= "Auto-increment PK" if table == "seq_pk7" else "Random PK"
        )

    #ax.set_title(titles[idx])
    ax.set_xlabel("Operations")
    ax.set_ylabel(titles[idx])
    ax.grid(alpha=0.3)

# Hide unused subplot (9th one)
#axes[-1].axis("off")

# One legend for entire figure
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(
    handles,
    labels,
    loc="upper center",
    ncol=len(tables),
    frameon=False
)

#fig.suptitle("Rolling Average Metrics Over Time", fontsize=8, y=.98)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.show()




