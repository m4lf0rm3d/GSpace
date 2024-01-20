
# GSpace: Seamless Cross-Platform File Synchronization with Google Drive

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![GitHub issues](https://img.shields.io/github/issues/m4lf0rm3d/GSpace)](https://github.com/m4lf0rm3d/GSpace/issues)
[![GitHub stars](https://img.shields.io/github/stars/m4lf0rm3d/GSpace)](https://github.com/m4lf0rm3d/GSpace/stargazers)

## Overview

GSpace is an efficient and unified solution for synchronizing files across multiple devices using the power of Google Drive APIs. While Google Drive offers a desktop application for file synchronization, GSpace extends this capability to Android and Linux platforms, providing a seamless experience for users across diverse environments.

## Features

- **One-Command Syncing:** With GSpace, file synchronization is simplified to a single command, streamlining the process across all supported platforms.
  
- **Cross-Platform Compatibility:** GSpace brings Google Drive syncing to Android and Linux, ensuring a consistent experience for users regardless of the device they are using.

- **Efficient API Integration:** Leveraging the Google Drive API services, GSpace optimizes file transfers and updates, minimizing bandwidth usage and maximizing efficiency.

- **Customizable Configuration:** Tailor the synchronization process to meet your specific needs with a range of configurable options, allowing users to control the frequency and types of files synced.

- **Fetch:** See changes considering main is Google Drive.
  
- **Push:** Push local filesystem changes to Google Drive.

- **Pull:** Pull changes from Google Drive to the local file system.

- **Sync:** Perform a pull followed by a push.

- **Logging System:** GSpace includes a logging system to track and review synchronization activities without the need to delve into the code.

## Getting Started

1. Clone the repository: `git clone https://github.com/m4lf0rm3d/GSpace.git`
2. Navigate to the project directory: `cd GSpace`
3. Install dependencies: `pip install -r requirements.txt`
4. Enable Google Drive API for your account and download the credentials JSON file. Provide the file path in `settings.conf`.
5. Customize other settings in `settings.conf` according to your preferences.
6. Run GSpace with the desired command: `python3 GSpace.py <command>`

   - Commands:
     - `fetch`: See changes considering the main is Google Drive.
     - `push`: Push local filesystem changes to Google Drive.
     - `pull`: Pull changes from Google Drive to the local file system.
     - `sync`: Perform a pull followed by a push.


## Command Line Usage
- For Linux, MacOS, and Windows, use the command line.
- For Android, Termux can be a great option.
```bash
python3 GSpace.py <command> 
```

## Contributions and Issues

Contributions to GSpace are welcome! If you encounter any issues or have suggestions for improvement, please open an issue on the GitHub repository. Feel free to fork the project and submit pull requests to contribute to its development.

## License

GSpace is licensed under the MIT License.