# Extract secrets from Google Secret Manager and create .env file for local development
# This script helps with local development by creating a .env file with the same values as production

Write-Host "Extracting secrets from Google Secret Manager..." -ForegroundColor Green

# Create .env file
$envFile = ".env_cloud"
if (Test-Path $envFile) {
    Remove-Item $envFile
}

# Database Configuration
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

# Redis Configuration
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

# API Keys
$openaiApiKey = gcloud secrets versions access latest --secret="ai-customer-agent-openai_api_key" 2>$null
if ($openaiApiKey) {
    Add-Content $envFile "OPENAI_API_KEY=$openaiApiKey"
    Write-Host "OPENAI_API_KEY extracted" -ForegroundColor Green
}

$groqApiKey = gcloud secrets versions access latest --secret="ai-customer-agent-groq_api_key" 2>$null
if ($groqApiKey) {
    Add-Content $envFile "GROQ_API_KEY=$groqApiKey"
    Write-Host "GROQ_API_KEY extracted" -ForegroundColor Green
}

$googleApiKey = gcloud secrets versions access latest --secret="ai-customer-agent-google_api_key" 2>$null
if ($googleApiKey) {
    Add-Content $envFile "GOOGLE_API_KEY=$googleApiKey"
    Write-Host "GOOGLE_API_KEY extracted" -ForegroundColor Green
}

# Qdrant Configuration
$qdrantUrlCloud = gcloud secrets versions access latest --secret="ai-customer-agent-qdrant_url_cloud" 2>$null
if ($qdrantUrlCloud) {
    Add-Content $envFile "QDRANT_URL_CLOUD=$qdrantUrlCloud"
    Write-Host "QDRANT_URL_CLOUD extracted" -ForegroundColor Green
}

# For local development, QDRANT_URL_LOCAL should be localhost
Add-Content $envFile "QDRANT_URL_LOCAL=http://localhost:6333"
Write-Host "QDRANT_URL_LOCAL set to localhost for local development" -ForegroundColor Green

$qdrantApiKey = gcloud secrets versions access latest --secret="ai-customer-agent-qdrant_api_key" 2>$null
if ($qdrantApiKey) {
    Add-Content $envFile "QDRANT_API_KEY=$qdrantApiKey"
    Write-Host "QDRANT_API_KEY extracted" -ForegroundColor Green
}

# WhatsApp Configuration
$whatsappAccessToken = gcloud secrets versions access latest --secret="ai-customer-agent-whatsapp_access_token" 2>$null
if ($whatsappAccessToken) {
    Add-Content $envFile "WHATSAPP_ACCESS_TOKEN=$whatsappAccessToken"
    Write-Host "WHATSAPP_ACCESS_TOKEN extracted" -ForegroundColor Green
}

$whatsappPhoneNumberId = gcloud secrets versions access latest --secret="ai-customer-agent-whatsapp_phone_number_id" 2>$null
if ($whatsappPhoneNumberId) {
    Add-Content $envFile "WHATSAPP_PHONE_NUMBER_ID=$whatsappPhoneNumberId"
    Write-Host "WHATSAPP_PHONE_NUMBER_ID extracted" -ForegroundColor Green
}

$whatsappWebhookVerifyToken = gcloud secrets versions access latest --secret="ai-customer-agent-whatsapp_webhook_verify_token" 2>$null
if ($whatsappWebhookVerifyToken) {
    Add-Content $envFile "WHATSAPP_WEBHOOK_VERIFY_TOKEN=$whatsappWebhookVerifyToken"
    Write-Host "WHATSAPP_WEBHOOK_VERIFY_TOKEN extracted" -ForegroundColor Green
}

# Email Configuration
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

# Flask Configuration
Add-Content $envFile "FLASK_ENV=local"
Add-Content $envFile "FLASK_SECRET_KEY=nigerian-ecommerce-support-2025"

# Additional WhatsApp Configuration
Add-Content $envFile "WHATSAPP_API_BASE_URL=https://graph.facebook.com/v23.0"
Add-Content $envFile "TEST_PHONE_NUMBER=+15556657520"
Add-Content $envFile "DEVELOPER_WHATSAPP_NUMBER=+2347025965922"

Write-Host "`nSecrets extraction completed! File created: $envFile" -ForegroundColor Green
Write-Host "You can now copy this to .env for local development:" -ForegroundColor Yellow
Write-Host "Copy-Item $envFile .env" -ForegroundColor Cyan
