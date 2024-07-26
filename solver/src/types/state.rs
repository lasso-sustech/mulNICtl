use std::{cmp::max, collections::HashMap};

use pyo3::ToPyObject;

use crate::qos::Qos;


#[derive(PartialEq, Eq, Ord, PartialOrd, Clone)]
pub enum Color {
    Green,
    Yellow,
    Red,
}

impl ToPyObject for Color {
    fn to_object(&self, py: pyo3::Python) -> pyo3::PyObject {
        match self {
            Color::Green => "green".to_object(py),
            Color::Yellow => "yellow".to_object(py),
            Color::Red => "red".to_object(py),
        }
    }
}

#[derive(Clone)]
pub struct State{
    pub color: HashMap<String, Color>,
}

impl State{
    pub fn new() -> State{
        State{
            color: HashMap::new(),
        }
    }

    fn color(rtt: f64, target_rtt: f64, outage_rate: f64) -> Color{
        if rtt < target_rtt {
            if outage_rate < 0.1 {
                Color::Green
            }
            else{
                Color::Yellow
            }
        }else {
            Color::Red
        }
    }

    pub fn update(&mut self, qoss: & HashMap<String, Qos>) {
        // filter qoss with channel_rtts
        let mut color_map: HashMap<String, Color> = HashMap::new();

        for qos in qoss.values() {
            if let (Some(channel_rtts), Some(ch_outage_rates)) = (&qos.channel_rtts, &qos.ch_outage_rates) {
                for (channel, (channel_rtt, outage_rate)) in qos.channels.iter().zip(channel_rtts.iter().zip(ch_outage_rates.iter())) {
                    let color = State::color(*channel_rtt, qos.target_rtt, *outage_rate);
                    color_map.entry(channel.clone())
                        .and_modify(|existing_color| *existing_color = max(existing_color.clone(), color.clone()))
                        .or_insert(color);
                }
            }
        }

        self.color = color_map;
    }
}

