#!/usr/bin/python3
import os
from brownie import MockERC721, accounts, network, config

ape_uri = "https://opensea.mypinata.cloud/ipfs/QmeSjSinHpPnmXmspMjwiXyN6zS4E9zccariGR3jxcaWtq/7885"

def main():
    work = accounts.load("work")
    print(network.show_active())
    publish_source = True # Not supported on Testnet
    name = "FTL 2"
    symbol = "FTL2"
    max_supply = 10
    nft = MockERC721.deploy(name, symbol, max_supply, work, {"from": work}, publish_source=publish_source)

    for i in range(max_supply):
        nft.mint(ape_uri)
