mod ipc;
mod data;

pub use ipc::IPCController;

static mut ENABLE_CONTROLLER: bool = false;

#[no_mangle]
pub fn start_controller(target_uri: String) {
    let _content = reqwest::blocking::get(&target_uri).unwrap().text().unwrap();
    let _controller = IPCController::new(target_uri, 12345);

    loop {
        // check if controller is enabled
        unsafe{
            if ENABLE_CONTROLLER {
                std::thread::sleep(std::time::Duration::from_secs(1));
                continue;
            }
        }

        //TODO: apply controller logic

    }
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

#[cfg(target_os="android")]
#[allow(non_snake_case)]
#[allow(dead_code)]
#[no_mangle]
pub extern "system" fn Java_com_github_lasso_1sustech_androidscreencaster_service_RustStreamReplay_set_controller_status(
    _: JNIEnv, _: JClass,
    status: jboolean,
)
{
    unsafe {
        ENABLE_CONTROLLER = status == 1;
    }
}

#[test]
fn test_start_controller() {
    start_controller("http://127.0.0.1:5000/test.json".to_string());
}
