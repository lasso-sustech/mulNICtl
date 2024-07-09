use pyo3::{prelude::*, types::{PyDict, PyList}};
use serde::Deserialize;

type Link = (String, String);

#[derive(Deserialize, Clone)]
pub struct Qos {
    pub channel_rtts: Vec<f64>,
    pub tx_parts: Vec<f64>,
    pub channel_probabilities:Option<Vec<f64>>,
    pub name: String,
}

impl FromPyObject<'_> for Qos {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let channel_rtts = ob.get_item("channel_rtts")?.extract()?;
        let tx_parts = ob.get_item("tx_parts")?.extract()?;
        // Handle optional field
        let channel_probabilities: Option<Vec<f64>> = match ob.get_item("channel_probabilities") {
            Ok(val) => Some(val.extract()?),
            Err(_) => None,
        };
        let name = ob.get_item("name")?.extract()?;
        Ok(Qos { channel_rtts, tx_parts, channel_probabilities, name })
    }
}

#[derive(Deserialize, Clone)]
pub struct Stream {
    pub target_rtt  : f64,
    pub links       : Vec<Link>,
}

impl FromPyObject<'_> for Stream {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let target_rtt = ob.get_item("target_rtt")?.extract()?;
        let temp_links:Vec<Vec<String>> = ob.get_item("links")?.extract()?;
        // temp_links is a list of list
        let links = temp_links.iter().map(|x| (x[0].clone(), x[1].clone())).collect();
        Ok(Stream { target_rtt, links })
    }
}

impl IntoPy<PyObject> for Stream {
    fn into_py(self, py: Python<'_>) -> PyObject {
        let links = PyList::new(py, self.links.iter().map(|(a, b)| (a, b)).collect::<Vec<_>>());
        let target_rtt = self.target_rtt;
        let stream = PyDict::new(py);
        stream.set_item("links", links).unwrap();
        stream.set_item("target_rtt", target_rtt).unwrap();
        stream.into()
    }
}