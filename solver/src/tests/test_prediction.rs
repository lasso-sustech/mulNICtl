#![allow(non_snake_case)]
#[cfg(test)]
mod tests {
    use ndarray::array;
    use crate::cores::prediction::LinearRegression;

    #[test]
    fn test_fit_single_feature() {
        let X = array![[1.0], [2.0], [3.0], [4.0], [5.0]];
        let y = array![1.0, 2.0, 3.0, 4.0, 5.0];
        
        let mut lr = LinearRegression::new();
        lr.fit(&X, &y);

        // Assert that beta is not None
        assert!(lr.beta.is_some());
        
        // Since this is a perfect fit, we expect beta to be [0, 1] (intercept 0, slope 1)
        let expected_beta = array![0.0, 1.0];
        assert_eq!(lr.beta.unwrap(), expected_beta);
    }

    #[test]
    fn test_predict_single_feature() {
        let X_train = array![[1.0], [2.0], [3.0], [4.0], [5.0]];
        let y_train = array![1.0, 2.0, 3.0, 4.0, 5.0];
        
        let mut lr = LinearRegression::new();
        lr.fit(&X_train, &y_train);

        let X_test = array![[6.0], [7.0], [8.0]];
        let y_pred = lr.predict(&X_test);
        
        let expected_y_pred = array![6.0, 7.0, 8.0];
        assert_eq!(y_pred, expected_y_pred);
    }

    #[test]
    #[should_panic(expected = "The linear regression estimator has to be fitted first!")]
    fn test_predict_without_fit() {
        let lr = LinearRegression::new();
        let X_test = array![[6.0], [7.0], [8.0]];
        lr.predict(&X_test); // This should panic
    }

    #[test]
    #[should_panic(expected = "The matrix is singular and cannot be inverted!")]
    fn test_singular_matrix() {
        let X = array![[1.0, 2.0], [1.0, 2.0], [1.0, 2.0]]; // Singular matrix
        let y = array![1.0, 2.0, 3.0];
        
        let mut lr = LinearRegression::new();
        lr.fit(&X, &y); // This should panic
    }
}
