#!/usr/bin/python3
import os
from brownie import MasterChef, accounts, network, config

def main():
    work = accounts.load("work")
    print(network.show_active())
    publish_source = True # Not supported on Testnet
    loot = "0x4A25E282A663d5d60ee558064791e35572369947"
    loot_per_second = 38600000000000000 # 0.0386 LOOT
    start_time = 1643975400
    end_time = 1643979000
    MasterChef.deploy(
            loot,
            loot_per_second,
            start_time,
            end_time,
            {"from": work},
            publish_source=publish_source
    )
