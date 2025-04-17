# AWS Setup Guide for Sentinel-2 Downloads

## 1. Install Required Python Packages
```powershell
pip install boto3==1.26.137 botocore==1.29.137 pandas requests
```

## 2. Create AWS Credentials File
```powershell
# Create .aws directory
mkdir "$env:USERPROFILE\.aws"

# Create credentials file
@"
[default]
aws_access_key_id = anonymous
aws_secret_access_key = anonymous
"@ | Out-File -FilePath "$env:USERPROFILE\.aws\credentials" -Encoding UTF8

# Create config file
@"
[default]
region = eu-central-1
output = json
"@ | Out-File -FilePath "$env:USERPROFILE\.aws\config" -Encoding UTF8
```

## 3. Verify AWS Configuration
```powershell
# Test AWS configuration
$env:AWS_NO_SIGN_REQUEST = "YES"
python -c "import boto3; s3 = boto3.client('s3'); print(s3.list_buckets())"
```

## 4. Set Environment Variable Permanently
```powershell
# Set system-wide environment variable
[System.Environment]::SetEnvironmentVariable("AWS_NO_SIGN_REQUEST", "YES", "User")
```

## 5. Run Download Script
```powershell
# Create required directories
mkdir -Force data/processed/Sentinel-2/L2A
mkdir -Force data/intermediate
mkdir -Force results/logs

# Run the download script
python src/main/download.py
```

## Troubleshooting
- If you get credentials errors, restart Visual Studio Code after setting up the credentials
- Verify the credentials files exist:
  ```powershell
  Get-Content "$env:USERPROFILE\.aws\credentials"
  Get-Content "$env:USERPROFILE\.aws\config"
  ```
- Check if environment variable is set:
  ```powershell
  Get-ChildItem Env:AWS_NO_SIGN_REQUEST
  ```


& 'C:\Program Files\Amazon\AWSCLIV2\aws.exe' --version
& 'C:\Program Files\Amazon\AWSCLIV2\aws.exe' configure