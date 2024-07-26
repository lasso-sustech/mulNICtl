use std::collections::HashMap;

use crate::{action::Action, qos::Qos, state::State, types::state::Color, CtlRes, CtlState, DecSolver};

pub struct FileSolver {
    pub step_size: f64,
}

impl DecSolver for FileSolver {
    fn control(&self, qoses: HashMap<String, Qos>, channel_state: &State) -> CtlRes {
        let controls = qoses.into_iter().map(|(name, qos)| {
            let channel_colors: Vec<Color> = qos.channels.iter()
            .filter_map(|channel| channel_state.color.get(channel).cloned())
            .collect();

            if qos.channel_rtts.is_none(){
                let mut throttle = qos.throttle - self.step_size;
                if throttle <= 0.0 {
                    throttle = 1.0;
                }
                println!("step_size: {}", self.step_size);
                
                (name, Action::new(None, Some(throttle), Some(channel_colors)))
            }
            else{
                (name, Action::new(None, None, Some(channel_colors)))
            }
        }).collect();
        (controls, CtlState::Normal ,None)
    }
}