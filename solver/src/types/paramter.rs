pub struct HyperParameter {
    pub throttle_low: f64,
    pub throttle_high: f64,
    pub backward_threshold: f64,
    pub epsilon_rtt: f64,
    pub scale_factor: f64,
}

pub(crate) static HYPER_PARAMETER: HyperParameter = HyperParameter {
    throttle_low: 100.0,
    throttle_high: 300.0,
    backward_threshold: 0.8,
    epsilon_rtt: 0.002,
    scale_factor: 1.0,
};