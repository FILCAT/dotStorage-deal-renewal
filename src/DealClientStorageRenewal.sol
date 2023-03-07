import "./DealClient.sol";
import {
    CommonTypes
} from "@zondax/filecoin-solidity/contracts/v0.8/types/CommonTypes.sol";

contract DealClientStorageRenewal is DealClient {
    int64 public constant START_EPOCH = 0;
    int64 public constant END_EPOCH = 0;
    uint64 public constant STORAGE_PRICE_PER_EPOCH = 0;
    bool public constant VERIFIED_DEAL = true;
    string public constant LABEL = "";
    uint64[] DEFAULT_VERIFIED_SPS = [4, 5, 6];

    mapping(CommonTypes.FilActorId => bool) public verifiedSPs;

    constructor() {
        setDefaultVerifiedSPs();
    }


    function isVerifiedSPUint64(uint64 actorId)
        public
        view
        returns (bool)
    {
        CommonTypes.FilActorId a = CommonTypes.FilActorId.wrap(actorId);
        return isVerifiedSP(a);
    }

    function isVerifiedSP(CommonTypes.FilActorId actorId)
        public
        view
        returns (bool)
    {
        return verifiedSPs[actorId];
    }

    function addVerifiedSP(CommonTypes.FilActorId actorId)
        public
        onlyOwner
    {
        verifiedSPs[actorId] = true;
    }

    function deleteSP(CommonTypes.FilActorId _actorID) public onlyOwner {
        require(verifiedSPs[_actorID] == true, "SP not found");
        delete verifiedSPs[_actorID];
    }

    function setDefaultVerifiedSPs() internal {
        for (uint256 i = 0; i < DEFAULT_VERIFIED_SPS.length; i++) {
            CommonTypes.FilActorId actorId =
                CommonTypes.FilActorId.wrap(DEFAULT_VERIFIED_SPS[i]);
            addVerifiedSP(actorId);
        }
    }

    function authenticateMessage(bytes memory params) internal view override {
        bytes memory allowedParams = hex"deadbeaf"; // placeholder

        require(
            keccak256(params) == keccak256(allowedParams),
            "params not correct"
        ); // check place holder

        //todo learn format of params and get actor id from params
        CommonTypes.FilActorId params_actor_id = CommonTypes.FilActorId.wrap(5);
        require(
            isVerifiedSP(params_actor_id),
            "Actor id is not a verified SP in this contract"
        );

        //AccountTypes.AuthenticateMessageParams memory amp = params.deserializeAuthenticateMessageParams();
        //MarketTypes.DealProposal memory proposal = deserializeDealProposal(amp.message);
        //require(pieceToProposal[proposal.piece_cid.data].valid, "piece cid must be added before authorizing");
        //require(!pieceProviders[proposal.piece_cid.data].valid, "deal failed policy check: provider already claimed this cid");
    }

    function createDealRequest(
        bytes memory CID,
        uint64 piece_size,
        string memory location_ref,
        uint64 car_size
    ) public returns (DealRequest memory) {
        //possible todo: add label as an input
        DealRequest memory request =
            DealRequest({
                piece_cid: CID,
                piece_size: piece_size,
                verified_deal: VERIFIED_DEAL,
                label: LABEL,
                start_epoch: START_EPOCH,
                end_epoch: END_EPOCH,
                storage_price_per_epoch: STORAGE_PRICE_PER_EPOCH,
                provider_collateral: 0,
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
}
