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

    fn color(rtt: f64, target_rtt: f64) -> Color{
        if rtt < target_rtt * 0.8{
            Color::Green
        }else if rtt > target_rtt {
            Color::Red
        }else{
            Color::Yellow
        }
    }

    pub fn update(&mut self, qoss: HashMap<String, Qos>) {
        // filter qoss with channel_rtts
        self.color = qoss.into_iter()
            .flat_map(|(_k, qos)| {
                match qos.channel_rtts {
                    Some(channel_rtts) => {
                        qos.channels.into_iter()
                            .zip(channel_rtts.into_iter())
                            .map(move |(channel, channel_rtt)| (channel, State::color(channel_rtt, qos.target_rtt)))
                            .collect::<Vec<_>>()
                    }
                    None => vec![],
                }
            })
            .fold(HashMap::new(), |mut acc, (channel, color)| {
                acc.entry(channel)
                    .and_modify(|e| *e = max(e.clone(), color.clone()))
                    .or_insert(color);
                acc
            });
    }
}

