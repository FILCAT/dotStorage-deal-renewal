import "./DealClient.sol";

contract DealClientFactory{
    DealClient public dealClient;
    int64 constant public START_EPOCH = 0;
    int64 constant public END_EPOCH = 0;
    uint64 constant public STORAGE_PRICE_PER_EPOCH = 0;
    bool constant public VERIFIED_DEAL = true;
    string constant public LABEL = "";

    
    constructor() {
        dealClient = new DealClient();
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
