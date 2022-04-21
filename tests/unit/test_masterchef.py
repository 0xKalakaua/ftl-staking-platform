import pytest
import brownie
from brownie import network, accounts, chain, MasterChef, ArcaneRelic, MockERC721
import time

def print_tx(tx, tx_nb):
    print(tx.info())
    print(f"{tx_nb}: timestamp: {tx.timestamp}\nblock: {tx.block_number}")
    print(f"chain_timestamp: {chain.time()}")
    print("-" * 80)

@pytest.fixture
def xrlc():
    dev = accounts[0]
    xrlc = ArcaneRelic.deploy({'from': dev})
    return xrlc

@pytest.fixture
def nft_1():
    bob = accounts[1]
    max_ = 6
    nft_1 = MockERC721.deploy("First Contract", "FIRST", max_, bob, {'from': bob})

    for i in range(max_):
        nft_1.mint(f"FIRST #{i}", {'from': bob})

    nft_1.safeTransferFrom(bob, accounts[2], 3, {'from': bob})
    nft_1.safeTransferFrom(bob, accounts[2], 4, {'from': bob})
    nft_1.safeTransferFrom(bob, accounts[3], 5, {'from': bob})
    return nft_1

@pytest.fixture
def nft_2():
    alice = accounts[4]
    max_ = 6
    nft_2 = MockERC721.deploy("Second Contract", "SECOND", max_, alice, {'from': alice})
    for i in range(max_):
        tx = nft_2.mint(f"SECOND #{i}", {'from': alice})

    nft_2.safeTransferFrom(alice, accounts[5], 3, {'from': alice})
    nft_2.safeTransferFrom(alice, accounts[5], 4, {'from': alice})
    nft_2.safeTransferFrom(alice, accounts[6], 5, {'from': alice})
    return nft_2

@pytest.fixture
def masterchef_and_xrlc(xrlc):
    dev = accounts[0]
    xrlc_per_second = 7000000000000000 # 0.007 LOOT per second
    start_time = 1600000000
    end_time = 1680000000
    masterchef = MasterChef.deploy(
                                    xrlc,
                                    xrlc_per_second,
                                    start_time,
                                    end_time,
                                    {'from': dev}
                 )
    xrlc.transferOwnership(masterchef, {'from': dev})
    return masterchef, xrlc

def test_initial_state(nft_1, nft_2, masterchef_and_xrlc):
    masterchef, xrlc = masterchef_and_xrlc
    dev = accounts[0]
    bob = accounts[1]
    alice = accounts[4]

    assert xrlc.owner() == masterchef.address
    assert masterchef.owner() == dev.address

    assert nft_1.balanceOf(bob) == 3
    assert nft_1.balanceOf(accounts[2]) == 2
    assert nft_1.balanceOf(accounts[3]) == 1
    assert nft_2.balanceOf(alice) == 3
    assert nft_2.balanceOf(accounts[5]) == 2
    assert nft_2.balanceOf(accounts[6]) == 1

