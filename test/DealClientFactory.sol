// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "forge-std/Test.sol";
import "../src/DealClientFactory.sol";

contract DealClientFactoryTest is Test {
    DealClientFactory public dealClientFactory;
    bytes testCID;
    uint64 piece_size;
    string location_ref;
    uint64 car_size;

    function setUp() public {
        dealClientFactory = new DealClientFactory();
        testCID = hex"000181E2039220206B86B273FF34FCE19D6B804EFF5A3F5747ADA4EAA22F1D49C01E52DDB7875B4B";
        piece_size = 1337;
        car_size = 1337337;
        location_ref = "http://localhost/file.car";
    }

    function testMakeDealProposal() public {
        require(dealClientFactory.getDealClientLength() == 0, "Expect no deals");
        dealClientFactory.createDealRequest(testCID, piece_size, location_ref, car_size) ;
        require(dealClientFactory.getDealClientLength() == 1, "Expect one deal");
    }

}
