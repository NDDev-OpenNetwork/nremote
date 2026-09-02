use std::{
    path::{Component, Path, PathBuf},
    sync::atomic::{AtomicUsize, Ordering},
};

static CONTROLLING_SESSION_COUNT: AtomicUsize = AtomicUsize::new(0);

pub fn update_controlling_session_count(count: usize) {
    CONTROLLING_SESSION_COUNT.store(count, Ordering::SeqCst);
}

/// Returns true when there are no active incoming or outgoing connections.
/// Manual installation paths use this to avoid replacing the application
/// during a remote session.
pub fn has_no_active_conns() -> bool {
    let conns = crate::Connection::alive_conns();
    conns.is_empty() && has_no_controlling_conns()
}

#[cfg(any(not(target_os = "windows"), feature = "flutter"))]
fn has_no_controlling_conns() -> bool {
    CONTROLLING_SESSION_COUNT.load(Ordering::SeqCst) == 0
}

#[cfg(not(any(not(target_os = "windows"), feature = "flutter")))]
fn has_no_controlling_conns() -> bool {
    let app_exe = format!("{}.exe", crate::get_app_name().to_lowercase());
    for arg in [
        "--connect",
        "--play",
        "--file-transfer",
        "--view-camera",
        "--port-forward",
        "--rdp",
    ] {
        if !crate::platform::get_pids_of_process_with_first_arg(&app_exe, arg).is_empty() {
            return false;
        }
    }
    true
}

/// Maps a user-selected release asset URL to a temporary destination.
///
/// This is deliberately restricted to this project's GitHub Releases path.
/// The caller performs the download only after an explicit UI action.
pub fn get_download_file_from_url(url: &str) -> Option<PathBuf> {
    let parsed = url::Url::parse(url).ok()?;
    if !url.starts_with("https://github.com/")
        || parsed.scheme() != "https"
        || parsed.host_str() != Some("github.com")
        || !parsed.username().is_empty()
        || parsed.password().is_some()
        || parsed.port().is_some()
        || parsed.query().is_some()
        || parsed.fragment().is_some()
    {
        return None;
    }

    let mut segments = parsed.path_segments()?;
    let owner = segments.next()?;
    let repo = segments.next()?;
    let releases = segments.next()?;
    let download = segments.next()?;
    let tag = segments.next()?;
    let filename = segments.next()?;

    if owner != "NDDev-OpenNetwork"
        || repo != "nremote"
        || releases != "releases"
        || download != "download"
        || tag.is_empty()
        || segments.next().is_some()
        || !is_plain_filename(filename)
    {
        return None;
    }

    Some(std::env::temp_dir().join(filename))
}

fn is_plain_filename(filename: &str) -> bool {
    if filename.is_empty()
        || filename.contains('/')
        || filename.contains('\\')
        || filename.contains(':')
    {
        return false;
    }

    let mut components = Path::new(filename).components();
    matches!(
        components.next(),
        Some(Component::Normal(name)) if name.to_str() == Some(filename)
    ) && components.next().is_none()
}

/// Queries every logged-in user's server process. Any IPC uncertainty fails
/// closed because a manual replacement must not race an active session.
#[cfg(target_os = "macos")]
pub fn has_no_active_conns_ipc() -> bool {
    use hbb_common::tokio;

    let rt = match tokio::runtime::Runtime::new() {
        Ok(rt) => rt,
        Err(_) => return false,
    };
    rt.block_on(async {
        for uid in crate::platform::get_logged_in_uids() {
            let Ok(mut conn) = crate::ipc::connect_for_uid(1000, uid, "").await else {
                return false;
            };
            if conn
                .send(&crate::ipc::Data::HasNoActiveConns(None))
                .await
                .is_err()
            {
                return false;
            }
            match conn.next_timeout(1000).await {
                Ok(Some(crate::ipc::Data::HasNoActiveConns(Some(true)))) => {}
                _ => return false,
            }
        }
        true
    })
}

#[cfg(test)]
mod tests {
    use super::get_download_file_from_url;

    #[test]
    fn accepts_this_projects_release_assets() {
        let file = get_download_file_from_url(
            "https://github.com/NDDev-OpenNetwork/nremote/releases/download/0.1.0/nremote-0.1.0.dmg",
        )
        .expect("valid nremote release asset URL");

        assert_eq!(
            file.file_name().and_then(|name| name.to_str()),
            Some("nremote-0.1.0.dmg")
        );
    }

    #[test]
    fn rejects_other_origins_and_malformed_paths() {
        for url in [
            "http://github.com/NDDev-OpenNetwork/nremote/releases/download/1/nremote.exe",
            "https://example.com/nremote.exe",
            "https://github.com/other/project/releases/download/1/nremote.exe",
            "https://github.com/NDDev-OpenNetwork/nremote/releases/download/1/",
            "https://github.com/NDDev-OpenNetwork/nremote/releases/download/1/nested/nremote.exe",
            "https://github.com/NDDev-OpenNetwork/nremote/releases/download/1/C:nremote.exe",
            "https://user@github.com/NDDev-OpenNetwork/nremote/releases/download/1/nremote.exe",
            "https://github.com:443/NDDev-OpenNetwork/nremote/releases/download/1/nremote.exe",
            "https://github.com/NDDev-OpenNetwork/nremote/releases/download/1/nremote.exe?download=1",
            "https://github.com/NDDev-OpenNetwork/nremote/releases/download/1/nremote.exe#download",
            "not a url",
        ] {
            assert!(get_download_file_from_url(url).is_none(), "{url}");
        }
    }
}
