#!/usr/bin/python3
import os
from brownie import MockERC721, accounts, network, config

test_uri = "https://eupliqj065.execute-api.us-east-1.amazonaws.com/metadata?index=10" #auman
test_uri_2 = "ipfs://QmWEMQjjimkoAPFz913hGHPf9EtxH2hZKi6STydq7q2Hx1/1.json" #ftl

def main():
    work = accounts.load("work")
    print(network.show_active())
    publish_source = True # Not supported on Testnet
    name = "FTL Test"
    symbol = "FTL"
    max_supply = 2000
    nft = MockERC721.deploy(name, symbol, max_supply, work, {"from": work}, publish_source=publish_source)

    nft.mintMany(test_uri_2, 50)
