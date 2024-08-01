mod types;
mod cores;
mod tests;
mod api;

extern crate blas_src;

use core::str;
use std::collections::HashMap;
use std::net::UdpSocket;
use base64::prelude::*;
use serde_json::Value;
use std::str::FromStr;

use clap::{Parser};
use cores::back_switch_solver::BackSwitchSolver;
use cores::green_solver::GRSolver;
use serde::{Deserialize, Serialize};

use crate::types::{action, qos, state, static_value::StaticValue};
use crate::state::{State, Color};
use crate::qos::Qos;
use crate::action::Action;
use crate::cores::green_solver::GSolver;
use crate::cores::file_restrict::FileSolver;

type HisQos = Vec<HashMap<String, Qos>>;
type CtlRes = (HashMap<String, Action>, CtlState, Option<String>);
trait DecSolver {
    fn control(&self, qoses: HashMap<String, Qos>, channel_state: &State) -> CtlRes;
}
trait CenSolver {
    fn control(&self, qoses: &HisQos, ctl_task: String) -> CtlRes;
}

fn algorithm_selection(glb_state: &State) -> Option<Box<dyn DecSolver>>{
    let color_values = glb_state.color.values().cloned().collect::<Vec<Color>>();
    if color_values.len() == 0 || color_values.len() > 2 {
        println!("color_values: {:?}", color_values.clone());
        eprintln!("The number of channel is zero or more than 2; Not handle.");
        return None;
    }
    match color_values.as_slice() {
        [Color::Green]  => None,
        [Color::Yellow] => None,
        [Color::Red]    => Some( Box::new(FileSolver {step_size: 10.0}) ),

        [Color::Green, Color::Green]    => Some( Box::new( GSolver { backward_threshold: 0.8, is_all_balance: false, throttle_step_size: 10.0 } ) ),
        [Color::Yellow, Color::Yellow]  => None,
        [Color::Red, Color::Red]        => Some( Box::new( FileSolver {step_size: 10.0} ) ),

        [Color::Green, Color::Yellow] | [Color::Yellow, Color::Green]     => Some( Box::new(GSolver {backward_threshold: 0.8, is_all_balance: false, throttle_step_size: 10.0}) ),
        [Color::Green, Color::Red]    | [Color::Red, Color::Green]        => Some( Box::new(GRSolver {backward_threshold: 0.8, is_all_balance: true, throttle_step_size: 10.0}) ),
        [Color::Yellow, Color::Red]   | [Color::Red, Color::Yellow]       => Some( Box::new(GRSolver {backward_threshold: 0.8, is_all_balance: true, throttle_step_size: 10.0}) ),

        _ => None,
    }
}

#[derive(Clone, PartialEq, Eq)]
enum CtlState {
    Normal,
    PredOpt,
    BackSwitch,
}

#[derive(Clone)]
pub struct Controller {
    glb_state: State,
    history_qos: HisQos,
    ctl_state: CtlState,
    ctl_task: Option<String>,
}

impl Controller {
    pub fn new() -> Controller {
        Controller {
            glb_state: State::new(),
            history_qos: Vec::new(),
            ctl_state: CtlState::Normal,
            ctl_task: None,
        }
    }

    pub fn control(&mut self, qoss: HashMap<String, Qos>) -> HashMap<String, Action>{
        self.history_qos.push(qoss.clone());
        if self.history_qos.len() > 2 {
            self.history_qos.remove(0);
        }
        self.glb_state.update(&qoss);
        
        println!("qoss: {:?}", qoss.clone());

        if self.ctl_state == CtlState::Normal {
            let solver = algorithm_selection(&self.glb_state);
            match solver {
                Some(solver) => {
                    let (controls, ctl_state, ctl_task) = solver.control(qoss, &self.glb_state);
                    self.ctl_state = ctl_state;
                    self.ctl_task = ctl_task;
                    controls
                },
                None => HashMap::new(),
            }
        }
        else {
            if self.ctl_state == CtlState::BackSwitch {
                let solver = BackSwitchSolver::new();
                let (controls, ctl_state, _) = solver.control(&self.history_qos, self.ctl_task.clone().unwrap());
                self.ctl_state = ctl_state;
                controls
            }
            else {
                HashMap::new()
            }
        }
    }
}


