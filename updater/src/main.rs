use std::{io::Read, path::Path};
use reqwest;
use tokio;
use chrono;


mod updater;


fn pause() -> std::io::Result<usize> {
	let mut stdin = std::io::stdin();
	return stdin.read(&mut [0u8]);
}

#[tokio::main]
async fn main() {
	let downloads = Path::new(&std::env::var("UPDATER_DOWNLOAD_DIR").unwrap_or(String::from(std::env::current_dir().unwrap().join("binder").to_str().unwrap()))).to_path_buf();

	let tool = updater::Updater {
		download_path: downloads.clone(),
		update_base_url: reqwest::Url::parse("https://github.com/JudeDM/binder/raw/files/").unwrap(),
		checksum_url: reqwest::Url::parse("https://raw.githubusercontent.com/JudeDM/binder/main/info.json").unwrap(),
	};

	let checksum = match tool.update().await {
		Ok(checksum) => checksum,
        Err(e) => {
            println!("Произошла ошибка!\n{}", e.to_string());
            pause().unwrap();
            return;
        }
	};

	if (!checksum.outdated_files.is_empty()) {
		let datetime = checksum.last_updated.with_timezone(&chrono::Local);
		println!("Последнее обновление: {}", datetime.format("%d.%m.%Y, %H:%M:%S").to_string());
	} else {
		println!("Уже установлена последняя версия!");
	}

	println!("Нажмите Enter для завершения");
	pause().unwrap();
}
