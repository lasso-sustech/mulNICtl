use std::collections::HashMap;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3::ToPyObject;

use crate::state::Color;

#[derive(Clone)]
pub struct Action {
    pub tx_parts: Option<Vec<f64>>,
    pub throttle: Option<f64>,
    pub channel_colors: Vec<Color>,
}


impl Action {
    pub fn new(tx_parts: Option<Vec<f64>>, throttle: Option<f64>, channel_colors: Vec<Color>) -> Self {
        Action {
            tx_parts,
            throttle,
            channel_colors,
        }
    }
}

impl ToPyObject for Action {
    fn to_object(&self, py: Python) -> PyObject {
        let tx_parts_list = match &self.tx_parts {
            Some(parts) => PyList::new(py, parts),
            None => PyList::empty(py),
        };
        
        let channels_list: Vec<PyObject> = self.channel_colors.iter().map(|c| c.to_object(py)).collect();
        let py_channels_list = PyList::new(py, &channels_list);

        let dict = PyDict::new(py);
        dict.set_item("tx_parts", tx_parts_list).unwrap();
        dict.set_item("throttle", self.throttle).unwrap();
        dict.set_item("channels", py_channels_list).unwrap();
        dict.into()
    }
}


pub fn hash_map_to_py_dict(map: HashMap<String, Action>) -> Py<PyDict> {
    Python::with_gil(|py| {
        let py_dict = PyDict::new(py);
        for (key, value) in map {
            py_dict.set_item(key, value.to_object(py)).unwrap();
        }
        py_dict.into()
    })
}