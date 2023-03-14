// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

import "./DealClient.sol";
import {CommonTypes} from "@zondax/filecoin-solidity/contracts/v0.8/types/CommonTypes.sol";
import {FilAddresses} from "@zondax/filecoin-solidity/contracts/v0.8/utils/FilAddresses.sol";
import {MarketTypes} from "@zondax/filecoin-solidity/contracts/v0.8/types/MarketTypes.sol";

contract DealClientStorageRenewal is DealClient {
    using AccountCBOR for *;
    using MarketCBOR for *;

    // 2023-03-25 00:00:00 UTC
    int64 public constant START_EPOCH = 2713200;
    // 2713200 + 500 * 2880
    int64 public constant END_EPOCH = 4153200;
    uint64 public constant STORAGE_PRICE_PER_EPOCH = 0;
    bool public constant VERIFIED_DEAL = true;
    uint64[] DEFAULT_VERIFIED_SPS = [1036, 1648];

    uint256 MIN_PROVIDER_COLLATERAL = 12000000000000000;

    mapping(bytes => bool) public verifiedSPs;

    constructor() {
        setDefaultVerifiedSPs();
    }

    function isZero(CommonTypes.BigInt memory a) internal pure returns (bool) {
        CommonTypes.BigInt memory Zero = CommonTypes.BigInt(hex"00", false);
        return compareBigInts(a, Zero);
    }

    function compareBigInts(
        CommonTypes.BigInt memory a,
        CommonTypes.BigInt memory b
    ) internal pure returns (bool) {
        return keccak256(a.val) == keccak256(b.val) && a.neg == b.neg;
    }

    function compareStrings(
        string memory a,
        string memory b
    ) internal pure returns (bool) {
        return (keccak256(abi.encodePacked(a)) ==
            keccak256(abi.encodePacked(b)));
    }

    function authenticateMessage(bytes memory params) internal view override {
        require(
            msg.sender == MARKET_ACTOR_ETH_ADDRESS,
            "msg.sender needs to be market actor f05"
        );

        AccountTypes.AuthenticateMessageParams memory amp = params
            .deserializeAuthenticateMessageParams();
        MarketTypes.DealProposal memory proposal = deserializeDealProposal(
            amp.message
        );

        bytes memory pieceCid = proposal.piece_cid.data;
        require(
            pieceToProposal[pieceCid].valid,
            "piece cid must be added before authorizing"
        );
        require(
            !pieceProviders[pieceCid].valid,
            "deal failed policy check: provider already claimed this cid"
        );

        //check deal params are correct
        require(
            VERIFIED_DEAL == proposal.verified_deal,
            "Deal verified incorrect"
        );

        require(proposal.start_epoch == START_EPOCH, "Start epoch incorrect");
        require(proposal.end_epoch == END_EPOCH, "End epoch incorrect");
        require(
            isZero(proposal.storage_price_per_epoch),
            "Storage price incorrect"
        );
        require(
            bigIntToUint(proposal.provider_collateral) ==
                MIN_PROVIDER_COLLATERAL,
            "Provider collateral incorrect"
        );
        require(
            isZero(proposal.client_collateral),
            "Client collateral incorrect"
        );

        //check for valid SPs
        require(isVerifiedSP(proposal.provider), "SP not verified");
    }

    function isVerifiedSP(
        CommonTypes.FilAddress memory actor
    ) public view returns (bool) {
        return verifiedSPs[actor.data];
    }

    function isVerifiedSP(uint64 actorId) public view returns (bool) {
        return verifiedSPs[getBytes(actorId)];
    }

    function getBytes(uint64 actorId) internal pure returns (bytes memory) {
        CommonTypes.FilAddress memory a = FilAddresses.fromActorID(actorId);
        return a.data;
    }

    function changeMINPROVIDERCOLLATERAL(uint256 min) public onlyOwner {
        MIN_PROVIDER_COLLATERAL = min;
    }

    function addVerifiedSP(uint64 actorId) public onlyOwner {
        verifiedSPs[getBytes(actorId)] = true;
    }

    function addVerifiedSPs(uint64[] memory minerIds) public onlyOwner {
        for (uint i = 0; i < minerIds.length; i++) {
            addVerifiedSP(minerIds[i]);
        }
    }

    function deleteSP(uint64 _actorID) public onlyOwner {
        require(verifiedSPs[getBytes(_actorID)] == true, "SP not found");
        delete verifiedSPs[getBytes(_actorID)];
    }

    function setDefaultVerifiedSPs() internal {
        for (uint256 i = 0; i < DEFAULT_VERIFIED_SPS.length; i++) {
            uint64 actorId = DEFAULT_VERIFIED_SPS[i];
            addVerifiedSP(actorId);
        }
    }

    function createDealRequests(
        bytes[] memory CIDs,
        uint64[] memory piece_sizes,
        string[] memory location_refs,
        uint64[] memory car_sizes,
        string[] memory labels
    ) public returns (DealRequest[] memory) {
        //ensure all arrays have same length
        uint len = CIDs.length;
        require(
            len == piece_sizes.length,
            "Piece sizes length not equal to CIDs"
        );
        require(
            len == location_refs.length,
            "Location Refs length not equal to CIDs"
        );
        require(len == car_sizes.length, "Car Sizes length not equal to CIDs");
        DealRequest[] memory ret = new DealRequest[](len);
        //loop through requests and call createDealRequest
        for (uint256 i = 0; i < CIDs.length; i++) {
            ret[i] = createDealRequest(
                CIDs[i],
                piece_sizes[i],
                location_refs[i],
                car_sizes[i],
                labels[i]
            );
        }
        return ret;
    }

    function createDealRequest(
        bytes memory CID,
        uint64 piece_size,
        string memory location_ref,
        uint64 car_size,
        string memory labelCID
    ) public returns (DealRequest memory) {
        //possible todo: add label as an input
        DealRequest memory request = DealRequest({
            piece_cid: CID,
            piece_size: piece_size,
            verified_deal: VERIFIED_DEAL,
            label: labelCID,
            start_epoch: START_EPOCH,
            end_epoch: END_EPOCH,
            storage_price_per_epoch: STORAGE_PRICE_PER_EPOCH,
            provider_collateral: MIN_PROVIDER_COLLATERAL,
            client_collateral: 0,
            extra_params_version: 0,
            extra_params: ExtraParamsV1({
                location_ref: location_ref,
                car_size: car_size,
                skip_ipni_announce: false,
                remove_unsealed_copy: false
            })
        });
        makeDealProposal(request);
    }

    function withdrawBalance(
        address client,
        uint256 value
    ) public override onlyOwner returns (uint) {
        revert("withdrawBalance: Contract not payable");
    }

    function addBalance(uint256 value) public override onlyOwner {
        revert("addBalance: Contract not payable");
    }
}
