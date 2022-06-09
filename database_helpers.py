import os
import sqlite3

# Kompromat db
KEYSTORE = 'keystore.db'


def create_keystore_database(database='keystore.db'):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    # SQLite has INTEGER, REAL, TEXT, and BLOB. No BOOLEAN is available
    # Avoid "id" as it is a keyword in Python.
    table_creation_sql = 'CREATE TABLE active_addresses (' \
                         'UID INTEGER PRIMARY KEY AUTOINCREMENT, ' \
                         'MNEMONIC TEXT DEFAULT NULL, ' \
                         'PRIVATE_KEY TEXT NOT NULL, ' \
                         'ADDRESS TEXT NOT NULL, ' \
                         'NONCE INTEGER NOT NULL, ' \
                         'IS_CONTRACT INTEGER DEFAULT NULL, ' \
                         'NETWORK_COUNT INTEGER DEFAULT NULL, ' \
                         'NETWORKS TEXT DEFAULT NULL, ' \
                         'ETH_BALANCE TEXT DEFAULT NULL,' \
                         'ETH_TOKENS_BALANCE TEXT DEFAULT NULL,' \
                         'BNB_BALANCE TEXT DEFAULT NULL,' \
                         'BNB_TOKENS_BALANCE TEXT DEFAULT NULL,' \
                         'MATIC_BALANCE TEXT DEFAULT NULL,' \
                         'MATIC_TOKENS_BALANCE TEXT DEFAULT NULL,' \
                         'ETC_BALANCE TEXT DEFAULT NULL,' \
                         'ETC_TOKENS_BALANCE TEXT DEFAULT NULL,' \
                         'UNIQUE(PRIVATE_KEY, ADDRESS)' \
                         ')'
    cursor.execute(table_creation_sql)
    print("Table created successfully")
    conn.close()


def add_to_keystore(mnemonic, private_key, interesting_addresses):
    # create DB if not exists
    if not os.path.exists(KEYSTORE):
        create_keystore_database(KEYSTORE)

    print(interesting_addresses)
    conn = sqlite3.connect(KEYSTORE)
    cursor = conn.cursor()
    print(f"\nSaving to {KEYSTORE}")
    for address_data in interesting_addresses:
        if (address_data['balance'] != '0') or (address_data['network_count'] != 0):
            # We have an interesting account with balance or presence on other networks
            if address_data['type'] == 'A':
                is_contract = 0
            elif address_data['type'] == 'C':
                is_contract = 1
            else:
                is_contract = None
            try:
                cursor.execute("INSERT INTO active_addresses "
                               "(MNEMONIC, PRIVATE_KEY, ADDRESS, NONCE, IS_CONTRACT, NETWORK_COUNT, NETWORKS, ETH_BALANCE) "
                               "VALUES (?,?,?,?,?,?,?,?)",
                               [mnemonic,
                                # private_key,
                                address_data['private_key'],
                                address_data['address'],
                                address_data['nonce'],
                                is_contract,
                                address_data['network_count'],
                                address_data['networks'],
                                address_data['balance']
                                ]
                               )
                print(f"{address_data['address'][0:7]}... saved.")
            except sqlite3.IntegrityError as err:
                # print(f"{address_data['address']} with {private_key} was already present in keystore.")
                print(f"Skipping {address_data['address'][0:7]}... already present. ")
    conn.commit()
    conn.close()

    return True
