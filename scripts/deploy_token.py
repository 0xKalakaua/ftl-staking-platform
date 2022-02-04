#!/usr/bin/python3
import os
from brownie import Loot, accounts, network, config

def main():
    work = accounts.load("work")
    print(network.show_active())
    publish_source = True # Not supported on Fantom Testnet
    Loot.deploy({"from": work}, publish_source=publish_source)
