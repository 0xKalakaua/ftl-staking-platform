#!/usr/bin/python3
import os
from brownie import ArcaneRelic, accounts, network, config

def main():
    work = accounts.load("work")
    print(network.show_active())
    publish_source = True # Not supported on Fantom Testnet
    ArcaneRelic.deploy({"from": work}, publish_source=publish_source)
