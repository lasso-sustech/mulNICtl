#![allow(non_snake_case)]
use std::collections::HashMap;


use ndarray::{Array1, Array2};

use crate::{action::Action, cores::prediction::LinearRegression, qos::Qos, types::paramter::HYPER_PARAMETER, CenSolver, CtlRes, CtlState, HisQos};


pub fn determine_forward_switch(his_qoses: &HisQos) -> Option<String> {
    let len = his_qoses.len();
    let start = if len >= HYPER_PARAMETER.balance_time_thres {
        len - HYPER_PARAMETER.balance_time_thres
    } else {
        0
    };
    
    // Collect all tasks from the starting point QoS.
    let tasks: Vec<String> = his_qoses[start]
        .keys()
        .cloned()
        .collect();

    // Iterate over each task to determine if switching is necessary.
    for task in tasks {
        let mut min_tx = f64::MAX;
        let mut max_tx = f64::MIN;
        let mut min_idx = start;
        let mut max_idx = start;

        // Find the minimum and maximum tx_parts for the task across the given range.
        for i in start..len {
            if let Some(qos) = his_qoses[i].get(&task) {
                let tx_part = qos.tx_parts[0];
                if tx_part < min_tx {
                    min_tx = tx_part;
                    min_idx = i;
                }
                if tx_part > max_tx {
                    max_tx = tx_part;
                    max_idx = i;
                }
            }
        }

        // Check if the difference in tx_parts exceeds the threshold.
        if max_tx - min_tx >= HYPER_PARAMETER.balance_tx_part_thres {
            let qos_min = his_qoses[min_idx]
                .get(&task)
                .expect("QoS data should be available for min_idx");
            let qos_max = his_qoses[max_idx]
                .get(&task)
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
            let rtt_diff_0 = (channel_rtts_min[0] - channel_rtts_max[0]).abs();
            let rtt_diff_1 = (channel_rtts_min[1] - channel_rtts_max[1]).abs();

            // Check if the RTT differences exceed the threshold.
            if rtt_diff_0 >= HYPER_PARAMETER.balance_rtt_thres || rtt_diff_1 >= HYPER_PARAMETER.balance_rtt_thres {
                return Some(task);
            }
        }
    }

    None
}


pub struct ForwardSwitchSolver {

}

impl ForwardSwitchSolver {
    pub fn new() -> Self {
        ForwardSwitchSolver {}
    }
}

impl CenSolver for ForwardSwitchSolver {
    fn control(&self, qoses: &HisQos, ctl_task: &String) -> CtlRes {
        // Appropriate for the back switch control
        let current_qos = qoses[qoses.len() - 1].get(ctl_task).unwrap();
        let past_qos = qoses[qoses.len() - 2].get(ctl_task).unwrap();

        let reg_vec = transform_qos_to_xy((&[past_qos, current_qos]).to_vec());

        assert!(reg_vec.len() == 2, "reg_vec must have a length of 2");
        
        let mut lr = Vec::new();
        // Do the regression
        for idx in 0..reg_vec.len() {
            let (X, y) = &reg_vec[idx];
            let mut reg = LinearRegression::new();
            reg.fit(X, y);
            lr[idx] = reg;
        }
        
        let predict = lr[0].find_min_difference_x(&lr[1]);

        let tx_parts = if predict.is_some() {
            let res = predict.unwrap();
            [res[0], res[1]]
        } else {
            [past_qos.tx_parts[0], past_qos.tx_parts[1]]
        };

        let mut controls = HashMap::new();
        controls.insert(ctl_task.clone(), Action::new(Some(tx_parts.to_vec()), None, None));
        (controls, CtlState::Normal, None)

    }
}


// Function to transform Qos vector to X and y
pub fn transform_qos_to_xy(qos_vector: Vec<&Qos>) -> Vec<(Array2<f64>, Array1<f64>)> {
    // Calculate the total number of data points
    let n_samples = qos_vector.len();
    
    // create vector to store X and y, based on the length of tx_parts
    let mut reg_vec = Vec::new();

    for idx in 0..qos_vector[0].tx_parts.len() {
        // Initialize X and y arrays
        let mut X = Array2::<f64>::zeros((n_samples, 1));
        let mut y = Array1::<f64>::zeros(n_samples);

        let mut sample_idx = 0;

        // Populate X and y
        for qos in &qos_vector {
            if let Some(channel_rtts) = &qos.channel_rtts {
                assert_eq!(qos.tx_parts.len(), channel_rtts.len(), "tx_parts and channel_rtts must have the same length");

                X[[sample_idx, 0]] = qos.tx_parts[idx];
                y[sample_idx] = channel_rtts[idx];
                sample_idx += 1;
            } else {
                panic!("channel_rtts must be Some for all Qos instances");
            }
        }

        reg_vec.push((X, y));
    }
    reg_vec

}