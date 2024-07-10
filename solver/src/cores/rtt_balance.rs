use std::collections::HashMap;

use crate::{action::Action, qos::Qos, state::State, Solver};

pub struct RttBalanceSolver;

impl Solver for RttBalanceSolver{
    fn control(&self, qoses: HashMap<String, Qos>, channel_state: &State) -> HashMap<String, Action> {
        qoses.into_iter().map(|(name, qos)| {
            let tx_parts = ChannelBalanceSolver::new().control(qos.clone());
            let channel_colors = qos.channels.iter()
                .filter_map(|channel| channel_state.color.get(channel).cloned())
                .collect();
            (name, Action::new(Some(tx_parts), None, channel_colors))
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
}

impl ChannelBalanceSolver {
    fn new() -> Self {
        ChannelBalanceSolver {
            inc_direction: [-1, 1],
            min_step: 0.05,
            epsilon_rtt: 0.002,
            epsilon_prob_upper: 0.6,
            epsilon_prob_lower: 0.01,
            redundency_mode: false,
        }
    }

    fn control(&mut self, qos: Qos) -> Vec<f64> {
        if self.redundency_mode {
            self.redundency_balance(qos)
        } else {
            self.solve_by_rtt_balance(qos)
        }
    }

    fn solve_by_rtt_balance(&mut self, qos: Qos) -> Vec<f64> {
        let mut tx_parts = qos.tx_parts.clone();
        assert_eq!(tx_parts.len(), 2, "TX parts should have 2 parts");
        assert_eq!(tx_parts[0], tx_parts[1], "In rtt balance mode, TX parts should be the same");

        if qos.channel_rtts.iter().any(|&rtt| rtt == 0.0) {
            return tx_parts;
        }

        if (qos.channel_rtts[0] - qos.channel_rtts[1]).abs() > self.epsilon_rtt {
            tx_parts[0] += if qos.channel_rtts[0] > qos.channel_rtts[1] { self.min_step } else { -self.min_step };
            tx_parts[0] = (tx_parts[0].max(0.0).min(1.0) * 100.0).round() / 100.0;
            tx_parts[1] = tx_parts[0];
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