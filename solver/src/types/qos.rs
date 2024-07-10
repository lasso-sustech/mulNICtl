use pyo3::prelude::*;
use serde::Deserialize;

type Link = (String, String);

#[derive(Deserialize, Clone)]
pub struct Qos {
    pub channel_rtts: Vec<f64>,
    pub tx_parts: Vec<f64>,
    pub channel_probabilities:Option<Vec<f64>>,
    pub target_rtt: f64,
    pub links : Vec<Link>,
    pub channels: Vec<String>,
}

impl FromPyObject<'_> for Qos {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let channel_rtts = ob.get_item("channel_rtts")?.extract()?;
        let tx_parts = ob.get_item("tx_parts")?.extract()?;
        let channel_probabilities: Option<Vec<f64>> = match ob.get_item("channel_probabilities") {
            Ok(val) => Some(val.extract()?),
            Err(_) => None,
        };
        
        let target_rtt = ob.get_item("target_rtt")?.extract()?;
        let temp_links: Vec<Vec<String>> = ob.get_item("links")?.extract()?;
        let links = temp_links.iter().map(|x| (x[0].clone(), x[1].clone())).collect();
        let channels = ob.get_item("channels")?.extract()?;

        Ok(Qos { channel_rtts, tx_parts, channel_probabilities, target_rtt, links, channels})
    }
}