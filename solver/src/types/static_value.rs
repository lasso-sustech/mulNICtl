use std::str::FromStr;

use serde::{Deserialize, Serialize};
#[derive(Debug, Default, Deserialize, Serialize, Clone)]
pub struct StaticValue {
    pub npy_file: String,
    pub tos: u8,
    pub port: u16,
    pub throttle: u32,
    pub start_offset: u32,
    pub priority: String,
    pub calc_rtt: bool,
    pub no_logging: bool,
    pub links: Vec<(String, String)>,
    pub tx_parts: Vec<f64>,
    pub target_rtt: f64,
    pub duration: [f64; 2],
    pub channels: Vec<String>,
    pub name: String,
}

impl FromStr for StaticValue {
    type Err = serde_json::Error;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        serde_json::from_str(s)
    }
}