use std::collections::HashMap;


use ndarray::{Array, Array1, Array2};

use crate::{action::Action, cores::prediction::LinearRegression, qos::Qos, CenSolver, CtlRes, CtlState, HisQos};


pub struct BackSwitchSolver {

}

impl BackSwitchSolver {
    pub fn new() -> Self {
        BackSwitchSolver {}
    }
}

impl CenSolver for BackSwitchSolver {
    fn control(&self, qoses: &HisQos, ctl_task: String) -> CtlRes {
        // Appropriate for the back switch control
        let current_qos = qoses[qoses.len() - 1].get(&ctl_task).unwrap();
        let past_qos = qoses[qoses.len() - 2].get(&ctl_task).unwrap();

        let reg_vec = transform_qos_to_xy((&[past_qos, current_qos]).to_vec());
        let target_x = [1.0, 0.0];
        assert!(reg_vec.len() == 2, "reg_vec must have a length of 2");
        let mut res = [0.0, 0.0];
    
        // Do the regression
        for idx in 0..reg_vec.len() {
            let (X, y) = &reg_vec[idx];
            let mut reg = LinearRegression::new();
            reg.fit(X, y);
    
            // Convert target_x[idx] to an Array1 for prediction
            let target_value = Array::from_elem((1,1), target_x[idx]);
            let pred = reg.predict(&target_value);
            println!("Predicted value: {}", pred);
            res[idx] = pred[0];
        }
        
        let mut controls = HashMap::new();

        let tx_parts = if res[0] < current_qos.target_rtt {
            [1.0, 1.0]
        } else if res[1] < current_qos.target_rtt {
            [0.0, 0.0]
        }
        else{
            [past_qos.tx_parts[0], past_qos.tx_parts[1]]
        };

        controls.insert(ctl_task, Action::new(Some(tx_parts.to_vec()), None, None));
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