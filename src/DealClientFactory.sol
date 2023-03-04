import "./DealClient.sol";


contract DealClientConfig{
    bytes allowedParams =  hex"deadbeaf"; // placeholder

    function authenticateMessage(bytes calldata params) view external {
        require( keccak256(params) == keccak256(allowedParams),"params not correct"); // check place holder

        //AccountTypes.AuthenticateMessageParams memory amp = params.deserializeAuthenticateMessageParams();
        //MarketTypes.DealProposal memory proposal = deserializeDealProposal(amp.message);
        //require(pieceToProposal[proposal.piece_cid.data].valid, "piece cid must be added before authorizing");
        //require(!pieceProviders[proposal.piece_cid.data].valid, "deal failed policy check: provider already claimed this cid");
    }
}
contract DealClientFactory{
    DealClient public dealClient;
    int64 constant public START_EPOCH = 0;
    int64 constant public END_EPOCH = 0;
    uint64 constant public STORAGE_PRICE_PER_EPOCH = 0;
    bool constant public VERIFIED_DEAL = true;
    string constant public LABEL = "";

    constructor() {
        DealClientConfig dealClientConfig = new DealClientConfig();
        dealClient = new DealClient();
        dealClient.setFileCoinFunctionMap( dealClient.AUTHENTICATE_MESSAGE_METHOD_NUM() , dealClientConfig.authenticateMessage);
    }
    
    function getDealClient() public view returns (DealClient){
      return dealClient;
    }

    function getDealClientLength() public view returns (uint256){
      return dealClient.dealsLength();
    }

    function createDealRequest(bytes memory CID, uint64 piece_size, string memory location_ref, uint64 car_size) public returns (DealRequest memory) {
        //possible todo: add label as an input
        DealRequest memory request = DealRequest({
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
        dealClient.makeDealProposal(request);
    }
}
