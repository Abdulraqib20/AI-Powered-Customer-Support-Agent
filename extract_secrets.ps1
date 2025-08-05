# Extract all Google Cloud secrets and create .env_cloud file

Write-Host "Extracting all Google Cloud secrets..." -ForegroundColor Cyan

# Create .env_cloud file
$envFile = ".env_cloud"

# Clear the file if it exists
if (Test-Path $envFile) {
    Remove-Item $envFile
}

# Add header
Add-Content $envFile "# ====================================================================="
Add-Content $envFile "# GOOGLE CLOUD SECRETS - EXTRACTED FROM SECRET MANAGER"
Add-Content $envFile "# This file contains all secrets used in the cloud deployment"
Add-Content $envFile "# ====================================================================="
Add-Content $envFile ""

Write-Host "Creating .env_cloud file..." -ForegroundColor Yellow

# Database Configuration
Write-Host "Extracting database secrets..." -ForegroundColor Green
Add-Content $envFile "# Database Configuration"

$dbHost = gcloud secrets versions access latest --secret="ai-customer-agent-db_host" 2>$null
if ($dbHost) {
    Add-Content $envFile "DB_HOST=$dbHost"
    Write-Host "DB_HOST extracted" -ForegroundColor Green
}

$dbPort = gcloud secrets versions access latest --secret="ai-customer-agent-db_port" 2>$null
if ($dbPort) {
    Add-Content $envFile "DB_PORT=$dbPort"
    Write-Host "DB_PORT extracted" -ForegroundColor Green
}

$dbName = gcloud secrets versions access latest --secret="ai-customer-agent-db_name" 2>$null
if ($dbName) {
    Add-Content $envFile "DB_NAME=$dbName"
    Write-Host "DB_NAME extracted" -ForegroundColor Green
}

$dbUser = gcloud secrets versions access latest --secret="ai-customer-agent-db_user" 2>$null
if ($dbUser) {
    Add-Content $envFile "DB_USER=$dbUser"
    Write-Host "DB_USER extracted" -ForegroundColor Green
}

$dbPassword = gcloud secrets versions access latest --secret="ai-customer-agent-db_password" 2>$null
if ($dbPassword) {
    Add-Content $envFile "DB_PASSWORD=$dbPassword"
    Write-Host "DB_PASSWORD extracted" -ForegroundColor Green
}

$dbSslMode = gcloud secrets versions access latest --secret="ai-customer-agent-db_sslmode" 2>$null
if ($dbSslMode) {
    Add-Content $envFile "DB_SSLMODE=$dbSslMode"
    Write-Host "DB_SSLMODE extracted" -ForegroundColor Green
}

$dbConnectTimeout = gcloud secrets versions access latest --secret="ai-customer-agent-db_connect_timeout" 2>$null
if ($dbConnectTimeout) {
    Add-Content $envFile "DB_CONNECT_TIMEOUT=$dbConnectTimeout"
    Write-Host "DB_CONNECT_TIMEOUT extracted" -ForegroundColor Green
}

Add-Content $envFile ""

# Redis Configuration
Write-Host "Extracting Redis secrets..." -ForegroundColor Green
Add-Content $envFile "# Redis Configuration"

$redisHost = gcloud secrets versions access latest --secret="ai-customer-agent-redis_host" 2>$null
if ($redisHost) {
    Add-Content $envFile "REDIS_HOST=$redisHost"
    Write-Host "REDIS_HOST extracted" -ForegroundColor Green
}

$redisPort = gcloud secrets versions access latest --secret="ai-customer-agent-redis_port" 2>$null
if ($redisPort) {
    Add-Content $envFile "REDIS_PORT=$redisPort"
    Write-Host "REDIS_PORT extracted" -ForegroundColor Green
}

$redisDb = gcloud secrets versions access latest --secret="ai-customer-agent-redis_db" 2>$null
if ($redisDb) {
    Add-Content $envFile "REDIS_DB=$redisDb"
    Write-Host "REDIS_DB extracted" -ForegroundColor Green
}

$redisUrl = gcloud secrets versions access latest --secret="ai-customer-agent-redis_url" 2>$null
if ($redisUrl) {
    Add-Content $envFile "REDIS_URL=$redisUrl"
    Write-Host "REDIS_URL extracted" -ForegroundColor Green
}

