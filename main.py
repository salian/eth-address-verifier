import rlp
from eth_utils import keccak, to_checksum_address, to_bytes
from eth_keys import keys

from hdwallet import BIP44HDWallet
from hdwallet.derivations import BIP44Derivation
from hdwallet.cryptocurrencies import EthereumMainnet

from colorama import init, Fore, Back, Style

import argparse

from etherscan_helpers import get_eth_balance_multiple_with_retries
import database_helpers
import blockchainscan_helpers


def blockscan_url(wallet_address: str) -> str:
    return "https://blockscan.com/address/" + wallet_address


def parse_args():
    """ Get the command line parameters
    """
    parser = argparse.ArgumentParser(description="Verify (generate) ETH Account Address and Contract Addresses "
                                                 "from a mnemonic or private key.",
                                     epilog="© 2022 Pranab Salian - github.com/salian - All rights reserved.")
    parser.add_argument("-k", "--privatekey", help="Private Key")
    parser.add_argument("-m", "--mnemonic", help="English Mnemonic / Seed Phrase / Secret Recovery Phrase")
    return parser.parse_args()


def create_private_keys_from_mnemonic(mnemonic: str, passphrase=None, nonce_start: int = 0, nonce_count: int = 1) -> list[str]:
    """ Create a private key from a mnemonic
    """
    # Initialize Ethereum mainnet BIP44HDWallet
    bip44_hdwallet: BIP44HDWallet = BIP44HDWallet(cryptocurrency=EthereumMainnet)
    # Get Ethereum BIP44HDWallet from mnemonic
    bip44_hdwallet.from_mnemonic(mnemonic=mnemonic, language="english", passphrase=passphrase)

    private_key_list = []

    for nonce in range(nonce_start, nonce_start + nonce_count):
        # Clean default BIP44 derivation indexes/paths
        bip44_hdwallet.clean_derivation()
        # Derivation from Ethereum BIP44 derivation path
        bip44_derivation: BIP44Derivation = BIP44Derivation(cryptocurrency=EthereumMainnet,
                                                            account=0,
                                                            change=False,
                                                            address=nonce  # iterate over the nonces for HD addresses
                                                            )
        # Derive Ethereum BIP44HDWallet
        bip44_hdwallet.from_path(path=bip44_derivation)
        print(f"account path = {bip44_derivation}")
        private_key = bip44_hdwallet.private_key()
        print(f"private_key = {private_key}")
        private_key_list.append(private_key)

    return private_key_list


def create_contract_address(sender: str, nonce: int) -> str:
    """Create a contract address using eth-utils.
    # https://ethereum.stackexchange.com/a/761/620
    """
    sender_bytes = to_bytes(hexstr=sender)
    raw = rlp.encode([sender_bytes, nonce])
    h = keccak(raw)
    address_bytes = h[12:]
    return to_checksum_address(address_bytes)


def derive_all_addresses(private_key_list, nonce_start=0):
    global private_key_without_0x
    # global all_addresses, private_key_without_0x, public_key
    all_addresses = []
    for counter, private_key in enumerate(private_key_list):
        nonce = counter + nonce_start
        if private_key[:2] == "0x":
            # It's pretty standard by 2022 not to prefix private keys with 0x.
            # But some old software could have prefixed 0x (like metamask before 2016)
            # so we strip 0x if present at the beginning of the private key
            private_key_without_0x = private_key[2:]
        else:
            private_key_without_0x = private_key

        # Convert the private key from hex string to bytes
        private_key_bytes = bytes.fromhex(private_key_without_0x)
        if len(private_key_bytes) != 32:
            print(f"Private Key length is {len(private_key_bytes)} bytes but should be 32 bytes")
            assert len(private_key_bytes) == 32

        pk = keys.PrivateKey(private_key_bytes)

        # Derive a (deterministic) public key from the private key
        public_key = pk.public_key
        print(f"Private Key {nonce}:", Style.NORMAL + Back.BLACK + Fore.LIGHTRED_EX + private_key_without_0x)
        print(f"Public Key {nonce}:", public_key)

        # Convert the public key to a deterministic account address (EOA)
        eoa_account_address = public_key.to_checksum_address()
        # print("First Account Address:", eoa_account_address)
        # Colorama Quick Colors Reference
        # Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
        # Back: BLACK, RED, WHITE, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
        # Style: DIM, NORMAL, BRIGHT, RESET_ALL
        print(f"Account Address {nonce}:", Style.NORMAL + Back.RESET + Fore.LIGHTCYAN_EX + eoa_account_address)
        network_count, network_data = blockchainscan_helpers.blockchainscan_networks(eoa_account_address)
        all_addresses.append({'address': eoa_account_address,
                              'type': 'A',  # A for Account
                              'nonce': nonce,
                              'private_key': private_key_without_0x,
                              'network_count': network_count,
                              'networks': ','.join([network['network'] for network in network_data])
                              })

        # Convert an address (EOA) to its contract addresses with nonces 0 to 5
        # This is the older CREATE opcode
        # print("Generating Contract Addresses using CREATE Opcode \nNonce: Contract Addresses")
        for contract_nonce in range(3):
            contract_address = to_checksum_address(
                create_contract_address(to_checksum_address(eoa_account_address), contract_nonce))
            # print(f"{nonce}: {contract_address}")
            network_count, network_data = blockchainscan_helpers.blockchainscan_networks(contract_address)

            all_addresses.append({'address': contract_address,
                                  'type': 'C',  # C for contract
                                  'nonce': contract_nonce,
                                  'private_key': private_key_without_0x,
                                  'network_count': network_count,
                                  'networks': ','.join([network['network'] for network in network_data])
                                  })
    return all_addresses


