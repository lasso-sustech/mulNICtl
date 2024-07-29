use pyo3::prelude::*;
use pyo3::types::PyAny;
#[derive(Debug, Default)]
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

impl FromPyObject<'_> for StaticValue {
    fn extract(ob: &'_ PyAny) -> PyResult<Self> {
        let npy_file: String = ob.get_item("npy_file")?.extract()?;
        let tos: u8 = ob.get_item("tos")?.extract()?;
        let port: u16 = ob.get_item("port")?.extract()?;
        let throttle: u32 = ob.get_item("throttle")?.extract()?;
        let start_offset: u32 = ob.get_item("start_offset")?.extract()?;
        let priority: String = ob.get_item("priority")?.extract()?;
        let calc_rtt: bool = ob.get_item("calc_rtt")?.extract()?;
        let no_logging: bool = ob.get_item("no_logging")?.extract()?;
        
        let temp_links: Vec<Vec<String>> = ob.get_item("links")?.extract()?;
        let links: Vec<(String, String)> = temp_links
            .into_iter()
            .map(|link| (link[0].clone(), link[1].clone()))
            .collect();

        let tx_parts: Vec<f64> = ob.get_item("tx_parts")?.extract()?;
        let target_rtt: f64 = ob.get_item("target_rtt")?.extract()?;

        let temp_duration: Vec<f64> = ob.get_item("duration")?.extract()?;
        let duration = [temp_duration[0], temp_duration[1]];

        let channels: Vec<String> = ob.get_item("channels")?.extract()?;
        let name: String = ob.get_item("name")?.extract()?;

        Ok(StaticValue {
            npy_file,
            tos,
            port,
            throttle,
            start_offset,
            priority,
            calc_rtt,
            no_logging,
            links,
            tx_parts,
            target_rtt,
            duration,
            channels,
            name,
        })
    }
}