use std::{collections::HashMap, time::Duration};
use std::net::UdpSocket;
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::types::action::Action;

#[derive(Serialize, Deserialize, Debug, Clone)] //TODO: make the statistics synced with the stream-replay
pub struct Statistics {
    pub rtt: Option<f64>,
    pub channel_rtts: Option<Vec<f64>>,
    pub outage_rate : Option<f64>,
    pub ch_outage_rates: Option<Vec<f64>>,
    pub throughput: f64,
    pub tx_parts: Vec<f64>,
    pub throttle: f64,
}

#[derive(Serialize, Deserialize, Default)]
struct ThrottleCommand {
    #[serde(rename = "Throttle")]
    pub throttle_ctl: HashMap<String, f32>
}

#[derive(Serialize, Deserialize, Default)]
struct StatisticsCommand {
    #[serde(rename = "Statistics")]
    pub statistics: HashMap<String, Statistics>
}

#[derive(Serialize, Deserialize, Default)]
struct TxPartCommand {
    #[serde(rename = "TxPart")]
    pub tx_part: HashMap<String, [f32; 2]>
}

pub struct IPCManager {
    pub ipcs : HashMap<String, IPCController>,
    pub name2ipc: HashMap<String, String>,
}

impl IPCManager {
    pub fn new( target_ips: HashMap<String, (String, u16)>, name2ipc: HashMap<String, String> ) -> IPCManager {
        let mut ipcs = HashMap::new();
        for (name, (target_ip, ipc_port)) in target_ips.iter() {
            
            let ipc = IPCController::new(target_ip.clone(), ipc_port.clone() as u16);
            ipcs.insert(name.clone(), ipc);
        }
        Self { ipcs, name2ipc }
    }

    pub fn qos_collect(&self) -> HashMap<String, Statistics> {
        let mut res = HashMap::new();
        for (_, ipc) in self.ipcs.iter() {
            let statistics = ipc.statistics();
            for (k, v) in statistics {
                res.insert(k, v);
            }
        }
        res
    }

    pub fn apply_control(&self, controls: HashMap<String, Action>) {
        for (name, action) in controls {
            if let Some(throttle) = action.throttle {
                let mut throttle_ctl = HashMap::new();
                throttle_ctl.insert(name.clone(), throttle as f32);
                if let Some(ipc) = self.ipcs.get(self.name2ipc.get(&name).unwrap()) {
                    ipc.throttle(throttle_ctl);
                }
            }
    
            if let Some(tx_parts) = action.tx_parts.as_ref() {
                if tx_parts.len() == 2 {
                    let mut tx_part = HashMap::new();
                    tx_part.insert(name.clone(), [tx_parts[0] as f32, tx_parts[1] as f32]);
                    if let Some(ipc) = self.ipcs.get(self.name2ipc.get(&name).unwrap()) {
                        ipc.tx_part(tx_part);
                    }
                }
            }
        }
    }
    
    
}


pub struct IPCController {
    sock: UdpSocket,
    target_addr: String,
}

impl IPCController {
    pub fn new(target_ip: String, ipc_port: u16) -> IPCController {
        let sock = UdpSocket::bind("0.0.0.0:0").unwrap();
        // Set the read timeout duration
        sock.set_read_timeout(Some(Duration::from_secs(1))).unwrap();
        let target_addr = format!("{}:{}", target_ip, ipc_port);
        Self { sock, target_addr }
    }

    fn send_cmd(&self, content: &Value) {
        let msg = HashMap::from([("cmd", content)]);
        let msg = serde_json::to_string(&msg).unwrap();
        self.sock.send_to(msg.as_bytes(), &self.target_addr).unwrap();
    }

    fn ipc_communicate(&self, content: &Value) -> Value {
        let mut buf = [0 as u8; 4048];
        self.send_cmd(content);
        
        match self.sock.recv_from(&mut buf) {
            Ok((len, _addr)) => {
                serde_json::from_slice(&buf[0..len]).unwrap_or_else(|_| Value::Null)
            },
            Err(e) => {
                // Handle other kinds of errors if needed
                eprintln!("An error occurred: {}", e);
                Value::Null
            },
        }
    }

    fn ipc_transmit(&self, content: &Value) {
        self.send_cmd(content);
    }

    pub fn throttle(&self, throttle_ctl: HashMap<String, f32>) {
        let command = ThrottleCommand { throttle_ctl };
        let command = serde_json::to_value(command).unwrap();
        self.ipc_transmit(&command);
    }

    pub fn statistics(&self) -> HashMap<String, Statistics> {
        let command = StatisticsCommand::default();
        let command = serde_json::to_value(command).unwrap();
        let res = self.ipc_communicate(&command);
        
        if res == Value::Null {
            // Handle the case where the response is empty due to timeout or error
            return HashMap::new();
        }
        
        // Attempt to deserialize the response
        match serde_json::from_value::<HashMap<String, Statistics>>(res["cmd"]["Statistics"].clone()) {
            Ok(stats) => stats,
            Err(e) => {
                eprintln!("Failed to deserialize statistics: {}", e);
                HashMap::new()
            }
        }
    }

    pub fn tx_part(&self, tx_part: HashMap<String, [f32; 2]>) {
        let command = TxPartCommand { tx_part };
        let command = serde_json::to_value(command).unwrap();
        self.ipc_transmit(&command);
    }
}