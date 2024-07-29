use std::collections::HashMap;

use serde::Serialize;

use crate::state::Color;
#[derive(Clone, Debug, Serialize)]
pub struct Action {
    pub tx_parts: Option<Vec<f64>>,
    pub throttle: Option<f64>,
    pub channel_colors: Option<Vec<Color>>,
}


impl Action {
    pub fn new(tx_parts: Option<Vec<f64>>, throttle: Option<f64>, channel_colors: Option<Vec<Color>>) -> Self {
        Action {
            tx_parts,
            throttle,
            channel_colors,
        }
    }
}
