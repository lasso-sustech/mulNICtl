use std::collections::HashMap;

use crate::{action::Action, qos::Qos, state::State, types::{paramter::HYPER_PARAMETER, state::Color}, CtlRes, CtlState, DecSolver};

pub struct FileSolver {
    pub throttle_step_size: f64,
}

impl DecSolver for FileSolver {
    fn control(&self, qoses: &HashMap<String, Qos>, channel_state: &State) -> CtlRes {
        let controls = qoses.into_iter().map(|(name, qos)| {
            let channel_colors: Vec<Color> = qos.channels.iter()
            .filter_map(|channel| channel_state.color.get(channel).cloned())
            .collect();

            if qos.channel_rtts.is_none(){
                let throttle = (qos.throttle - self.throttle_step_size).clamp(HYPER_PARAMETER.throttle_low, HYPER_PARAMETER.throttle_high);
                println!("step_size: {}", self.throttle_step_size);
                
                (name.clone(), Action::new(None, Some(throttle), Some(channel_colors)))
            }
            else{
                (name.clone(), Action::new(None, None, Some(channel_colors)))
            }
        }).collect();
        (controls, CtlState::Normal ,None)
    }
}