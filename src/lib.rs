mod ipc;
mod data;

pub use ipc::IPCController;

#[no_mangle]
pub fn start_controller(target_uri: String) {
    let _content = reqwest::blocking::get(&target_uri).unwrap().text().unwrap();
    let _controller = IPCController::new(target_uri, 12345);
}

#[cfg(target_os="android")]
#[allow(non_snake_case)]
#[allow(dead_code)]
#[no_mangle]
pub extern "system" fn Java_com_github_lasso_1sustech_androidscreencaster_service_RustStreamReplay_start_controller(
    mut env: JNIEnv, _: JClass,
    target_uri: JString,
)
{
    let target_uri = env.get_string(&target_uri).expect("Couldn't get java string!").into();
    start_controller(target_uri);
}

#[test]
fn test_start_controller() {
    start_controller("http://127.0.0.1:5000/test.json".to_string());
}
