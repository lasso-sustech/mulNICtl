use crate::types::paramter::HYPER_PARAMETER;

pub fn check_degration( channel_rtt: &Vec<f64>,  tx_parts: &Vec<f64>, rtt: f64) -> bool{
    let reference_rtt = channel_rtt[0] * HYPER_PARAMETER.degration_threshold;
    if tx_parts[0] >= HYPER_PARAMETER.degration_tx_part_threshold && rtt > reference_rtt{
        false
    }
    else{
        true
    }
}