mod types;
mod cores;

use std::collections::HashMap;
use pyo3::{prelude::*, types::PyDict};

use crate::types::{action, qos, state};
use crate::state::{State, Color};
use crate::qos::Qos;
use crate::action::{hash_map_to_py_dict, Action};
use crate::cores::rtt_balance::RttBalanceSolver;

trait Solver {
    fn control(&self, qos: HashMap<String, Qos>, channel_state: &State) -> HashMap<String, Action>;
}

fn algorithm_selection(glb_state: &State) -> Option<Box<dyn Solver>>{
    let color_values = glb_state.color.values().cloned().collect::<Vec<Color>>();
    if color_values.len() == 0 || color_values.len() > 2 {
        eprintln!("The number of channel is zero or more than 2; Not handle.");
        return None;
    }
    match color_values.as_slice() {
        [Color::Green]  => None,
        [Color::Yellow] => None,
        [Color::Red]    => None,

        [Color::Green, Color::Green]    => Some(Box::new(RttBalanceSolver {backward_threshold: 0.8})),
        [Color::Yellow, Color::Yellow]  => None,
        [Color::Red, Color::Red]        => None,

        [Color::Green, Color::Yellow] | [Color::Yellow, Color::Green]   => Some(Box::new(RttBalanceSolver {backward_threshold: 0.8})),
        [Color::Green, Color::Red]  | [Color::Red, Color::Green]        => Some(Box::new(RttBalanceSolver {backward_threshold: 0.8})),
        [Color::Yellow, Color::Red] | [Color::Red, Color::Yellow]       => None,

        _ => None,
    }
}

#[pyclass]
#[derive(Clone)]
pub struct Controller {
    glb_state: State,
}

#[pymethods]
impl Controller {
    #[new]
    pub fn new() -> Controller {
        Controller {
            glb_state: State::new(),
        }
    }

    #[pyo3(text_signature = "(self, qoss)")]
    pub fn control(&mut self, qoss: HashMap<String, Qos>) -> Py<PyDict> {
        self.glb_state.update(qoss.clone());

        let solver = algorithm_selection(&self.glb_state);
        match solver {
            Some(solver) => hash_map_to_py_dict(solver.control(qoss, &self.glb_state)),
            None => hash_map_to_py_dict(HashMap::new()),
        }
    }
}


#[pymodule]
fn solver(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Controller>()?;
    Ok(())
}
