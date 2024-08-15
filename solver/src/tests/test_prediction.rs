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

    #[test]
    fn test_find_min_difference_x_single_feature() {
        let mut model1 = LinearRegression::new();
        let mut model2 = LinearRegression::new();

        // Single feature data
        let X = array![[1.0], [2.0], [3.0], [4.0], [5.0]];
        let y1 = array![1.0, 2.0, 3.0, 4.0, 5.0];
        let y2 = array![2.0, 4.0, 6.0, 8.0, 10.0];

        model1.fit(&X, &y1);
        model2.fit(&X, &y2);

        let x_min = model1.find_min_difference_x(&model2);
        assert!(x_min.is_some());

        let x_min = x_min.unwrap();
        assert_eq!(x_min.len(), 1);
        assert!((x_min[0] - 0.0).abs() < 1e-9); // The lines should intersect at x = 0.0
    }

    #[test]
    fn test_find_min_difference_x_parallel_lines() {
        let mut model1 = LinearRegression::new();
        let mut model2 = LinearRegression::new();

        // Parallel lines with no intersection (same slopes, different intercepts)
        let X = array![[1.0], [2.0], [3.0], [4.0], [5.0]];
        let y1 = array![1.0, 2.0, 3.0, 4.0, 5.0]; // y = 1.0 + 1.0*x
        let y2 = array![2.0, 3.0, 4.0, 5.0, 6.0]; // y = 2.0 + 1.0*x

        model1.fit(&X, &y1);
        model2.fit(&X, &y2);

        let x_min = model1.find_min_difference_x(&model2);
        println!("{:?}", x_min);
        assert!(x_min.is_none()); // Parallel lines should return None
    }

    #[test]
    fn test_find_min_difference_x_identical_models() {
        let mut model1 = LinearRegression::new();
        let mut model2 = LinearRegression::new();

        // Identical models
        let X = array![[1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [4.0, 5.0], [5.0, 6.0]];
        let y = array![3.0, 5.0, 7.0, 9.0, 11.0]; // y = 1.0 + 1.0*x1 + 1.0*x2

        model1.fit(&X, &y);
        model2.fit(&X, &y);

        let x_min = model1.find_min_difference_x(&model2);
        assert!(x_min.is_none()); // Identical models should return None
    }
}
