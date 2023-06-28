# Fantom Lords Staking Platform
NFT Staking Platform for the Fantom Lords. Supported collections can be staked and get rewarded in [$XRLC](https://ftmscan.com/token/0xE5586582E1a60E302a53e73E4FaDccAF868b459a) tokens.

## Contract
The contract is a fork of MasterChef by SushiSwap with 2 big changes made:
1. Using per second instead of per block for rewards. (Fantom blocks have very inconsistent block times so this makes the rewards more predictable)
2. Using ERC-721 tokens instead of ERC-20. Some major changes had to be done for this which are inspired by [Openzeppellin's ERC721Enumerable.sol](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC721/extensions/ERC721Enumerable.sol)

Also migration functions were removed because they were not needed.

## Deployment
The contract is deployed since Apr-22-2022 and has been working as intented ever since. It can be found here: https://ftmscan.com/address/0x3859530f0f88577ba84b752773804c9d56670100
