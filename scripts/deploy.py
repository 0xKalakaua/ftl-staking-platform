#!/usr/bin/python3
import os
from brownie import MasterChef, accounts, network, config

def main():
    work = accounts.load("work")
    print(network.show_active())
    publish_source = True # Not supported on Testnet
    xrlc = "0xE5586582E1a60E302a53e73E4FaDccAF868b459a"
    xrlc_per_second = 28063165905631659 # 0.028063165905631659 XRLC

    ### TESTING ONLY!! ### Change to ^^ before mainnet deployment
    # xrlc_per_second = 2806316591000000000 # 2.806316591 XRLC
    ### TESTING ONLY!! ###

    start_time = 1650834000
    end_time = 1682370000
    MasterChef.deploy(
            xrlc,
            xrlc_per_second,
            start_time,
            end_time,
            {"from": work},
            publish_source=publish_source
    )
