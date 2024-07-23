use std::collections::HashMap;

use crate::{action::Action, qos::Qos, state::State, Solver};

pub struct FileSolver {
    pub step_size: f64,
}

impl Solver for FileSolver {
    fn control(&self, qoses: HashMap<String, Qos>, channel_state: &State) -> HashMap<String, Action> {
        qoses.into_iter().map(|(name, qos)| {
            let channel_colors = qos.channels.iter()
            .filter_map(|channel| channel_state.color.get(channel).cloned())
            .collect();
            if qos.channel_rtts.is_none(){
                let mut throttle = qos.throttle - self.step_size;
                if throttle <= 0.0 {
                    throttle = 1.0;
                }
                println!("step_size: {}", self.step_size);
                
                (name, Action::new(None, Some(throttle), channel_colors))
            }
            else{
                (name, Action::new(None, None, channel_colors))
            }
        }).collect()
    }
}