def test_deposit(nft_1, nft_2, masterchef_and_xrlc):
    masterchef, xrlc = masterchef_and_xrlc
    dev = accounts[0]
    bob = accounts[1]
    alice = accounts[4]

    # add nft_1 pool
    tx_1 = masterchef.add(10, nft_1, {'from': dev})
    assert masterchef.poolInfo(0)["lastRewardTime"] == tx_1.timestamp
    print_tx(tx_1, 1)

    # deposit without approval
    with brownie.reverts():
        masterchef.deposit(0, [0, 1], {'from': bob})

    # approve deposits
    nft_1.setApprovalForAll(masterchef, True, {'from': bob})
    nft_1.setApprovalForAll(masterchef, True, {'from': accounts[2]})
    nft_1.setApprovalForAll(masterchef, True, {'from': accounts[3]})
    nft_2.setApprovalForAll(masterchef, True, {'from': alice})
    nft_2.setApprovalForAll(masterchef, True, {'from': accounts[5]})
    nft_2.setApprovalForAll(masterchef, True, {'from': accounts[6]})

    # deposit to wrong pid
    with brownie.reverts():
        masterchef.deposit(1, [0, 1], {'from': bob})

    # deposit not owned tokens
    with brownie.reverts():
        masterchef.deposit(0, [2, 3], {'from': bob})
        masterchef.deposit(0, [4], {'from': bob})

    # first pool deposit, one token
    pid = 0
    chain.sleep(10)
    tx_2 = masterchef.deposit(pid, [0], {'from': bob})
    print_tx(tx_2, 2)
    acc_xrlc_per_share = masterchef.poolInfo(pid)["accXrlcPerShare"]
    assert nft_1.ownerOf(0) == masterchef.address
    assert masterchef.tokenOfOwnerByIndex(pid, bob, 0) == 0
    assert masterchef.userInfo(pid, bob.address)["amount"] == 1
    assert masterchef.userInfo(pid, bob.address)["rewardDebt"] == 0
    assert xrlc.balanceOf(bob) == 0
    assert xrlc.balanceOf(masterchef) == 0

    # add nft_2 pool
    chain.sleep(10)
    tx_3 = masterchef.add(10, nft_2, {'from': dev})
    print_tx(tx_3, 3)
    multiplier = tx_3.timestamp - tx_2.timestamp
    assert xrlc.balanceOf(masterchef) == multiplier * masterchef.xrlcPerSecond()

    # deposit multiple tokens
    pid = 1
    tx_4 = masterchef.deposit(pid, [1, 0], {'from': alice})
    print_tx(tx_4, 4)
    tx_5 = masterchef.deposit(pid, [3], {'from': accounts[5]})

    acc_xrlc_per_share = masterchef.poolInfo(pid)["accXrlcPerShare"]
    assert nft_2.ownerOf(0) == masterchef.address
    assert nft_2.ownerOf(1) == masterchef.address
    assert nft_2.ownerOf(3) == masterchef.address
    assert masterchef.tokenOfOwnerByIndex(pid, alice, 0) == 1
    assert masterchef.tokenOfOwnerByIndex(pid, alice, 1) == 0
    assert masterchef.userInfo(pid, alice.address)["amount"] == 2
    assert masterchef.userInfo(pid, alice.address)["rewardDebt"] == 0

    assert masterchef.tokenOfOwnerByIndex(pid, accounts[5], 0) == 3
    assert masterchef.userInfo(pid, accounts[5].address)["amount"] == 1
    assert masterchef.userInfo(pid, accounts[5].address)["rewardDebt"] == 1 * acc_xrlc_per_share / 1e12

    # deposit again after previous deposit
    pid = 0
    acc_xrlc_per_share_before = masterchef.poolInfo(pid)["accXrlcPerShare"]
    tx_6 = masterchef.deposit(pid, [2, 1], {'from': bob})
    multiplier = tx_6.timestamp - tx_2.timestamp
    acc_xrlc_per_share = masterchef.poolInfo(pid)["accXrlcPerShare"]
    assert nft_1.ownerOf(0) == masterchef.address
    assert nft_1.ownerOf(1) == masterchef.address
    assert nft_1.ownerOf(2) == masterchef.address
    assert masterchef.tokenOfOwnerByIndex(pid, bob, 0) == 0
    assert masterchef.tokenOfOwnerByIndex(pid, bob, 1) == 2
    assert masterchef.tokenOfOwnerByIndex(pid, bob, 2) == 1
    assert masterchef.userInfo(pid, bob.address)["amount"] == 3
    assert masterchef.userInfo(pid, bob.address)["rewardDebt"] == 3 * acc_xrlc_per_share / 1e12


    multiplier_1 = tx_3.timestamp - tx_2.timestamp
    xrlc_reward_1 = multiplier_1 * masterchef.xrlcPerSecond()
    acc_xrlc_per_share = xrlc_reward_1 * 1e12

    multiplier_2 = tx_6.timestamp - tx_3.timestamp
    xrlc_reward_2 = multiplier_2 * masterchef.xrlcPerSecond() * 0.5
    acc_xrlc_per_share += xrlc_reward_2 * 1e12
    assert xrlc.balanceOf(bob) == 1 * acc_xrlc_per_share / 1e12
    assert xrlc.balanceOf(alice) == 0
    assert xrlc.balanceOf(accounts[5]) == 0

