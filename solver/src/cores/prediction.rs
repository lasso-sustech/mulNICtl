#![allow(non_snake_case)]
use ndarray::{concatenate, s, Array, Array1, ArrayBase, Axis, Data, Ix1, Ix2};
use ndarray_linalg::Solve;

/// The simple linear regression model is
///     y = bX + e  where e ~ N(0, sigma^2 * I)
/// In probabilistic terms this corresponds to
///     y - bX ~ N(0, sigma^2 * I)
///     y | X, b ~ N(bX, sigma^2 * I)
/// The loss for the model is simply the squared error between the model
/// predictions and the true values:
///     Loss = ||y - bX||^2
/// The maximum likelihood estimation for the model parameters `beta` can be computed
/// in closed form via the normal equation:
///     b = (X^T X)^{-1} X^T y
/// where (X^T X)^{-1} X^T is known as the pseudoinverse or Moore-Penrose inverse.
///
/// Adapted from: https://github.com/ddbourgin/numpy-ml
pub struct LinearRegression {
    pub beta: Option<Array1<f64>>,
}

impl LinearRegression {
    pub fn new() -> LinearRegression {
        LinearRegression {
            beta: None,
        }
    }

    /// Given:
    /// - an input matrix `X`, with shape `(n_samples, n_features)`;
    /// - a target variable `y`, with shape `(n_samples,)`;
    /// `fit` tunes the `beta` parameter of the linear regression model
    /// to match the training data distribution.
    ///
    /// `self` is modified in place, nothing is returned.
    pub fn fit<A, B>(&mut self, X: &ArrayBase<A, Ix2>, y: &ArrayBase<B, Ix1>)
    where
        A: Data<Elem = f64>,
        B: Data<Elem = f64>,
    {
        let (n_samples, _) = X.dim();

        // Check that our inputs have compatible shapes
        assert_eq!(y.dim(), n_samples);

        // If we are fitting the intercept, we need an additional column
        self.beta = {
            let dummy_column: Array<f64, _> = Array::ones((n_samples, 1));
            let X = concatenate(Axis(1), &[dummy_column.view(), X.view()]).unwrap();
            Some(LinearRegression::solve_normal_equation(&X, y))
        }
    }

    /// Given an input matrix `X`, with shape `(n_samples, n_features)`,
    /// `predict` returns the target variable according to linear model
    /// learned from the training data distribution.
    ///
    /// **Panics** if `self` has not be `fit`ted before calling `predict.
    pub fn predict<A>(&self, X: &ArrayBase<A, Ix2>) -> Array1<f64>
    where
        A: Data<Elem = f64>,
    {
        let (n_samples, _) = X.dim();

        // If we are fitting the intercept, we need an additional column
        let dummy_column: Array<f64, _> = Array::ones((n_samples, 1));
        let X = concatenate(Axis(1), &[dummy_column.view(), X.view()]).unwrap();
        self._predict(&X)
    }

    fn solve_normal_equation<A, B>(X: &ArrayBase<A, Ix2>, y: &ArrayBase<B, Ix1>) -> Array1<f64>
    where
        A: Data<Elem = f64>,
        B: Data<Elem = f64>,
    {
        let rhs = X.t().dot(y);
        let linear_operator = X.t().dot(X);
        // print the inversion of linear_operator
        let res = linear_operator.solve_into(rhs);
        if res.is_err() {
            println!("Linear operator: {:?}", linear_operator);
            panic!("The matrix is singular and cannot be inverted!");
        }
        res.unwrap()
    }

    fn _predict<A>(&self, X: &ArrayBase<A, Ix2>) -> Array1<f64>
    where
        A: Data<Elem = f64>,
    {
        match &self.beta {
            None => panic!("The linear regression estimator has to be fitted first!"),
            Some(beta) => X.dot(beta),
        }
    }

    /// Find the x values that minimize the absolute difference
    /// between two linear regression models for general beta.
    pub fn find_min_difference_x(&self, other: &LinearRegression) -> Option<Array1<f64>> {
        if let (Some(beta1), Some(beta2)) = (&self.beta, &other.beta) {
            let delta_beta = beta1 - beta2;
            let delta_intercept = delta_beta[0]; // Difference in intercept (b1 - b2)

            if delta_beta.slice(s![1..]).iter().all(|&x| x == 0.0) {
                return None; // Parallel lines with identical slopes
            }

            // Convert the view to an owned array
            let delta_beta_owned = delta_beta.slice(s![1..]).to_owned();

            if delta_beta_owned.iter().all(|&x| x == 0.0) {
                return None; // Parallel lines with identical slopes
            }

            // Solve for x values
            let x_values = -delta_intercept / delta_beta_owned;
            Some(x_values)
        } else {
            None // One or both models are not fitted
        }
    }
}