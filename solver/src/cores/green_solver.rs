use std::collections::HashMap;
use crate::HisQos;
use crate::{action::Action, qos::Qos, state::State, types::state::Color, CtlRes, CtlState, DecSolver};
use crate::types::parameter::HYPER_PARAMETER;
use crate::cores::channel_balancer::ChannelBalanceSolver;

use super::checker::{is_adaptation, is_degration, is_his_back_ever, is_stay_in_channel, determine_back_switch};

pub struct GSolver {
    pub throttle_step_size: f64,
    pub is_back_switch: bool,
}

impl DecSolver for GSolver{
    fn control(&self, his_qoses: &HisQos, channel_state: &State) -> CtlRes {
        let qoses = &his_qoses[0];
        let back_switch_name = match self.is_back_switch {
            true => determine_back_switch(qoses, HYPER_PARAMETER.backward_threshold),
            false => None,
        };
        
        if let Some(back_switch_name) = back_switch_name {
            self.handle_back_switch(back_switch_name.clone(), qoses, channel_state)
        }
        else{
            self.handle_control(qoses, channel_state, his_qoses)
        }
    }
}

#[allow(dead_code)]
impl GSolver {
    pub fn new() -> Self {
        GSolver {
            throttle_step_size: 10.0,
            is_back_switch: false,
        }
    }

    fn handle_back_switch(
        &self,
        back_switch_name: String,
        qoses: &HashMap<String, Qos>,
        channel_state: &State,
    ) -> CtlRes {
        let mut controls: HashMap<String, Action> = HashMap::new();
    
        if let Some(qos) = qoses.get(&back_switch_name) {
            let channel_colors: Vec<Color> = qos
                .channels
                .iter()
                .filter_map(|channel| channel_state.color.get(channel).cloned())
                .collect();
    
            // Add default offset to tx_parts
            let tx_parts = if qos.tx_parts[0] + 0.1 < 1.0 {
                qos.tx_parts.clone().into_iter().map(|x| x + 0.1).collect()
            } else {
                qos.tx_parts.clone().into_iter().map(|x| x - 0.1).collect()
            };
    
            controls.insert(
                back_switch_name.clone(),
                Action::new(Some(tx_parts), None, Some(channel_colors)),
            );
        }
    
        (controls, CtlState::BackSwitch, Some(back_switch_name.clone()))
    }

    fn handle_control(
        &self,
        qoses: &HashMap<String, Qos>,
        channel_state: &State,
        his_qoses: &HisQos,
    ) -> CtlRes {
        let controls = qoses
            .iter()
            .map(|(name, qos)| {
                let channel_colors: Vec<Color> = qos
                    .channels
                    .iter()
                    .filter_map(|channel| channel_state.color.get(channel).cloned())
                    .collect();
                
                if let (Some(channel_rtts), Some(rtt)) = (qos.channel_rtts.clone(), qos.rtt) {
                    let tx_parts = qos.tx_parts.clone();
                    if qos.is_single_channel() {
                        // check his_qoses if the channel is back switch ever
                        if is_his_back_ever(his_qoses, name) {
                            return (name.clone(), Action::new(Some(tx_parts), None, Some(channel_colors)));
                        }
                        if is_stay_in_channel(&qos.tx_parts, &channel_colors){
                            return (name.clone(), Action::new(Some(tx_parts), None, Some(channel_colors)));
                        }
                    }
                    else{
                        if is_degration(&channel_rtts, &qos.tx_parts, rtt){
                            return (name.clone(), Action::new(Some(vec![1.0, 1.0]), None, Some(channel_colors)));
                        }
                        if !is_adaptation(&channel_rtts, &channel_colors){
                            return (name.clone(), Action::new(Some(tx_parts), None, Some(channel_colors)));
                        }
                    }

                    let tx_parts =
                        ChannelBalanceSolver::new().control(qos.clone(), his_qoses, name.clone());
                    (name.clone(), Action::new(Some(tx_parts), None, Some(channel_colors)))
                } else {
                    let throttle = (qos.throttle + self.throttle_step_size)
                        .clamp(HYPER_PARAMETER.throttle_low, HYPER_PARAMETER.throttle_high);
                    (name.clone(), Action::new(None, Some(throttle), Some(channel_colors)))
                }
            })
            .collect();
        
        (controls, CtlState::Normal, None)
    }
}


