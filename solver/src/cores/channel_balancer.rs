use crate::types::{paramter::HYPER_PARAMETER, qos::Qos, state::{Color, State}};

use super::degration_checker::check_degration;

pub struct ChannelBalanceSolver {
    inc_direction: [i32; 2],
    min_step: f64,
    epsilon_rtt: f64,
    scale_factor: f64,
    epsilon_prob_upper: f64,
    epsilon_prob_lower: f64,
    redundency_mode: bool,
    balance_anyway: bool,
    stick_to_original: bool,
}

impl ChannelBalanceSolver {
    pub fn new(balance_anyway: bool, stick_to_original: bool) -> Self {
        ChannelBalanceSolver {
            inc_direction: [-1, 1],
            min_step: 0.05,
            epsilon_rtt: HYPER_PARAMETER.epsilon_rtt,
            scale_factor: HYPER_PARAMETER.scale_factor,
            epsilon_prob_upper: 0.6,
            epsilon_prob_lower: 0.01,
            redundency_mode: false,
            balance_anyway,
            stick_to_original: stick_to_original,
        }
    }

    pub fn control(&mut self, qos: Qos, channel_state: &State) -> Vec<f64> {
        if self.redundency_mode {
            self.redundency_balance(qos)
        } else {
            self.solve_by_rtt_balance(qos, channel_state)
        }
    }

    fn solve_by_rtt_balance(&mut self, qos: Qos, channel_state: &State) -> Vec<f64> {
        let mut tx_parts = qos.tx_parts.clone();

        if let (Some(channel_rtts), Some(rtt)) = (qos.channel_rtts, qos.rtt) {

            if check_degration(&channel_rtts, &tx_parts, rtt){
                return vec![1.0, 1.0];
            }

            if self.stick_to_original && qos.tx_parts.iter().any(|&tx_part| tx_part == 0.0 || tx_part == 1.0) {
                return tx_parts;
            }

            if (channel_rtts[0] - channel_rtts[1]).abs() > self.epsilon_rtt {
                let direction = if channel_rtts[0] > channel_rtts[1] { 1 } else { 0 };

                // if the direction is toward yellow or red channel, stop it
                if !self.balance_anyway && channel_state.color.get(&qos.channels[direction]).cloned() == Some(Color::Red) {
                    return tx_parts;
                }
            
                let step = self.min_step * self.scale_factor * (channel_rtts[0] - channel_rtts[1]).abs() / self.epsilon_rtt;
                tx_parts[0] += if channel_rtts[0] > channel_rtts[1] { -step } else { step };
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