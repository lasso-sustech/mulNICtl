use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Statistics {
    pub rtt: f64,
    pub channel_rtts: Vec<f64>,
    pub throughput: f64,
    pub tx_parts: Vec<f64>,
}

pub struct SystemState {
    exp_data: ExpInputData,
    metric_data: MetricInputData,
}

pub struct ExpInputData {

}

pub struct MetricInputData {

}


