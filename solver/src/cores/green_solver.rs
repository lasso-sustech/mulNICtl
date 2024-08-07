use std::{collections::HashMap};

use crate::{action::Action, qos::Qos, state::State, types::state::Color, CtlRes, CtlState, DecSolver};


pub struct GSolver {
    #[warn(dead_code)]
    pub backward_threshold: f64,
    pub balance_anyway: bool,
    pub throttle_step_size: f64,
}

#[allow(dead_code)]
impl GSolver {
    pub fn new() -> Self {
        GSolver {
            backward_threshold: 0.8,
            balance_anyway: false,
            throttle_step_size: 10.0,
        }
    }
}

impl DecSolver for GSolver{
    fn control(&self, qoses: HashMap<String, Qos>, channel_state: &State) -> CtlRes {

        if let Some(back_switch_name) = determine_back_switch(&qoses, 0.8){
            let mut controls: HashMap<String, Action> = HashMap::new();

            if let Some(qos) = qoses.get(back_switch_name) {
                let channel_colors: Vec<Color>  = qos.channels.iter()
                    .filter_map(|channel| channel_state.color.get(channel).cloned())
                    .collect();
                
                
                // add default offset to tx_parts
                let tx_parts = if qos.tx_parts[0] + 0.1 <= 1.0 {
                    qos.tx_parts.clone().into_iter().map(|x| x + 0.1).collect()
                }
                else{
                    qos.tx_parts.clone().into_iter().map(|x| x - 0.1).collect()
                };
                
                controls.insert(
                    back_switch_name.clone(),
                    Action::new(Some(tx_parts), None, Some(channel_colors)),
                );
            }

            return (controls, CtlState::BackSwitch, Some(back_switch_name.clone()));
        }

        let controls = qoses.into_iter().map(|(name, qos)| {
            let channel_colors: Vec<Color>  = qos.channels.iter()
                .filter_map(|channel| channel_state.color.get(channel).cloned())
                .collect();
            if qos.channel_rtts.is_some(){
                let tx_parts = ChannelBalanceSolver::new(self.balance_anyway, true).control(qos.clone(), channel_state);
                (name, Action::new(Some(tx_parts), None, Some(channel_colors)))
            }
            else{
                let mut throttle = qos.throttle + self.throttle_step_size;
                if throttle <= 0.0 {
                    throttle = 1.0;
                } else if throttle >= 300.0 {
                    throttle = 300.0;
                }
                (name, Action::new(None, Some(throttle), Some(channel_colors)))
            }
        }).collect();
        let ctrl_state = CtlState::Normal;
        (controls, ctrl_state, None)

    }
}

fn determine_back_switch(qoses: &HashMap<String, Qos>, alpha: f64) -> Option<&String>{
    let mut back_switch_task = None;
    for (name, qos) in qoses {
        if let Some(channel_rtts) = qos.channel_rtts.clone() {
            let tx_parts = qos.tx_parts.clone();
            let target_rtt = qos.target_rtt;
        
            if channel_rtts[0] == 0.0 || channel_rtts[1] == 0.0 {
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

pub struct GRSolver {
    #[warn(dead_code)]
    pub backward_threshold: f64,
    pub balance_anyway: bool,
    pub throttle_step_size: f64,
}

#[allow(dead_code)]
impl GRSolver {
    pub fn new() -> Self {
        GRSolver {
            backward_threshold: 0.8,
            balance_anyway: false,
            throttle_step_size: 10.0,
        }
    }
}

impl DecSolver for GRSolver{
    fn control(&self, qoses: HashMap<String, Qos>, channel_state: &State) -> CtlRes {
        let controls = qoses.into_iter().map(|(name, qos)| {
            let channel_colors: Vec<Color> = qos.channels.iter()
                .filter_map(|channel| channel_state.color.get(channel).cloned())
                .collect();
            if qos.channel_rtts.is_some(){
                let tx_parts = ChannelBalanceSolver::new(self.balance_anyway, false).control(qos.clone(), channel_state);
                (name, Action::new(Some(tx_parts), None, Some(channel_colors)))
            }
            else{
                let mut throttle = qos.throttle - self.throttle_step_size;
                if throttle <= 0.0 {
                    throttle = 1.0;
                } else if throttle >= 300.0 {
                    throttle = 300.0;
                }
                (name, Action::new(None, Some(throttle), Some(channel_colors)))
            }
        }).collect();
        (controls, CtlState::Normal, None)
    }
}

pub struct ChannelBalanceSolver {
    inc_direction: [i32; 2],
    min_step: f64,
    epsilon_rtt: f64,
    epsilon_prob_upper: f64,
    epsilon_prob_lower: f64,
    redundency_mode: bool,
    balance_anyway: bool,
    stick_to_original: bool,
}

impl ChannelBalanceSolver {
    fn new(balance_anyway: bool, stick_to_original: bool) -> Self {
        ChannelBalanceSolver {
            inc_direction: [-1, 1],
            min_step: 0.05,
            epsilon_rtt: 0.002,
            epsilon_prob_upper: 0.6,
            epsilon_prob_lower: 0.01,
            redundency_mode: false,
            balance_anyway,
            stick_to_original: stick_to_original,
        }
    }

    fn control(&mut self, qos: Qos, channel_state: &State) -> Vec<f64> {
        if self.redundency_mode {
            self.redundency_balance(qos)
        } else {
            self.solve_by_rtt_balance(qos, channel_state)
        }
    }

    fn solve_by_rtt_balance(&mut self, qos: Qos, channel_state: &State) -> Vec<f64> {
        let mut tx_parts = qos.tx_parts.clone();


        if let Some(channel_rtts) = qos.channel_rtts {
            if self.stick_to_original && qos.tx_parts.iter().any(|&tx_part| tx_part == 0.0 || tx_part == 1.0) {
                return tx_parts;
            }

            if (channel_rtts[0] - channel_rtts[1]).abs() > self.epsilon_rtt {
                let direction = if channel_rtts[0] > channel_rtts[1] { 1 } else { 0 };

                // if the direction is toward yellow or red channel, stop it
                if !self.balance_anyway && channel_state.color.get(&qos.channels[direction]).cloned() == Some(Color::Red) {
                    return tx_parts;
                }

                tx_parts[0] += if channel_rtts[0] > channel_rtts[1] { -self.min_step } else { self.min_step };
                tx_parts[0] = format!("{:.2}", tx_parts[0].clamp(0.0, 1.0)).parse().unwrap();
                tx_parts[1] = tx_parts[0];
            }
        }

        tx_parts
    }

    fn redundency_balance(&mut self, qos: Qos) -> Vec<f64> {
        let mut tx_parts = qos.tx_parts.clone();
        if let Some(channel_probabilities) = qos.channel_probabilities {
            for (idx, &pro) in channel_probabilities.iter().enumerate() {
                assert!((0.0..=1.0).contains(&pro), "Invalid probability: {}, should be in [0, 1]", pro);
                if pro > self.epsilon_prob_upper {
                    tx_parts[idx] += self.min_step * self.inc_direction[idx] as f64;
                } else if pro < self.epsilon_prob_lower {
                    tx_parts[idx] -= self.min_step * self.inc_direction[idx] as f64;
                }
                tx_parts[idx] = (tx_parts[idx].max(0.0).min(1.0) * 100.0).round() / 100.0;
            }
        }

        tx_parts
    }
}