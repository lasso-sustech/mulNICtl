mod test {
    #[test]
    #[ignore]
    fn statistics() {
        use crate::api::ipc::IPCController;

        // Create an IPCController
        let ipc = IPCController::new(String::from("127.0.0.1"), 11112);
        let statistic = ipc.statistics();

        // Print the statistics
        println!("statistic: {:?}", statistic);
    }

    #[test]
    #[ignore]
    fn throttle() {
        use crate::api::ipc::IPCController;
        use std::collections::HashMap;
        // Create an IPCController
        let ipc = IPCController::new(String::from("127.0.0.1"), 11112);

        let statistic = ipc.statistics();

        // Print the statistics
        println!("statistic: {:?}", statistic);

        let throttle_val = HashMap::from([(String::from("6207@128"), 20 as f32)]);
        let _ = ipc.throttle(throttle_val);

        // sleep for 1 second
        std::thread::sleep(std::time::Duration::from_secs(1));

        let statistic = ipc.statistics();

        // Print the statistics
        println!("statistic: {:?}", statistic);
    }

    #[test]
    #[ignore]
    fn tx_part(){
        use crate::api::ipc::IPCController;
        use std::collections::HashMap;

        // Create an IPCController
        let ipc = IPCController::new(String::from("127.0.0.1"), 11112);

        let statistic = ipc.statistics();

        // Print the statistics
        println!("statistic: {:?}", statistic);

        let tx_part_val = HashMap::from([(String::from("6207@128"), [0.5, 0.5])]);
        let _ = ipc.tx_part(tx_part_val);

        // sleep for 1 second
        std::thread::sleep(std::time::Duration::from_secs(1));

        let statistic = ipc.statistics();

        // Print the statistics
        println!("statistic: {:?}", statistic);
    }
}