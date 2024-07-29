use pyo3::prelude::*;
use serde::Deserialize;

use crate::api::ipc::Statistics;

use super::static_value::StaticValue;

type Link = (String, String);

#[derive(Deserialize, Clone, Debug)]
pub struct Qos {
    pub channel_rtts: Option<Vec<f64>>,
    pub outage_rate : Option<f64>,
    pub ch_outage_rates: Option<Vec<f64>>,
    pub tx_parts: Vec<f64>,
    pub channel_probabilities:Option<Vec<f64>>,
    pub target_rtt: f64,
    pub links : Vec<Link>,
    pub channels: Vec<String>,
    pub throttle: f64,
}

impl From<(&Statistics, &StaticValue)> for Qos {
    fn from((stats, static_value): (&Statistics, &StaticValue)) -> Self {
        Qos {
            channel_rtts: stats.channel_rtts.clone(),
            outage_rate: stats.outage_rate,
            ch_outage_rates: stats.ch_outage_rates.clone(),
            tx_parts: stats.tx_parts.clone(),
            channel_probabilities: None, // Assuming channel probabilities need to be calculated separately
            target_rtt: static_value.target_rtt,
            links: static_value.links.clone(),
            channels: static_value.channels.clone(),
            throttle: stats.throttle,
        }
    }
}

impl FromPyObject<'_> for Qos {
    fn extract(ob: &PyAny) -> PyResult<Self> {
        let channel_rtts = ob.get_item("channel_rtts")?.extract()?;
        let outage_rate = ob.get_item("outage_rate")?.extract()?;
        let ch_outage_rates: Option<Vec<f64>> = ob.get_item("ch_outage_rates")?.extract()?;
        let tx_parts = ob.get_item("tx_parts")?.extract()?;
        let channel_probabilities: Option<Vec<f64>> = match ob.get_item("channel_probabilities") {
            Ok(val) => Some(val.extract()?),
            Err(_) => None,
        };
        
        let target_rtt = ob.get_item("target_rtt")?.extract()?;
        let temp_links: Vec<Vec<String>> = ob.get_item("links")?.extract()?;
        let links = temp_links.iter().map(|x| (x[0].clone(), x[1].clone())).collect();
        let channels = ob.get_item("channels")?.extract()?;
        let throttle = ob.get_item("throttle")?.extract()?;

        Ok(Qos { channel_rtts, outage_rate, ch_outage_rates, tx_parts, channel_probabilities, target_rtt, links, channels, throttle})
    }
}