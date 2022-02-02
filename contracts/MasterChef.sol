// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./Loot.sol";

// The FTL MasterChef is a fork of MasterChef by SushiSwap
// The biggest change made is using per second instead of per block for rewards
// This is due to Fantoms extremely inconsistent block times
// The other biggest change was the removal of the migration functions
//
// Note that it's ownable and the owner wields tremendous power. The ownership
// will be transferred to a governance smart contract once c is sufficiently
// distributed and the community can show to govern itself.
//
// Have fun reading it. Hopefully it's bug-free. 
contract MasterChef is Ownable {
    using SafeMath for uint256;
    using SafeERC20 for IERC20;

    // Info of each user.
    struct UserInfo {
        mapping(uint256 => uint256) ownedTokens;
        mapping(uint256 => uint256) ownedTokensIndex;
        uint256 amount;     // How many ERC-721 tokens the user has provided.
        uint256 rewardDebt; // Reward debt. See explanation below.
        //
        // We do some fancy math here. Basically, any point in time, the amount of LOOT
        // entitled to a user but is pending to be distributed is:
        //
        //   pending reward = (user.amount * pool.accLootPerShare) - user.rewardDebt
        //
        // Whenever a user deposits or withdraws ERC-721 tokens to a pool. Here's what happens:
        //   1. The pool's `accLootPerShare` (and `lastRewardBlock`) gets updated.
        //   2. User receives the pending reward sent to his/her address.
        //   3. User's `amount` gets updated.
        //   4. User's `rewardDebt` gets updated.
    }

    // Info of each pool.
    struct PoolInfo {
        IERC721 nftToken;           // Address of NFT token contract.
        uint256 allocPoint;       // How many allocation points assigned to this pool. LOOTs to distribute per block.
        uint256 lastRewardTime;  // Last block time that LOOTs distribution occurs.
        uint256 accLootPerShare; // Accumulated LOOTs per share, times 1e12. See below.
    }

    // such a cool token!
    Loot public loot;

    // LOOT tokens created per second.
    uint256 public immutable lootPerSecond;
 
    uint256 public constant MaxAllocPoint = 4000;

    // Info of each pool.
    PoolInfo[] public poolInfo;
    // Info of each user that stakes NFT tokens.
    mapping (uint256 => mapping (address => UserInfo)) public userInfo;
    // Total allocation points. Must be the sum of all allocation points in all pools.
    uint256 public totalAllocPoint = 0;
    // The block time when LOOT mining starts.
    uint256 public immutable startTime;
    // The block time when LOOT mining stops.
    uint256 public immutable endTime;

    event Deposit(address indexed user, uint256 indexed pid, uint256[] tokenIds);
    event Withdraw(address indexed user, uint256 indexed pid, uint256[] tokenIds);
    event EmergencyWithdraw(address indexed user, uint256 indexed pid, uint256 amount);

    constructor(
        Loot _loot,
        uint256 _lootPerSecond,
        uint256 _startTime,
        uint256 _endTime
    ) {
        loot = _loot;
        lootPerSecond = _lootPerSecond;
        startTime = _startTime;
        endTime = _endTime;
    }

    function tokenOfOwnerByIndex(uint256 _pid, address owner, uint256 index)
        external
        view
        returns (uint256)
    {
        UserInfo storage user = userInfo[_pid][owner];

        require(index < user.amount, "MasterChef: owner index out of bounds");
        return user.ownedTokens[index];
    }

    // Deposit ERC-721 tokens to MasterChef for LOOT allocation.
    //function deposit(uint256 _pid, uint256 _amount) public {
        //PoolInfo storage pool = poolInfo[_pid];
        //UserInfo storage user = userInfo[_pid][msg.sender];

        //updatePool(_pid);

        //uint256 pending = user.amount.mul(pool.accLootPerShare).div(1e12).sub(user.rewardDebt);

        //user.amount = user.amount.add(_amount);
        //user.rewardDebt = user.amount.mul(pool.accLootPerShare).div(1e12);

        //if(pending > 0) {
            //safeLootTransfer(msg.sender, pending);
        //}
        //pool.nftToken.safeTransferFrom(address(msg.sender), address(this), _amount);

        //emit Deposit(msg.sender, _pid, _amount);
    //}

    // New implementation! Deposit ERC-721 tokens to MasterChef for LOOT allocation.
    function deposit(uint256 _pid, uint256[] calldata _tokenIds) external {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        mapping(uint256 => uint256) storage ownedTokens = user.ownedTokens;
        mapping(uint256 => uint256) storage ownedTokensIndex = user.ownedTokensIndex;
        uint256 amount = _tokenIds.length;
        uint256 nextTokenIndex = user.amount;

        updatePool(_pid);

        uint256 pending = user.amount.mul(pool.accLootPerShare).div(1e12).sub(user.rewardDebt);

        user.amount = user.amount.add(amount);
        user.rewardDebt = user.amount.mul(pool.accLootPerShare).div(1e12);

        if(pending > 0) {
            safeLootTransfer(msg.sender, pending);
        }

        for (uint256 i = 0; i < amount; i++) {
            uint256 tokenId = _tokenIds[i];

            ownedTokens[nextTokenIndex] = tokenId;
            ownedTokensIndex[tokenId] = nextTokenIndex;
            pool.nftToken.safeTransferFrom(address(msg.sender), address(this), tokenId);

            nextTokenIndex++;
        }

        emit Deposit(msg.sender, _pid, _tokenIds);
    }

    // Withdraw ERC-721 tokens from MasterChef.
    //function withdraw(uint256 _pid, uint256 _amount) public {  
        //PoolInfo storage pool = poolInfo[_pid];
        //UserInfo storage user = userInfo[_pid][msg.sender];

        //require(user.amount >= _amount, "withdraw: not good");

        //updatePool(_pid);

        //uint256 pending = user.amount.mul(pool.accLootPerShare).div(1e12).sub(user.rewardDebt);

        //user.amount = user.amount.sub(_amount);
        //user.rewardDebt = user.amount.mul(pool.accLootPerShare).div(1e12);

        //if(pending > 0) {
            //safeLootTransfer(msg.sender, pending);
        //}
        //pool.nftToken.safeTransfer(address(msg.sender), _amount);
        
        //emit Withdraw(msg.sender, _pid, _amount);
    //}

    // Withdraw ERC-721 tokens from MasterChef.
    function withdraw(uint256 _pid, uint256[] calldata _tokenIds) external {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        mapping(uint256 => uint256) storage ownedTokens = user.ownedTokens;
        mapping(uint256 => uint256) storage ownedTokensIndex = user.ownedTokensIndex;
        uint256 amount = _tokenIds.length;
        uint256 lastTokenIndex = user.amount - 1;
        uint256 tokenId;
        uint256 tokenIndex;

        // what would happen if I try to withdraw tokenId 0 if I don't own it
        for (uint256 i = 0; i < amount; i++) {
            tokenId = _tokenIds[i];
            tokenIndex = ownedTokensIndex[tokenId];
            require(
                ownedTokens[tokenIndex] == tokenId,
                "withdraw: not good"
            );
        }

        updatePool(_pid);

        uint256 pending = user.amount.mul(pool.accLootPerShare).div(1e12).sub(user.rewardDebt);

        user.amount = user.amount.sub(amount);
        user.rewardDebt = user.amount.mul(pool.accLootPerShare).div(1e12);

        if(pending > 0) {
            safeLootTransfer(msg.sender, pending);
        }

        for (uint256 i = 0; i < amount; i++) {
            tokenId = _tokenIds[i];
            tokenIndex = ownedTokensIndex[tokenId];

            if (tokenIndex != lastTokenIndex) {
                uint256 lastTokenId = ownedTokens[lastTokenIndex];

                ownedTokens[tokenIndex] = lastTokenId;
                ownedTokensIndex[lastTokenId] = tokenIndex;
            }

            delete ownedTokensIndex[tokenId];
            delete ownedTokens[lastTokenIndex];
            lastTokenIndex--;

            pool.nftToken.safeTransferFrom(address(this), address(msg.sender), tokenId);
        }

        emit Withdraw(msg.sender, _pid, _tokenIds);
    }

    function harvest(uint256 _pid) external {
        UserInfo storage user;
        PoolInfo storage pool;
        uint256 calc;
        uint256 pending;

        user = userInfo[_pid][msg.sender];
        pool = poolInfo[_pid];

        require(user.amount > 0, "harvest: you ain't got nothing son");

        updatePool(_pid);

        calc = user.amount.mul(pool.accLootPerShare).div(1e12);
        pending = calc.sub(user.rewardDebt);
        user.rewardDebt = calc;

        if(pending > 0) {
            safeLootTransfer(msg.sender, pending);
        }
    }

    function harvestAll() external {
        uint256 length = poolInfo.length;
        uint256 calc;
        uint256 pending;
        UserInfo storage user;
        PoolInfo storage pool;
        uint256 totalPending;

        for (uint256 pid = 0; pid < length; ++pid) {
            user = userInfo[pid][msg.sender];
            if (user.amount > 0) {
                pool = poolInfo[pid];
                updatePool(pid);

                calc = user.amount.mul(pool.accLootPerShare).div(1e12);
                pending = calc.sub(user.rewardDebt);
                user.rewardDebt = calc;

                if(pending > 0) {
                    totalPending += pending;
                }
            }
        }
        if (totalPending > 0) {
            safeLootTransfer(msg.sender, totalPending);
        }
    }


    // Add a new ERC-721 Token to the pool. Can only be called by the owner.
    function add(uint256 _allocPoint, IERC721 _nftToken) external onlyOwner {
        require(_allocPoint <= MaxAllocPoint, "add: too many alloc points!!");

        checkForDuplicate(_nftToken); // ensure you cant add duplicate pools

        massUpdatePools();

        uint256 lastRewardTime = block.timestamp > startTime ? block.timestamp : startTime;
        totalAllocPoint = totalAllocPoint.add(_allocPoint);
        poolInfo.push(PoolInfo({
            nftToken: _nftToken,
            allocPoint: _allocPoint,
            lastRewardTime: lastRewardTime,
            accLootPerShare: 0
        }));
    }

    // Update the given pool's LOOT allocation point. Can only be called by the owner.
    function set(uint256 _pid, uint256 _allocPoint) external onlyOwner {
        require(_allocPoint <= MaxAllocPoint, "add: too many alloc points!!");

        massUpdatePools();

        totalAllocPoint = totalAllocPoint - poolInfo[_pid].allocPoint + _allocPoint;
        poolInfo[_pid].allocPoint = _allocPoint;
    }

    function poolLength() external view returns (uint256) {
        return poolInfo.length;
    }

    // View function to see pending LOOTs on frontend.
    function pendingLoot(uint256 _pid, address _user) external view returns (uint256) {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][_user];
        uint256 accLootPerShare = pool.accLootPerShare;
        uint256 nftSupply = pool.nftToken.balanceOf(address(this));
        if (block.timestamp > pool.lastRewardTime && nftSupply != 0) {
            uint256 multiplier = getMultiplier(pool.lastRewardTime, block.timestamp);
            uint256 lootReward = multiplier.mul(lootPerSecond).mul(pool.allocPoint).div(totalAllocPoint);
            accLootPerShare = accLootPerShare.add(lootReward.mul(1e12).div(nftSupply));
        }
        return user.amount.mul(accLootPerShare).div(1e12).sub(user.rewardDebt);
    }

    // Update reward variables for all pools. Be careful of gas spending!
    function massUpdatePools() public {
        uint256 length = poolInfo.length;
        for (uint256 pid = 0; pid < length; ++pid) {
            updatePool(pid);
        }
    }

    // Update reward variables of the given pool to be up-to-date.
    function updatePool(uint256 _pid) public {
        PoolInfo storage pool = poolInfo[_pid];
        if (block.timestamp <= pool.lastRewardTime) {
            return;
        }
        uint256 nftSupply = pool.nftToken.balanceOf(address(this));
        if (nftSupply == 0) {
            pool.lastRewardTime = block.timestamp;
            return;
        }
        uint256 multiplier = getMultiplier(pool.lastRewardTime, block.timestamp);
        uint256 lootReward = multiplier.mul(lootPerSecond).mul(pool.allocPoint).div(totalAllocPoint);

        loot.mint(address(this), lootReward);

        pool.accLootPerShare = pool.accLootPerShare.add(lootReward.mul(1e12).div(nftSupply));
        pool.lastRewardTime = block.timestamp;
    }

    // Return reward multiplier over the given _from to _to timestamp.
    function getMultiplier(uint256 _from, uint256 _to) public view returns (uint256) {
        _from = _from > startTime ? _from : startTime;
        if (_to < startTime || _from >= endTime) {
            return 0;
        } else if (_to <= endTime) {
            return _to.sub(_from);
        } else {
            return endTime.sub(_from);
        }
    }

    // Safe LOOT transfer function, just in case if rounding error causes pool to not have enough LOOTs.
    function safeLootTransfer(address _to, uint256 _amount) private {
        uint256 lootBal = loot.balanceOf(address(this));
        if (_amount > lootBal) {
            loot.transfer(_to, lootBal);
        } else {
            loot.transfer(_to, _amount);
        }
    }

    function checkForDuplicate(IERC721 _nftToken) private view {
        uint256 length = poolInfo.length;
        for (uint256 _pid = 0; _pid < length; _pid++) {
            require(poolInfo[_pid].nftToken != _nftToken, "add: pool already exists!!!!");
        }

    }

    // Withdraw without caring about rewards. EMERGENCY ONLY.
    function emergencyWithdraw(uint256 _pid) external {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        mapping(uint256 => uint256) storage ownedTokens = user.ownedTokens;
        mapping(uint256 => uint256) storage ownedTokensIndex = user.ownedTokensIndex;
        uint256 lastTokenIndex = user.amount - 1;

        uint oldUserAmount = user.amount;
        user.amount = 0;
        user.rewardDebt = 0;

        for (uint256 i = 0; i < oldUserAmount; i++) {
            uint256 tokenId = ownedTokens[i];
            delete ownedTokensIndex[tokenId];
            delete ownedTokens[i];

            pool.nftToken.safeTransferFrom(address(this), address(msg.sender), tokenId);
        }

        emit EmergencyWithdraw(msg.sender, _pid, oldUserAmount);

    }

    // Function needed to be able to receive ERC-721 tokens
    function onERC721Received(
        address operator,
        address from,
        uint256 tokenId,
        bytes memory
    ) public returns (bytes4) {
        return this.onERC721Received.selector;
    }

}