def test_withdraw(nft_1, nft_2, masterchef_and_xrlc):
    masterchef, xrlc = masterchef_and_xrlc
    dev = accounts[0]
    bob = accounts[1]

    # add nft_1 pool
    tx_1 = masterchef.add(10, nft_1, {'from': dev})

    # approve deposits
    nft_1.setApprovalForAll(masterchef, True, {'from': bob})
    nft_1.setApprovalForAll(masterchef, True, {'from': accounts[2]})

    # deposit tokens to pool
    pid = 0
    tx_2 = masterchef.deposit(pid, [0, 1, 2], {'from': bob})


    # Full withdrawal
    chain.sleep(10)
    tx_3 = masterchef.withdraw(pid, [2, 0, 1], {'from': bob})
    assert nft_1.ownerOf(0) == bob.address
    assert nft_1.ownerOf(1) == bob.address
    assert nft_1.ownerOf(2) == bob.address
    assert xrlc.balanceOf(bob) + 1 == (tx_3.timestamp - tx_2.timestamp) * masterchef.xrlcPerSecond()

    # Partial withdrawal
    prev_balance = xrlc.balanceOf(bob)
    tx_4 = masterchef.deposit(pid, [2, 1], {'from': bob})
    chain.sleep(10)
    tx_5 = masterchef.withdraw(pid, [2], {'from': bob})

    assert nft_1.ownerOf(1) == masterchef.address
    assert nft_1.ownerOf(2) == bob.address
    multiplier = tx_5.timestamp - tx_4.timestamp
    assert xrlc.balanceOf(bob) - prev_balance == multiplier * masterchef.xrlcPerSecond()

    # Try withdrawing tokens I don't own
    with brownie.reverts("withdraw: not good"):
        tx_5 = masterchef.deposit(pid, [3], {'from': accounts[2]})
        masterchef.withdraw(pid, [1], {'from': accounts[2]})

def test_harvest(nft_1, nft_2, masterchef_and_xrlc):
    masterchef, xrlc = masterchef_and_xrlc
    dev = accounts[0]
    bob = accounts[1]
    alice = accounts[4]

    # add nft_1 and nft_2 pools
    tx_1 = masterchef.add(10, nft_1, {'from': dev})
    tx_2 = masterchef.add(10, nft_2, {'from': dev})

    # approve deposits
    nft_1.setApprovalForAll(masterchef, True, {'from': bob})
    nft_1.setApprovalForAll(masterchef, True, {'from': accounts[2]})
    nft_2.setApprovalForAll(masterchef, True, {'from': alice})
    nft_2.setApprovalForAll(masterchef, True, {'from': accounts[5]})

    # deposit tokens to pool
    pid_1 = 0
    pid_2 = 1
    tx_3 = masterchef.deposit(pid_1, [0, 1, 2], {'from': bob})
    tx_4 = masterchef.deposit(pid_1, [3, 4], {'from': accounts[2]})
    tx_5 = masterchef.deposit(pid_2, [2, 1], {'from': alice})
    tx_6 = masterchef.deposit(pid_2, [4], {'from': accounts[5]})

    # harvest on pool you don't have tokens in
    with brownie.reverts("harvest: not good"):
        masterchef.harvest(pid_2, {'from': bob})

    # harvest tokens
    chain.sleep(1000)
    chain.mine(1)

    pending_1 = masterchef.pendingXrlc(pid_1, bob) * 1e-18
    tx_7 = masterchef.harvest(pid_1, {'from': bob})
    print(f"{round(xrlc.balanceOf(bob) * 1e-18, 2)} == {round(pending_1, 2)}")
    assert round(xrlc.balanceOf(bob) * 1e-18, 2) == round(pending_1, 2)

    pending_2 = masterchef.pendingXrlc(pid_1, accounts[2]) * 1e-18
    tx_8 = masterchef.harvest(pid_1, {'from': accounts[2]})
    print(f"{round(xrlc.balanceOf(accounts[2]) * 1e-18, 2)} == {round(pending_2, 2)}")
    assert round(xrlc.balanceOf(accounts[2]) * 1e-18, 2) == round(pending_2, 2)

    pending_3 = masterchef.pendingXrlc(pid_2, alice) * 1e-18
    tx_9 = masterchef.harvest(pid_2, {'from': alice})
    print(f"{round(xrlc.balanceOf(alice) * 1e-18, 2)} == {round(pending_3, 2)}")
    assert round(xrlc.balanceOf(alice) * 1e-18, 2) == round(pending_3, 2)

    pending_4 = masterchef.pendingXrlc(pid_2, accounts[5]) * 1e-18
    tx_10 = masterchef.harvest(pid_2, {'from': accounts[5]})
    print(f"{round(xrlc.balanceOf(accounts[5]) * 1e-18, 2)} == {round(pending_4, 2)}")
    assert round(xrlc.balanceOf(accounts[5]) * 1e-18, 2) == round(pending_4, 2)

