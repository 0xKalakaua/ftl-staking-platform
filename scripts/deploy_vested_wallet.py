#!/usr/bin/python3
import os
from pathlib import Path
from brownie import project, accounts, network, config

def main():
    work = accounts.load("work")
    print(network.show_active())
    publish_source = True # Not supported on Testnet

    VestingWallet = project.load(
            Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).VestingWallet


    beneficiary_address = "0xacB6E83F4523bc1139E4513ed5a60d435eDA7abc"
    start_timestamp = 1650834000 # Sun Apr 24 2022 21:00:00 GMT+0000
    duration = 31536000 # 365 days

    VestingWallet.deploy(
            beneficiary_address,
            start_timestamp,
            duration,
            {'from': work},
            publish_source=publish_source
    )
