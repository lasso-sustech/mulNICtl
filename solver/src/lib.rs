mod types;
mod cores;
mod tests;

extern crate blas_src;

use std::collections::{HashMap};

use cores::back_switch_solver::BackSwitchSolver;
use cores::green_solver::GRSolver;
use pyo3::{prelude::*, types::PyDict};

use crate::types::{action, qos, state};
use crate::state::{State, Color};
use crate::qos::Qos;
use crate::action::{hash_map_to_py_dict, Action};
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

        [Color::Green, Color::Green]    => Some( Box::new( GSolver { backward_threshold: 0.8, is_all_balance: false, throttle_step_size: 10.0 }) ),
        [Color::Yellow, Color::Yellow]  => None,
        [Color::Red, Color::Red]        => Some( Box::new( FileSolver {step_size: 10.0}) ),

        [Color::Green, Color::Yellow] | [Color::Yellow, Color::Green]   => Some( Box::new(GSolver {backward_threshold: 0.8, is_all_balance: false, throttle_step_size: 10.0}) ),
        [Color::Green, Color::Red]  | [Color::Red, Color::Green]        => Some( Box::new(GRSolver {backward_threshold: 0.8, is_all_balance: true, throttle_step_size: 10.0}) ),
        [Color::Yellow, Color::Red] | [Color::Red, Color::Yellow]       => Some( Box::new(GRSolver {backward_threshold: 0.8, is_all_balance: true, throttle_step_size: 10.0}) ),

        _ => None,
    }
}

#[derive(Clone, PartialEq, Eq)]
enum CtlState {
    Normal,
    PredOpt,
    BackSwitch,
}
#[pyclass]
#[derive(Clone)]
pub struct Controller {
    glb_state: State,
    history_qos: HisQos,
    ctl_state: CtlState,
    ctl_task: Option<String>,
}

#[pymethods]
impl Controller {
    #[new]
    pub fn new() -> Controller {
        Controller {
            glb_state: State::new(),
            history_qos: Vec::new(),
            ctl_state: CtlState::Normal,
            ctl_task: None,
        }
    }

    #[pyo3(text_signature = "(self, qoss)")]
    pub fn control(&mut self, qoss: HashMap<String, Qos>) -> Py<PyDict> {
        self.history_qos.push(qoss.clone());
        if self.history_qos.len() > 2 {
            self.history_qos.remove(0);
        }
        self.glb_state.update(&qoss);
        
        if self.ctl_state == CtlState::Normal {
            let solver = algorithm_selection(&self.glb_state);
            match solver {
                Some(solver) => {
                    let (controls, ctl_state, ctl_task) = solver.control(qoss, &self.glb_state);
                    self.ctl_state = ctl_state;
                    self.ctl_task = ctl_task;
                    hash_map_to_py_dict(controls)
                },
                None => hash_map_to_py_dict(HashMap::new()),
            }
        }
        else {
            if self.ctl_state == CtlState::BackSwitch {
                let solver = BackSwitchSolver::new();
                let (controls, ctl_state, _) = solver.control(&self.history_qos, self.ctl_task.clone().unwrap());
                self.ctl_state = ctl_state;
                hash_map_to_py_dict(controls)
            }
            else {
                hash_map_to_py_dict(HashMap::new())
            }
        }
    }
}


#[pymodule]
fn solver(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Controller>()?;
    Ok(())
}
