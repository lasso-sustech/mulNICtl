use std::{cmp::max, collections::HashMap};


use serde::Serialize;

use crate::qos::Qos;


#[derive(PartialEq, Eq, Ord, PartialOrd, Clone, Debug, Serialize)]
pub enum Color {
    Green,
    Yellow,
    Red,
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

    fn color(rtt: f64, target_rtt: f64, overall_rtt: f64) -> Color{
        if overall_rtt < target_rtt {
            Color::Green
        }
        else if rtt > overall_rtt * 0.8 && rtt < target_rtt {
            Color::Yellow
        }
        else {
            Color::Red
        }
    }

    pub fn update(&mut self, qoss: & HashMap<String, Qos>) {
        // filter qoss with channel_rtts
        let mut color_map: HashMap<String, Color> = HashMap::new();

        for qos in qoss.values() {
            if let (Some(channel_rtts), Some(ch_outage_rates), Some(rtt)) = (&qos.channel_rtts, &qos.ch_outage_rates, &qos.rtt) {
                for (channel, (channel_rtt, outage_rate)) in qos.channels.iter().zip(channel_rtts.iter().zip(ch_outage_rates.iter())) {
                    let color = State::color(*channel_rtt, qos.target_rtt, *rtt);
                    color_map.entry(channel.clone())
                        .and_modify(|existing_color| *existing_color = max(existing_color.clone(), color.clone()))
                        .or_insert(color);
                }
            }
        }

        self.color = color_map;
    }
}