// fn optimize( base_info: HashMap<String, StaticValue>, target_ips: HashMap<String, (String, u16)>, name2ipc: HashMap<String, String>  ){


fn optimize(
    base_info: HashMap<String, StaticValue>,
    target_ips: HashMap<String, (String, u16)>,
    name2ipc: HashMap<String, String>,
    monitor_ip: String,
){
    print!("target_ips: {:?}", target_ips.clone());
    print!("name2ipc: {:?}", name2ipc.clone());
    let ipc_manager = api::ipc::IPCManager::new( target_ips, name2ipc );

    // Create Send UDP Socket
    let send_socket = UdpSocket::bind("0.0.0.0:0").unwrap();
    

    // Start Control
    let mut controller = Controller::new();
    println!("Start Control");
    for _ in 0..200 {
        let stats = ipc_manager.qos_collect();

        // Trasform Statistics to QoS, by adding missing value from base_info AND delete the useless value
        let mut qoss = HashMap::new();
        for (name, stat) in stats {
            let qos:Qos = (&stat, base_info.get(&name).unwrap()).into();
            qoss.insert(name, qos);
        }

        // Control
        let controls = controller.control(qoss.clone());

        // Send to monitor ips
        match serde_json::to_string(&qoss) {
            Ok(value) => {
                let _ = send_socket.send_to(value.as_bytes(), monitor_ip.clone());
            },
            Err(e) => {
                eprintln!("Error parsing qoss: {}", e);
            }
        }
        match serde_json::to_string(&controls) {
            Ok(value) => {
                let _ = send_socket.send_to(value.as_bytes(), monitor_ip.clone());
            },
            Err(e) => {
                eprintln!("Error parsing controls: {}", e);
            }
        }

        // Apply Control
        ipc_manager.apply_control(controls);

        std::thread::sleep(std::time::Duration::from_secs(1));
    }

}


#[derive(Serialize, Deserialize, Debug, Parser)]
#[clap(author, version, about, long_about=None)]
struct ProgArgs {
    #[clap(short, long)]
    base_info: String,
    #[clap(short, long)]
    target_ips: String,
    #[clap(short, long)]
    name2ipc: String,
    #[clap(short, long)]
    monitor_ip: String,
}


fn from_base64(base64_str: String) -> Result<Value, serde_json::Error> {
    let decoded = BASE64_STANDARD.decode(base64_str).unwrap();
    let temp_slice: &[u8]= decoded.as_slice();
    serde_json::from_str(str::from_utf8(temp_slice).unwrap())
}

pub fn main() {
    let args: ProgArgs = ProgArgs::parse();
    let base_info: HashMap<String, StaticValue> = match {
        from_base64(args.base_info)
    } {
        Ok(value) => serde_json::from_value(value).unwrap(),
        Err(e) => {
            eprintln!("Error parsing base_info: {}", e);
            return;
        }
    };

    let target_ips: HashMap<String, (String, u16)> = match {
        from_base64(args.target_ips)
    } {
        Ok(value) => serde_json::from_value(value).unwrap(),
        Err(e) => {
            eprintln!("Error parsing target_ips: {}", e);
            return;
        }
    };

    let name2ipc: HashMap<String, String> = match {
        from_base64(args.name2ipc)
    } {
        Ok(value) => serde_json::from_value(value).unwrap(),
        Err(e) => {
            eprintln!("Error parsing name2ipc: {}", e);
            return;
        }
    };

    optimize(base_info, target_ips, name2ipc, args.monitor_ip);
}
