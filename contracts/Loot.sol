// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract Loot is ERC20Burnable, Ownable {
    constructor() ERC20("Loot Token", "LOOT") {}

    function mint(address _to, uint256 _amount) external onlyOwner {
        _mint(_to, _amount);
    }
}
