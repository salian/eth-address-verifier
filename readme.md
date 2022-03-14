## ETH Address Verifier

### A Python script to verify (i.e. generate) an Ethereum Account Address and its Contract Addresses, using your recovery phrase or private key

This script allows you to enter an ethereum private key (or a mnemonic / seed phrase / secret recovery phrase) and see the generated information including Public Keys, the First Account Address and a few of its Contract Addresses.

##### What you need to know about Ethereum-style account addresses:

1. Account Addresses (EOAs) on Ethereum and ethereum-like blockchains are derived from a private key, a nonce and a derivation path.

2. Private keys can (optionally) be derived from a mnemonic, which is a string of 12 English words. It is easier to remember a mnemonic than a private key.

3. Contract Addresses are derived from Account Addresses in two ways:
   - In the "CREATE Opcode" method, Contract Addresses are derived from the Account Address and a Nonce (count of transaction)
   - In the "CREATE2 Opcode" method, Contract Addresses are derived from the Account Address and a user-supplied 32-bit Salt.

#### The derivation path:
`Mnemonic > Private Key > Public Key > Account Addresses > Contract Addresses`

#### Script Usage: 

Run this script without any parameters to enter the mnemonic or key on-screen (in interactive mode).

Alternatively use the command-line options to enter either the private key or the mnemonic.

```
usage: main.py [-h] [-k PRIVATEKEY] [-m MNEMONIC]

options:
  -h, --help            show this help message and exit
  -k PRIVATEKEY, --privatekey PRIVATEKEY
                        Private Key
  -m MNEMONIC, --mnemonic MNEMONIC
                        English Mnemonic / Seed Phrase / Secret Recovery
                        Phrase

© 2022 Pranab Salian - github.com/salian - All rights reserved.
```

### Private Key and Mnemonic Safety Considerations

Never share your Private Key or Mnemonic. This can lead to a loss of funds.

This script can be run entirely offline on your computer. 
However the private key and/or mnemonic entered may remain retrievable in RAM until a cold/hard reboot.