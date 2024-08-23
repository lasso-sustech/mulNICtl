use std::collections::HashMap;

use crate::{state::Color, types::{parameter::HYPER_PARAMETER, qos::Qos}, HisQos};

pub fn is_degration( channel_rtt: &Vec<f64>,  tx_parts: &Vec<f64>, rtt: f64) -> bool{
    let reference_rtt = channel_rtt[0] * HYPER_PARAMETER.degration_threshold;
    if tx_parts[0] >= HYPER_PARAMETER.degration_tx_part_threshold && rtt > reference_rtt{
        true
    }
    else{
        false
    }
}

pub fn is_his_back_ever(his_qoses: &HisQos, task: &String) -> bool {
    let len = his_qoses.len();
    let start = if len >= HYPER_PARAMETER.his_back_time {
        len - HYPER_PARAMETER.his_back_time
    } else {
        0
    };

    // Find the minimum and maximum tx_parts for the task across the given range.
    for i in start..len {
        if let Some(qos) = his_qoses[i].get(task) {
            if qos.tx_parts.iter().any(|&tx_part| tx_part != 0.0 && tx_part != 1.0) {
                return true;
            }
        }
    }
    false
}

pub fn is_adaptation(channel_rtts: &Vec<f64>, channel_colors: &Vec<Color>) -> bool {
    let mut res = true;
    // if color is [red, green] or [green, red], then the adpation is feasible only if the corresponding channel_rtt has same order
    if channel_colors[0] > channel_colors[1] && channel_rtts[0] < channel_rtts[1] {
        res = false;
    }
    else if channel_colors[0] < channel_colors[1] && channel_rtts[0] > channel_rtts[1] {
        res = false;
    }
    return res;
} 

pub fn is_stay_in_channel(tx_parts: &Vec<f64>, channel_colors: &Vec<Color>) -> bool {
    if tx_parts[0] == 1.0 && channel_colors[0] == Color::Green {
        return true;
    }
    if tx_parts[1] == 0.0 && channel_colors[1] == Color::Green {
        return true;
    }
    false
}

pub fn determine_forward_switch(his_qoses: &HisQos, task: &String) -> bool {
    let len = his_qoses.len();
    let start = if len >= HYPER_PARAMETER.balance_time_thres {
        len - HYPER_PARAMETER.balance_time_thres
    } else {
        0
    };
    
    // Iterate over each task to determine if switching is necessary.
    let mut min_tx = f64::MAX;
    let mut max_tx = f64::MIN;
    let mut min_idx = start;
    let mut max_idx = start;

    // Find the minimum and maximum tx_parts for the task across the given range.
    for i in start..len {
        if let Some(qos) = his_qoses[i].get(task) {
            let tx_part = qos.tx_parts[0];
            if tx_part < min_tx {
                min_tx = tx_part;
                min_idx = i;
            }
            if tx_part >= max_tx {
                max_tx = tx_part;
                max_idx = i;
            }
        }
    }

    // Check if the difference in tx_parts exceeds the threshold.
    if max_tx - min_tx >= HYPER_PARAMETER.balance_tx_part_thres {
        let qos_min = his_qoses[min_idx]
            .get(task)
            .expect("QoS data should be available for min_idx");
        let qos_max = his_qoses[max_idx]
            .get(task)
            .expect("QoS data should be available for max_idx");

        // Ensure both QoS have channel_rtts.
        let channel_rtts_min = qos_min
            .channel_rtts
            .as_ref()
            .expect("channel_rtts must be Some for all Qos instances");
        let channel_rtts_max = qos_max
            .channel_rtts
            .as_ref()
            .expect("channel_rtts must be Some for all Qos instances");

        // Calculate the RTT differences for the channels.
        let rtt_diff_0 = channel_rtts_min[0] - channel_rtts_max[0]; // min - max
        let rtt_diff_1 = channel_rtts_min[1] - channel_rtts_max[1]; // max - min

        if rtt_diff_0 < 0.0 && rtt_diff_1 > 0.0 {
            if rtt_diff_0.abs() >= HYPER_PARAMETER.balance_rtt_thres || rtt_diff_1.abs() >= HYPER_PARAMETER.balance_rtt_thres {
                return true;
            }
        }
    }

    false
}

pub fn determine_back_switch(qoses: &HashMap<String, Qos>, alpha: f64) -> Option<&String>{
    let mut back_switch_task = None;
    for (name, qos) in qoses {
        if let Some(channel_rtts) = qos.channel_rtts.clone() {
            let tx_parts = qos.tx_parts.clone();
            let tx_parts = vec![tx_parts[0], 1.0 - tx_parts[1]];
            let target_rtt = qos.target_rtt;
        
            if tx_parts.iter().any(|&tx_part| tx_part == 0.0 || tx_part == 1.0) {
                continue;
            }

            let res:Vec<bool> = tx_parts.into_iter().zip(channel_rtts.into_iter()).map(|(tx_part, channel_rtt)| {
                if channel_rtt <= target_rtt * alpha * tx_part {
                    true
                }
                else{
                    false
                }
            }).collect();
        
            if res.into_iter().any(|x| x) {
                back_switch_task = Some(name);
            }
        }
    }
    back_switch_task
}