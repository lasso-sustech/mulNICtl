pub struct HyperParameter {
    pub throttle_low: f64,
    pub throttle_high: f64,
    pub backward_threshold: f64,
    pub epsilon_rtt: f64,
    pub scale_factor: f64,
    pub degration_threshold: f64,
    pub degration_tx_part_threshold: f64,
    pub wait_slots: usize,
    pub maximum_his_len: usize,
}

pub(crate) static HYPER_PARAMETER: HyperParameter = HyperParameter {
    throttle_low: 100.0,
    throttle_high: 300.0,
    backward_threshold: 0.8,
    epsilon_rtt: 0.002,
    scale_factor: 1.0,
    degration_threshold: 1.2,
    degration_tx_part_threshold: 0.8,
    wait_slots: 5,
    maximum_his_len: 10
};