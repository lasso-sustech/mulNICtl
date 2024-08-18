use crate::{types::{paramter::HYPER_PARAMETER, qos::Qos}, HisQos};

use super::{checker::determine_forward_switch, forward_switch_solver::forward_predict};

pub struct ChannelBalanceSolver {
    inc_direction: [i32; 2],
    min_step: f64,
    max_step: f64,
    epsilon_rtt: f64,
    scale_factor: f64,
    epsilon_prob_upper: f64,
    epsilon_prob_lower: f64,
    redundency_mode: bool,
}

impl ChannelBalanceSolver {
    pub fn new() -> Self {
        ChannelBalanceSolver {
            inc_direction: [-1, 1],
            min_step: 0.05,
            max_step: HYPER_PARAMETER.scale_factor * HYPER_PARAMETER.balance_channel_rtt_thres / HYPER_PARAMETER.epsilon_rtt,
            epsilon_rtt: HYPER_PARAMETER.epsilon_rtt,
            scale_factor: HYPER_PARAMETER.scale_factor,
            epsilon_prob_upper: 0.6,
            epsilon_prob_lower: 0.01,
            redundency_mode: false,
        }
    }

    pub fn control(&mut self, qos: Qos, his_qoses: &HisQos, name: String) -> Vec<f64> {
        if self.redundency_mode {
            self.redundency_balance(qos)
        } else {
            self.solve_by_rtt_balance(qos, his_qoses, name)
        }
    }

    fn solve_by_rtt_balance(&mut self, qos: Qos, his_qoses: &HisQos, name: String) -> Vec<f64> {
        let mut tx_parts = qos.tx_parts.clone();

        if let (Some(channel_rtts), Some(_rtt)) = (qos.channel_rtts, qos.rtt){

            let diff = (channel_rtts[0] - channel_rtts[1]).abs();

            if diff <= self.epsilon_rtt {
                return tx_parts;
            }
            else if diff < HYPER_PARAMETER.balance_channel_rtt_thres{
                let step = self.min_step * self.scale_factor * diff / self.epsilon_rtt;
                tx_parts[0] += if channel_rtts[0] > channel_rtts[1] { -step } else { step };
                tx_parts[0] = format!("{:.2}", tx_parts[0].clamp(0.0, 1.0)).parse().unwrap();
                tx_parts[1] = tx_parts[0];
                return tx_parts;
            }
            else if determine_forward_switch(his_qoses, &name) {
                return forward_predict(his_qoses, &name);
            }
            else {
                let step = self.max_step;
                tx_parts[0] += if channel_rtts[0] > channel_rtts[1] { -step } else { step };
                tx_parts[0] = format!("{:.2}", tx_parts[0].clamp(0.0, 1.0)).parse().unwrap();
                tx_parts[1] = tx_parts[0];
                return tx_parts;
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