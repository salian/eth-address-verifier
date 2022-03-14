import rlp
from eth_utils import keccak, to_checksum_address, to_bytes
from eth_keys import keys

from hdwallet import BIP44HDWallet
from hdwallet.derivations import BIP44Derivation
from hdwallet.cryptocurrencies import EthereumMainnet

import argparse


def parse_args():
    """ Get the command line parameters
    """
    parser = argparse.ArgumentParser(description="Verify (generate) ETH Account Address and Contract Addresses "
                                                 "from a mnemonic or private key.",
                                     epilog="© 2022 Pranab Salian - github.com/salian - All rights reserved.")
    parser.add_argument("-k", "--privatekey", help="Private Key")
    parser.add_argument("-m", "--mnemonic", help="English Mnemonic / Seed Phrase / Secret Recovery Phrase")
    return parser.parse_args()


def create_private_key_from_mnemonic(mnemonic: str) -> str:
    """ Create a private key from a mnemonic
    """
    # Initialize Ethereum mainnet BIP44HDWallet
    bip44_hdwallet: BIP44HDWallet = BIP44HDWallet(cryptocurrency=EthereumMainnet)
    # Get Ethereum BIP44HDWallet from mnemonic
    bip44_hdwallet.from_mnemonic(mnemonic=mnemonic, language="english", passphrase=None)
    # Clean default BIP44 derivation indexes/paths
    bip44_hdwallet.clean_derivation()
    # Derivation from Ethereum BIP44 derivation path
    bip44_derivation: BIP44Derivation = BIP44Derivation(cryptocurrency=EthereumMainnet,
                                                        account=0,
                                                        change=False,
                                                        address=0  # only the first address. iterate over this for more
                                                        )
    # Derive Ethereum BIP44HDWallet
    bip44_hdwallet.from_path(path=bip44_derivation)
    private_key = bip44_hdwallet.private_key()
    return private_key


def create_contract_address(sender: str, nonce: int) -> str:
    """Create a contract address using eth-utils.
    # https://ethereum.stackexchange.com/a/761/620
    """
    sender_bytes = to_bytes(hexstr=sender)
    raw = rlp.encode([sender_bytes, nonce])
    h = keccak(raw)
    address_bytes = h[12:]
    return to_checksum_address(address_bytes)


if __name__ == '__main__':

    # Run a test case using a known common address
    assert create_contract_address(to_checksum_address("0x6ac7ea33f8831ea9dcc53393aaa88b25a785dbf0"), 1) == \
           to_checksum_address("0x343c43a37d37dff08ae8c4a11544c718abb4fcf8")

    arguments = parse_args()

    if arguments.mnemonic:
        mnemonic = arguments.mnemonic
        private_key = create_private_key_from_mnemonic(mnemonic)
    elif arguments.privatekey:
        mnemonic = None
        private_key = arguments.privatekey
    else:
        # Interactive Mode
        print("Generate ETH Account Address and Contract Addresses from a mnemonic or private key.")
        unidentified_input = input("Enter a mnemonic or private key: ")
        if unidentified_input.count(' ') > 10:
            # assume the user entered a mnemonic
            mnemonic = unidentified_input
            private_key = create_private_key_from_mnemonic(mnemonic)
        else:
            mnemonic = None
            private_key = unidentified_input

    print("Mnemonic:", mnemonic)
    print("Private Key:", private_key)

    # It's pretty standard by 2022 not to prefix private keys with 0x.
    # But some old software could have prefixed 0x (like metamask before 2016)
    # so we strip 0x if present at the beginning of the private key
    if private_key[:2] == "0x":
        private_key_without_0x = private_key[2:]
    else:
        private_key_without_0x = private_key

    # Convert the private key from hex string to bytes
    private_key_bytes = bytes.fromhex(private_key_without_0x)
    assert len(private_key_bytes) == 32

    pk = keys.PrivateKey(private_key_bytes)

    # Derive a (deterministic) public key from the private key
    public_key = pk.public_key
    print("Public Key:", public_key)

    # Convert the public key to a deterministic account address (EOA)
    eoa_account_address = public_key.to_checksum_address()
    print("First Account Address:", eoa_account_address)

    # Convert an address (EOA) to its contract addresses with nonces 0 to 5
    # This is the older CREATE opcode
    print("Generating Contract Addresses using CREATE Opcode \nNonce: Contract Addresses")
    for nonce in range(6):
        contract_address = to_checksum_address(
            create_contract_address(to_checksum_address(eoa_account_address), nonce))
        print(f"{nonce}: {contract_address}")

    # Todo: accept a (list of?) 32-bit salt and display the Contract address via CREATE2 opcode
    # print("By CREATE2 Opcode \nSalt: Contract Addresses")