Add-Content $envFile ""

# API Keys
Write-Host "Extracting API keys..." -ForegroundColor Green
Add-Content $envFile "# API Keys"

$openaiKey = gcloud secrets versions access latest --secret="ai-customer-agent-openai_api_key" 2>$null
if ($openaiKey) {
    Add-Content $envFile "OPENAI_API_KEY=$openaiKey"
    Write-Host "OPENAI_API_KEY extracted" -ForegroundColor Green
}

$groqKey = gcloud secrets versions access latest --secret="ai-customer-agent-groq_api_key" 2>$null
if ($groqKey) {
    Add-Content $envFile "GROQ_API_KEY=$groqKey"
    Write-Host "GROQ_API_KEY extracted" -ForegroundColor Green
}

$googleKey = gcloud secrets versions access latest --secret="ai-customer-agent-google_api_key" 2>$null
if ($googleKey) {
    Add-Content $envFile "GOOGLE_API_KEY=$googleKey"
    Write-Host "GOOGLE_API_KEY extracted" -ForegroundColor Green
}

Add-Content $envFile ""

# Qdrant Configuration
Write-Host "Extracting Qdrant secrets..." -ForegroundColor Green
Add-Content $envFile "# Qdrant Configuration"

$qdrantUrl = gcloud secrets versions access latest --secret="ai-customer-agent-qdrant_url_cloud" 2>$null
if ($qdrantUrl) {
    Add-Content $envFile "QDRANT_URL_CLOUD=$qdrantUrl"
    Write-Host "QDRANT_URL_CLOUD extracted" -ForegroundColor Green
}

$qdrantKey = gcloud secrets versions access latest --secret="ai-customer-agent-qdrant_api_key" 2>$null
if ($qdrantKey) {
    Add-Content $envFile "QDRANT_API_KEY=$qdrantKey"
    Write-Host "QDRANT_API_KEY extracted" -ForegroundColor Green
}

Add-Content $envFile ""

# WhatsApp Configuration
Write-Host "Extracting WhatsApp secrets..." -ForegroundColor Green
Add-Content $envFile "# WhatsApp Configuration"

$whatsappToken = gcloud secrets versions access latest --secret="ai-customer-agent-whatsapp_access_token" 2>$null
if ($whatsappToken) {
    Add-Content $envFile "WHATSAPP_ACCESS_TOKEN=$whatsappToken"
    Write-Host "WHATSAPP_ACCESS_TOKEN extracted" -ForegroundColor Green
}

$whatsappPhoneId = gcloud secrets versions access latest --secret="ai-customer-agent-whatsapp_phone_number_id" 2>$null
if ($whatsappPhoneId) {
    Add-Content $envFile "WHATSAPP_PHONE_NUMBER_ID=$whatsappPhoneId"
    Write-Host "WHATSAPP_PHONE_NUMBER_ID extracted" -ForegroundColor Green
}

$whatsappVerifyToken = gcloud secrets versions access latest --secret="ai-customer-agent-whatsapp_webhook_verify_token" 2>$null
if ($whatsappVerifyToken) {
    Add-Content $envFile "WHATSAPP_VERIFY_TOKEN=$whatsappVerifyToken"
    Write-Host "WHATSAPP_VERIFY_TOKEN extracted" -ForegroundColor Green
}

$whatsappBusinessId = gcloud secrets versions access latest --secret="ai-customer-agent-whatsapp_business_account_id" 2>$null
if ($whatsappBusinessId) {
    Add-Content $envFile "WHATSAPP_BUSINESS_ACCOUNT_ID=$whatsappBusinessId"
    Write-Host "WHATSAPP_BUSINESS_ACCOUNT_ID extracted" -ForegroundColor Green
}

$whatsappApiUrl = gcloud secrets versions access latest --secret="ai-customer-agent-whatsapp_api_base_url" 2>$null
if ($whatsappApiUrl) {
    Add-Content $envFile "WHATSAPP_API_BASE_URL=$whatsappApiUrl"
    Write-Host "WHATSAPP_API_BASE_URL extracted" -ForegroundColor Green
}

