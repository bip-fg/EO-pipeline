# setup_env.ps1
# This script sets up a Python virtual environment and installs required packages.

# CONFIGURATION
$venvDir = ".venv"
$requirementsFile = "serequirements.txt"
$mandatoryPackages = @("rasterio", "numpy", "matplotlib", "sentinelsat")

# Create the virtual environment if it doesn't exist.
if (-Not (Test-Path $venvDir)) {
    Write-Host "Creating virtual environment in $venvDir..."
    python -m venv $venvDir
} else {
    Write-Host "Virtual environment already exists."
}

# Activate the environment.
Write-Host "Activating environment..."
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& "$venvDir\Scripts\Activate.ps1"

# Install packages from the requirements file.
if (Test-Path $requirementsFile) {
    Write-Host "Installing packages from $requirementsFile..."
    pip install --upgrade pip
    pip install -r $requirementsFile
} else {
    Write-Host "Requirements file not found at $requirementsFile"
}

# Install and append mandatory packages if missing.
foreach ($pkg in $mandatoryPackages) {
    if (-Not (pip show $pkg 2>$null)) {
        Write-Host "Installing missing package: $pkg"
        pip install $pkg
        if (-Not (Select-String -Path $requirementsFile -Pattern "^$pkg" -Quiet)) {
            Add-Content -Path $requirementsFile -Value $pkg
            Write-Host "Added $pkg to $requirementsFile"
        }
    } else {
        Write-Host "$pkg is already installed."
    }
}

# Final message.
Write-Host ""
Write-Host "Environment setup complete."
Write-Host "To activate the environment later, run:"
Write-Host "$venvDir\Scripts\Activate.ps1"
