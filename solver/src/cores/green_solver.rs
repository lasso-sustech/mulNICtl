use std::collections::HashMap;

use crate::{action::Action, qos::Qos, state::State, types::state::Color, Solver};


pub struct GSolver {
    #[warn(dead_code)]
    pub backward_threshold: f64,
    pub is_all_balance: bool,
    pub throttle_step_size: f64,
}

#[allow(dead_code)]
impl GSolver {
    pub fn new() -> Self {
        GSolver {
            backward_threshold: 0.8,
            is_all_balance: false,
            throttle_step_size: 10.0,
        }
    }
}

impl Solver for GSolver{
    fn control(&self, qoses: HashMap<String, Qos>, channel_state: &State) -> HashMap<String, Action> {
        qoses.into_iter().map(|(name, qos)| {
            let channel_colors = qos.channels.iter()
                .filter_map(|channel| channel_state.color.get(channel).cloned())
                .collect();
            if qos.channel_rtts.is_some(){
                let tx_parts = ChannelBalanceSolver::new(self.is_all_balance).control(qos.clone(), channel_state);
                (name, Action::new(Some(tx_parts), None, channel_colors))
            }
            else{
                let mut throttle = qos.throttle + self.throttle_step_size;
                if throttle <= 0.0 {
                    throttle = 1.0;
                }
                (name, Action::new(None, Some(throttle), channel_colors))
            }
        }).collect()
    }
}

pub struct GRSolver {
    #[warn(dead_code)]
    pub backward_threshold: f64,
    pub is_all_balance: bool,
    pub throttle_step_size: f64,
}

#[allow(dead_code)]
impl GRSolver {
    pub fn new() -> Self {
        GRSolver {
            backward_threshold: 0.8,
            is_all_balance: false,
            throttle_step_size: 10.0,
        }
    }
}

impl Solver for GRSolver{
    fn control(&self, qoses: HashMap<String, Qos>, channel_state: &State) -> HashMap<String, Action> {
        qoses.into_iter().map(|(name, qos)| {
            let channel_colors = qos.channels.iter()
                .filter_map(|channel| channel_state.color.get(channel).cloned())
                .collect();
            if qos.channel_rtts.is_some(){
                let tx_parts = ChannelBalanceSolver::new(self.is_all_balance).control(qos.clone(), channel_state);
                (name, Action::new(Some(tx_parts), None, channel_colors))
            }
            else{
                let mut throttle = qos.throttle - self.throttle_step_size;
                if throttle <= 0.0 {
                    throttle = 1.0;
                }
                (name, Action::new(None, Some(throttle), channel_colors))
            }
        }).collect()
    }
}

pub struct ChannelBalanceSolver {
    inc_direction: [i32; 2],
    min_step: f64,
    epsilon_rtt: f64,
    epsilon_prob_upper: f64,
    epsilon_prob_lower: f64,
    redundency_mode: bool,
    is_all_balance: bool,
}

impl ChannelBalanceSolver {
    fn new(is_all_balance: bool) -> Self {
        ChannelBalanceSolver {
            inc_direction: [-1, 1],
            min_step: 0.05,
            epsilon_rtt: 0.002,
            epsilon_prob_upper: 0.6,
            epsilon_prob_lower: 0.01,
            redundency_mode: false,
            is_all_balance: is_all_balance,
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
            if !self.is_all_balance && channel_rtts.iter().any(|&rtt| rtt == 0.0) {
                return tx_parts;
            }

            if (channel_rtts[0] - channel_rtts[1]).abs() > self.epsilon_rtt {
                let direction = if channel_rtts[0] > channel_rtts[1] { 1 } else { 0 };

                // if the direction is toward yellow or red channel, stop it
                if channel_state.color.get(&qos.channels[direction]).cloned() != Some(Color::Green) {
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