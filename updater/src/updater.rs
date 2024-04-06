use reqwest;
use md5::{Md5, Digest};
use hex;
use serde::{Deserialize, Serialize};
use serde_json;
use std::{collections::HashMap, fs, path::PathBuf};
use trauma::{download::Download, downloader::DownloaderBuilder};


type Error = Box<dyn std::error::Error>;


#[derive(Serialize, Deserialize)]
struct ChecksumJSON {
	pub hashes: HashMap<String, String>,
	pub files: Vec<String>,
	pub last_updated: String,
}


pub struct Checksum {
	pub outdated_files: Vec<String>,
	pub last_updated: chrono::DateTime<chrono::Utc>,
}


pub struct Updater {
	pub download_path: PathBuf,
	pub update_base_url: reqwest::Url,
	pub checksum_url: reqwest::Url,
}


impl Updater {
	pub async fn get_checksum(&self) -> Result<Checksum, Error> {
		let checksum_json = self.get_checksum_json().await?;
		let mut outdated_files : Vec<String> = Vec::new();
		for file in checksum_json.files.iter() {
			let local_filepath = self.download_path.join(file);
			if (!local_filepath.exists()) {
				outdated_files.push(file.to_owned());
			}
		}
		for (file, latest_hash) in checksum_json.hashes.iter() {
			let local_filepath = self.download_path.join(file);
			if (!local_filepath.exists()) {
				outdated_files.push(file.to_owned());
				continue;
			}
			let local_hash = Self::md5_sum(&local_filepath).unwrap_or_default();
			if (local_hash != *latest_hash) {
				outdated_files.push(file.to_owned());
			}
		}
		return Ok(Checksum {
			outdated_files: outdated_files,
			last_updated: chrono::DateTime::from_timestamp(checksum_json.last_updated.parse::<i64>()?, 0).unwrap_or_default().with_timezone(&chrono::Utc)
		});
	}

	pub async fn update(&self) -> Result<Checksum, Error> {
		let checksum = self.get_checksum().await?;
		for file in checksum.outdated_files.iter() {
			let filepath = self.download_path.join(file);
			if (filepath.exists()) {
				std::fs::remove_file(filepath).unwrap_or_default();
			}
		}
		let downloads : Vec<Download> = checksum.outdated_files.clone().into_iter().map(
			|file| Download {
				url: self.update_base_url.join(&file).unwrap(),
				filename: file.clone(),
			}
		).collect();
		let downloader_builder = DownloaderBuilder::new().directory(self.download_path.clone());
		let downloader = downloader_builder.build();
		let summary = downloader.download(&downloads).await;
		return Ok(checksum);
	}

	async fn get_checksum_json(&self) -> Result<ChecksumJSON, Error> {
		let cloud_response = reqwest::get(self.checksum_url.clone()).await?;
		let cloud_json : ChecksumJSON = serde_json::from_str(cloud_response.text().await?.trim())?;
		return Ok(cloud_json);
	}

	fn md5_sum(file: &PathBuf) -> Option<String> {
		if (!file.exists()) {
			return None;
		}
		let file_content = match fs::read(file) {
			Ok(result) => result,
            Err(error) => {
                return None;
            }
		};
		let hasher = Md5::new_with_prefix(file_content);
		return Some(hex::encode(hasher.finalize()));
	}
}
