use std::process::Stdio;
use std::sync::Mutex;

use tauri::{Manager, State};
use tokio::process::{Child, Command};
use tokio::time::{sleep, Duration};

// ---------------------------------------------------------------------------
// Sidecar manager
// ---------------------------------------------------------------------------

struct PythonSidecar {
    child: Mutex<Option<Child>>,
}

impl PythonSidecar {
    fn new() -> Self {
        Self {
            child: Mutex::new(None),
        }
    }

    async fn start(&self) -> Result<(), String> {
        let mut guard = self.child.lock().map_err(|e| e.to_string())?;

        if guard.is_some() {
            return Ok(()); // already running
        }

        let child = Command::new("python3")
            .arg("-m")
            .arg("server.main")
            .current_dir(env!("CARGO_MANIFEST_DIR").to_string() + "/../..")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .kill_on_drop(true)
            .spawn()
            .map_err(|e| format!("Failed to start Python sidecar: {}", e))?;

        *guard = Some(child);
        Ok(())
    }

    async fn health_check(&self, port: u16) -> Result<bool, String> {
        let url = format!("http://127.0.0.1:{}/api/health", port);
        let client = reqwest::Client::new();
        match client.get(&url).timeout(Duration::from_secs(2)).send().await {
            Ok(resp) => Ok(resp.status().is_success()),
            Err(_) => Ok(false),
        }
    }

    async fn shutdown(&self) {
        if let Ok(mut guard) = self.child.lock() {
            if let Some(ref mut child) = *guard {
                let _ = child.kill().await;
            }
            *guard = None;
        }
    }
}

// ---------------------------------------------------------------------------
// Tauri commands
// ---------------------------------------------------------------------------

#[tauri::command]
async fn get_server_status(sidecar: State<'_, PythonSidecar>) -> Result<String, String> {
    let port = 9876u16;
    match sidecar.health_check(port).await {
        Ok(true) => Ok("connected".into()),
        Ok(false) => Ok("disconnected".into()),
        Err(e) => Err(e),
    }
}

#[tauri::command]
async fn restart_sidecar(sidecar: State<'_, PythonSidecar>) -> Result<(), String> {
    sidecar.shutdown().await;
    sleep(Duration::from_secs(1)).await;
    sidecar.start().await?;

    // Wait for server to become ready (max 30s)
    for _ in 0..60 {
        if sidecar.health_check(9876).await.unwrap_or(false) {
            return Ok(());
        }
        sleep(Duration::from_millis(500)).await;
    }
    Err("Server did not become ready within 30 seconds".into())
}

// ---------------------------------------------------------------------------
// App setup
// ---------------------------------------------------------------------------

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive("depth_video_converter=info".parse().unwrap()),
        )
        .init();

    let sidecar = PythonSidecar::new();

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(sidecar)
        .setup(|app| {
            let sidecar: State<PythonSidecar> = app.state();

            // Spawn sidecar on startup
            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                tracing::info!("Starting Python sidecar…");

                if let Err(e) = sidecar.start().await {
                    tracing::error!("Failed to start sidecar: {}", e);
                    return;
                }

                // Wait for health
                for i in 0..60 {
                    match sidecar.health_check(9876).await {
                        Ok(true) => {
                            tracing::info!("Sidecar ready (port 9876)");
                            // Emit event to frontend
                            let _ = handle.emit("sidecar-ready", true);
                            return;
                        }
                        Ok(false) => {
                            tracing::debug!("Waiting for sidecar… attempt {}", i + 1);
                        }
                        Err(e) => {
                            tracing::warn!("Health check error: {}", e);
                        }
                    }
                    sleep(Duration::from_millis(500)).await;
                }
                tracing::error!("Sidecar did not become ready within 30s");
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                let sidecar: State<PythonSidecar> = window.state();
                tauri::async_runtime::block_on(async {
                    tracing::info!("Shutting down Python sidecar…");
                    sidecar.shutdown().await;
                });
            }
        })
        .invoke_handler(tauri::generate_handler![
            get_server_status,
            restart_sidecar,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