$developerWhatsapp = gcloud secrets versions access latest --secret="ai-customer-agent-developer_whatsapp_number" 2>$null
if ($developerWhatsapp) {
    Add-Content $envFile "DEVELOPER_WHATSAPP_NUMBER=$developerWhatsapp"
    Write-Host "DEVELOPER_WHATSAPP_NUMBER extracted" -ForegroundColor Green
}

Add-Content $envFile ""

# Email Configuration
Write-Host "Extracting email secrets..." -ForegroundColor Green
Add-Content $envFile "# Email Configuration"

$smtpServer = gcloud secrets versions access latest --secret="ai-customer-agent-smtp_server" 2>$null
if ($smtpServer) {
    Add-Content $envFile "SMTP_SERVER=$smtpServer"
    Write-Host "SMTP_SERVER extracted" -ForegroundColor Green
}

$smtpPort = gcloud secrets versions access latest --secret="ai-customer-agent-smtp_port" 2>$null
if ($smtpPort) {
    Add-Content $envFile "SMTP_PORT=$smtpPort"
    Write-Host "SMTP_PORT extracted" -ForegroundColor Green
}

$smtpUsername = gcloud secrets versions access latest --secret="ai-customer-agent-smtp_username" 2>$null
if ($smtpUsername) {
    Add-Content $envFile "SMTP_USERNAME=$smtpUsername"
    Write-Host "SMTP_USERNAME extracted" -ForegroundColor Green
}

$smtpPassword = gcloud secrets versions access latest --secret="ai-customer-agent-smtp_password" 2>$null
if ($smtpPassword) {
    Add-Content $envFile "SMTP_PASSWORD=$smtpPassword"
    Write-Host "SMTP_PASSWORD extracted" -ForegroundColor Green
}

$fromEmail = gcloud secrets versions access latest --secret="ai-customer-agent-from_email" 2>$null
if ($fromEmail) {
    Add-Content $envFile "FROM_EMAIL=$fromEmail"
    Write-Host "FROM_EMAIL extracted" -ForegroundColor Green
}

$fromName = gcloud secrets versions access latest --secret="ai-customer-agent-from_name" 2>$null
if ($fromName) {
    Add-Content $envFile "FROM_NAME=$fromName"
    Write-Host "FROM_NAME extracted" -ForegroundColor Green
}

Add-Content $envFile ""

# Flask Configuration
Write-Host "Extracting Flask secrets..." -ForegroundColor Green
Add-Content $envFile "# Flask Configuration"

$flaskEnv = gcloud secrets versions access latest --secret="ai-customer-agent-flask_env" 2>$null
if ($flaskEnv) {
    Add-Content $envFile "FLASK_ENV=$flaskEnv"
    Write-Host "FLASK_ENV extracted" -ForegroundColor Green
}

$flaskSecretKey = gcloud secrets versions access latest --secret="ai-customer-agent-flask_secret_key" 2>$null
if ($flaskSecretKey) {
    Add-Content $envFile "FLASK_SECRET_KEY=$flaskSecretKey"
    Write-Host "FLASK_SECRET_KEY extracted" -ForegroundColor Green
}

Add-Content $envFile ""
Add-Content $envFile "# ====================================================================="
Add-Content $envFile "# END OF GOOGLE CLOUD SECRETS"
Add-Content $envFile "# ====================================================================="

Write-Host ""
Write-Host "Successfully created .env_cloud file!" -ForegroundColor Green
Write-Host "File location: $envFile" -ForegroundColor Cyan

# Show file contents (with sensitive data masked)
Write-Host ""
Write-Host "Summary of extracted secrets:" -ForegroundColor Yellow
Get-Content $envFile | ForEach-Object {
    if ($_ -match "^([^#][^=]+)=(.*)$") {
        $varName = $matches[1]
        $varValue = $matches[2]

        # Mask sensitive values
        if ($varName -match "(PASSWORD|KEY|TOKEN)") {
            $maskedValue = if ($varValue.Length -gt 8) { $varValue.Substring(0, 8) + "..." } else { "***" }
        }
        else {
            $maskedValue = $varValue
        }

        Write-Host "   $varName=$maskedValue" -ForegroundColor Gray
    }
    else {
        Write-Host "   $_" -ForegroundColor DarkGray
    }
}