def derive_all_addresses_and_balances(all_addresses):
    global positive_account_count, network_presence_count, all_addresses_and_balances
    address_list = [address_dict['address'] for address_dict in all_addresses]
    address_balances = get_eth_balance_multiple_with_retries(address_list, eth=None)
    positive_account_count = len([account for account in address_balances if account['balance'] != '0'])
    network_presence_count = len([account for account in all_addresses if account['network_count'] != 0])
    all_addresses_and_balances = []
    address_key_dict = dict((address_dict['account'], address_dict) for address_dict in address_balances)
    # print(address_key_dict)
    for address_dict in all_addresses:
        address_with_balance = {'type': address_dict['type'],
                                'address': address_dict['address'],
                                'private_key': address_dict['private_key'],
                                'nonce': address_dict['nonce'],
                                'balance': address_key_dict[address_dict['address']]['balance'],
                                'network_count': address_dict['network_count'],
                                'networks': address_dict['networks']
                                }
        all_addresses_and_balances.append(address_with_balance)

    return all_addresses_and_balances, positive_account_count, network_presence_count


def pretty_print_interesting_addresses(all_addresses_and_balances):
    print("\nETH Address Balances for",
          Style.BRIGHT + Back.RESET + Fore.LIGHTCYAN_EX + "accounts",
          "(A) and",
          Style.NORMAL + Back.RESET + Fore.LIGHTBLUE_EX + "contracts",
          "(C)")
    print(
        Style.BRIGHT + Back.RESET + Fore.WHITE + "  T N Address                                    B                       N")
    for address_balance_data in all_addresses_and_balances:
        if (address_balance_data['balance'] != '0') or (address_balance_data['network_count'] != 0):
            # colored display for interesting addresses
            balance_string = Style.NORMAL + Back.RESET + Fore.LIGHTGREEN_EX + address_balance_data['balance']
            highlight_string = Style.DIM + Back.RESET + Fore.YELLOW + "★"
        else:
            # plain balance display
            balance_string = Style.NORMAL + Back.RESET + Fore.RESET + address_balance_data['balance']
            highlight_string = " "

        if address_balance_data['type'] == 'A':
            print(highlight_string,
                  address_balance_data['type'], address_balance_data['nonce'],
                  Style.NORMAL + Back.RESET + Fore.LIGHTCYAN_EX + address_balance_data['address'],
                  '{:>34}'.format(balance_string), "WEI",
                  address_balance_data['network_count'],
                  blockscan_url(address_balance_data['address']))
        elif address_balance_data['type'] == 'C':
            print(highlight_string,
                  address_balance_data['type'], address_balance_data['nonce'],
                  Style.NORMAL + Back.RESET + Fore.LIGHTBLUE_EX + address_balance_data['address'],
                  '{:>34}'.format(balance_string), "WEI",
                  address_balance_data['network_count'],
                  blockscan_url(address_balance_data['address']))


if __name__ == '__main__':

    # Run a test case using a known common address
    assert create_contract_address(to_checksum_address("0x6ac7ea33f8831ea9dcc53393aaa88b25a785dbf0"), 1) == \
           to_checksum_address("0x343c43a37d37dff08ae8c4a11544c718abb4fcf8")

    arguments = parse_args()

    # Initializes Colorama
    init(autoreset=True)

    if arguments.mnemonic:
        mnemonic = arguments.mnemonic
        nonce_start = arguments.nonce_start
        nonce_count = arguments.nonce_count
        private_key_list = create_private_keys_from_mnemonic(mnemonic, nonce_start=0, nonce_count=3)
    elif arguments.privatekey:
        mnemonic = None
        nonce_start = 0
        private_key_list = list(arguments.privatekey)
    else:
        # Interactive Mode
        print("Generate ETH Account Address and Contract Addresses from a mnemonic or private key.")
        print("                                 |--------------------------------------------------------------|")
        unidentified_input = input("Enter a mnemonic or private key: ")
        if unidentified_input.count(' ') > 10:
            # assume the user entered a mnemonic if there are more than 10 spaces
            mnemonic = unidentified_input
            nonce_start = int(input("Start nonce from (Enter for 0):") or "0")
            passphrase = str(input("Optional Passphrase (Enter to skip):"))
            if len(passphrase) < 1:
                passphrase = None  # Important; this cannot be empty string
            private_key_list = create_private_keys_from_mnemonic(mnemonic, passphrase, nonce_start=nonce_start, nonce_count=5)
        else:
            mnemonic = None
            nonce_start = 0
            private_key_list = [unidentified_input]

    print("Mnemonic:", mnemonic)
    # print("Private Key:", Style.NORMAL + Back.BLACK + Fore.LIGHTRED_EX + private_key_list[0])

    all_addresses = derive_all_addresses(private_key_list)

    # Todo: accept a (list of?) 32-bit salt and display the Contract address via CREATE2 opcode
    # print("By CREATE2 Opcode \nSalt: Contract Addresses")

    all_addresses_and_balances, positive_account_count, network_presence_count = derive_all_addresses_and_balances(all_addresses)

    pretty_print_interesting_addresses(all_addresses_and_balances)

    # Save to Database
    if positive_account_count or network_presence_count:
        database_helpers.add_to_keystore(mnemonic, private_key_without_0x, all_addresses_and_balances)

