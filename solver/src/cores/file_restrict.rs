use crate::{action::Action, state::State, types::{paramter::HYPER_PARAMETER, state::Color}, CtlRes, CtlState, DecSolver, HisQos};

pub struct FileSolver {
    pub throttle_step_size: f64,
}

impl DecSolver for FileSolver {
    fn control(&self, his_qoses: &HisQos, channel_state: &State) -> CtlRes {
        let qoses = &his_qoses[0];
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