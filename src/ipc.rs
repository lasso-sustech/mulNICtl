use std::collections::HashMap;
use std::net::UdpSocket;
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::data::Statistics;

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

pub struct IPCController {
    sock: UdpSocket,
    target_addr: String,
}

impl IPCController {
    pub fn new(target_ip: String, ipc_port: u16) -> IPCController {
        let sock = UdpSocket::bind("0.0.0.0:0").unwrap();
        let target_addr = format!("{}:{}", target_ip, ipc_port);
        Self { sock, target_addr }
    }

    fn send_cmd(&self, content: &Value) {
        let msg = HashMap::from([("cmd", content)]);
        let msg = serde_json::to_string(&msg).unwrap();
        self.sock.send_to(msg.as_bytes(), &self.target_addr).unwrap();
    }

    fn ipc_communicate(&self, content: &Value) -> Value {
        let mut buf = [0 as u8; 1024];
        self.send_cmd(content);
        let (_len, _addr) = self.sock.recv_from(&mut buf).unwrap();
        serde_json::from_slice(&buf).unwrap()
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
        let res: HashMap<String, Statistics> = serde_json::from_value(
            res["cmd"]["Statistics"].clone()
        ).unwrap();
        res
    }

    pub fn tx_part(&self, tx_part: HashMap<String, [f32; 2]>) {
        let command = TxPartCommand { tx_part };
        let command = serde_json::to_value(command).unwrap();
        self.ipc_transmit(&command);
    }
}
