use std::collections::HashMap;
use crate::HisQos;
use crate::{action::Action, qos::Qos, state::State, types::state::Color, CtlRes, CtlState, DecSolver};
use crate::types::paramter::HYPER_PARAMETER;
use crate::cores::channel_balancer::ChannelBalanceSolver;

pub struct GSolver {
    #[warn(dead_code)]
    pub balance_anyway: bool,
    pub throttle_step_size: f64,
    pub is_back_switch: bool,
}

#[allow(dead_code)]
impl GSolver {
    pub fn new() -> Self {
        GSolver {
            balance_anyway: false,
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

    fn handle_normal_switch(
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

                let len = his_qoses.len();
                let start = if len >= 5 { len - 5 } else { 0 };

                let not_check_degration = his_qoses[start..len].iter().any(|qoses| 
                    qoses.values().any(|qos| qos.tx_parts.iter().any( |&x| x != 0.0 && x != 1.0 )));

                if qos.channel_rtts.is_some() {
                    let tx_parts =
                        ChannelBalanceSolver::new(self.balance_anyway).control(qos.clone(), channel_state, not_check_degration);
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
            self.handle_normal_switch(qoses, channel_state, his_qoses)
        }
    }
}

fn determine_back_switch(qoses: &HashMap<String, Qos>, alpha: f64) -> Option<&String>{
    let mut back_switch_task = None;
    for (name, qos) in qoses {
        if let Some(channel_rtts) = qos.channel_rtts.clone() {
            let tx_parts = qos.tx_parts.clone();
            let tx_parts = vec![tx_parts[0], 1.0 - tx_parts[1]];
            let target_rtt = qos.target_rtt;
        
            if tx_parts.iter().any(|&tx_part| tx_part == 0.0 || tx_part == 1.0) {
                continue;
            }

            let res:Vec<bool> = tx_parts.into_iter().zip(channel_rtts.into_iter()).map(|(tx_part, channel_rtt)| {
                if channel_rtt <= target_rtt * alpha * tx_part {
                    true
                }
                else{
                    false
                }
            }).collect();
        
            if res.into_iter().any(|x| x) {
                back_switch_task = Some(name);
            }
        }
    }
    back_switch_task
}