def test_add_and_set(nft_1, nft_2, masterchef_and_xrlc):
    masterchef, xrlc = masterchef_and_xrlc
    dev = accounts[0]
    bob = accounts[1]

    # allocPoint too big revert
    with brownie.reverts("add: too many alloc points!!"):
        masterchef.add(4001, nft_1, {'from': dev})

    # onlyOwner
    with brownie.reverts("Ownable: caller is not the owner"):
        masterchef.add(10, nft_1, {'from': bob})

    # add nft_1 and nft_2 pools
    tx_1 = masterchef.add(20, nft_1, {'from': dev})
    # try to add duplicate pool
    with brownie.reverts("add: pool already exists!!!!"):
        masterchef.add(10, nft_1, {'from': dev})
    tx_2 = masterchef.add(10, nft_2, {'from': dev})

    assert masterchef.totalAllocPoint() == 30
    assert masterchef.poolInfo(0)["nftToken"] == nft_1.address
    assert masterchef.poolInfo(0)["allocPoint"] == 20
    assert masterchef.poolInfo(0)["lastRewardTime"] == tx_2.timestamp
    assert masterchef.poolInfo(0)["accXrlcPerShare"] == 0

    assert masterchef.poolInfo(1)["nftToken"] == nft_2.address
    assert masterchef.poolInfo(1)["allocPoint"] == 10
    assert masterchef.poolInfo(1)["lastRewardTime"] == tx_2.timestamp
    assert masterchef.poolInfo(1)["accXrlcPerShare"] == 0

    # change the alloc_points
    tx_3 = masterchef.set(0, 5, {'from': dev})
    tx_4 = masterchef.set(1, 15, {'from': dev})

    assert masterchef.totalAllocPoint() == 20
    assert masterchef.poolInfo(0)["allocPoint"] == 5
    assert masterchef.poolInfo(0)["lastRewardTime"] == tx_4.timestamp
    assert masterchef.poolInfo(0)["accXrlcPerShare"] == 0

    assert masterchef.poolInfo(1)["allocPoint"] == 15
    assert masterchef.poolInfo(1)["lastRewardTime"] == tx_4.timestamp
    assert masterchef.poolInfo(1)["accXrlcPerShare"] == 0

def test_emergency_withdraw(nft_1, masterchef_and_xrlc):
    masterchef, xrlc = masterchef_and_xrlc
    dev = accounts[0]
    bob = accounts[1]

    # add nft_1 pool
    tx_1 = masterchef.add(10, nft_1, {'from': dev})

    # approve deposits
    nft_1.setApprovalForAll(masterchef, True, {'from': bob})
    nft_1.setApprovalForAll(masterchef, True, {'from': accounts[2]})

    # deposit tokens to pool
    pid = 0
    tx_2 = masterchef.deposit(pid, [0, 1, 2], {'from': bob})
    tx_3 = masterchef.deposit(pid, [3, 4], {'from': accounts[2]})


    # Emergency withdrawal
    chain.sleep(10)
    tx_4 = masterchef.emergencyWithdraw(pid, {'from': bob})
    print(tx_4.info())
    assert nft_1.ownerOf(0) == bob.address
    assert nft_1.ownerOf(1) == bob.address
    assert nft_1.ownerOf(2) == bob.address
    assert masterchef.userInfo(pid, bob)["amount"] == 0
    assert masterchef.userInfo(pid, bob)["rewardDebt"] == 0
    with brownie.reverts("MasterChef: owner index out of bounds"):
        masterchef.tokenOfOwnerByIndex(pid, bob, 0)
        masterchef.tokenOfOwnerByIndex(pid, bob, 1)
        masterchef.tokenOfOwnerByIndex(pid, bob, 2)
