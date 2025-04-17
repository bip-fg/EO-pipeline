SATELLITE IMAGE PROCESSING PROJECT
==================================

DESCRIPTION
-----------
This project is a modular pipeline for processing satellite images.
It includes:
- Data download
- Preprocessing
- Image segmentation
- Classification
- Result analysis

FOLDER STRUCTURE
----------------
EO Pipeline/
├── src/
│   ├── main/
│   │   ├── preprocessing/
│   │   │   ├── __init__.py
│   │   │   └── preprocessing.py
│   │   ├── __init__.py
│   │   └── download.py
│   └── auxiliary/
│       ├── __init__.py
│       ├── unzip_utils.py
│       └── band_utils.py
├── data/
│   ├── raw/                 # Downloaded Sentinel-2 data
│   ├── L2/                  # Unzipped L2A products
│   └── preprocessed/        # Processed band data
├── config/
│   └── config.yaml         # Configuration settings
├── results/
│   └── logs/              # Pipeline logs
└── requirements.txt       # Python dependencies

project-root/
│
├── data/
│   ├── raw/             # Raw downloaded data
│   ├── processed/       # Final outputs
│   ├── intermediate/    # Optional intermediate steps
│   └── external/        # External datasets (shapefiles, DEM, etc.)
│
├── src/
│   ├── main/            # Core processing scripts
│   ├── auxiliary/       # Utility and config modules
│   └── main.py          # Pipeline entry point
│
├── notebooks/           # Jupyter notebooks for testing
├── models/              # Trained machine learning models
├── results/             # Analysis outputs (figures, reports, logs)
├── config/              # Configuration files
├── environment/         # Python/Conda environment files
└── README.txt           # This file

REQUIREMENTS
Python 3.8 or higher

Dependencies as listed in environment/requirements.txt or environment.yml

ENVIRONMENT SETUP USING POWERSHELL
This project includes a PowerShell script (setup_env.ps1) to automate the environment setup. Follow these steps:

Open the project root folder in VS Code.

Open the integrated PowerShell terminal.

(Temporarily) Allow script execution for the session by running:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Run the script by entering:

.\setup_env.ps1

The script does the following:

Creates a virtual environment in a folder specified by the variable "venvDir". (By default, venvDir = ".venv".)

Activates the virtual environment.

Upgrades pip and installs packages from environment\requirements.txt.

Checks for mandatory packages (rasterio, numpy, matplotlib, sentinelsat) and installs them if missing, appending them to the requirements file if necessary.

CHANGING THE VIRTUAL ENVIRONMENT NAME
To change the name of your virtual environment:

Open the file setup_env.ps1 in a text editor.

Find the line:

$venvDir = ".venv"

Replace ".venv" with your desired folder name (e.g., "myenv").

RUNNING THE PIPELINE
Adjust configuration parameters in config/config.yaml.

With the virtual environment activated, run the main pipeline script:

python src/main.py

CONTRIBUTING
Feel free to fork the repository, create a feature branch, and submit pull requests for improvements or fixes.

LICENSE
This project is licensed under the MIT License.

CONTACT
For questions or suggestions, please contact Filippo Galassi at filippo.galassi@bip-group.com


