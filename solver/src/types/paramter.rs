pub struct HyperParameter<'a> {
    pub throttle_low: f64,
    pub throttle_high: f64,
    pub backward_threshold: f64,
    pub epsilon_rtt: f64,
    pub scale_factor: f64,
    pub degration_threshold: f64,
    pub degration_tx_part_threshold: f64,
    pub wait_slots: usize,
    pub maximum_his_len: usize,
    pub ports_tobe_pop: [&'a str; 3],
}

pub(crate) static HYPER_PARAMETER: HyperParameter = {
    let throttle_high = 300.0;
    let throttle_low = throttle_high * 0.7;
    HyperParameter {
        throttle_low,
        throttle_high,
        backward_threshold: 0.8,
        epsilon_rtt: 0.002,
        scale_factor: 1.0,
        degration_threshold: 1.2,
        degration_tx_part_threshold: 0.8,
        wait_slots: 5,
        maximum_his_len: 10,
        ports_tobe_pop: ["6209@192", "6210@192", "6211@192"],
    }
};
