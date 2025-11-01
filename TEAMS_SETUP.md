# Microsoft Teams Webhook Setup Guide

This guide explains how to configure Microsoft Teams webhooks for the TradingView Webhook Bot.

## Option 1: Channel Webhooks (MessageCard format)

This option sends messages to Teams channels using Incoming Webhooks.

### Setting up Teams Incoming Webhook

1. **Navigate to your Teams channel**
   - Open Microsoft Teams
   - Select the channel where you want to receive alerts

2. **Create an Incoming Webhook**
   - Click on the three dots (**...**) next to the channel name
   - Select **Connectors** or **Workflows** (depending on your Teams version)
   - Search for "Incoming Webhook"
   - Click **Add** or **Configure**

3. **Configure the Webhook**
   - Provide a name (e.g., "TradingView Alerts")
   - Optionally upload an image/icon
   - Click **Create**

4. **Copy the Webhook URL**
   - Copy the generated webhook URL
   - It should look like: `https://outlook.office.com/webhook/...`

5. **Add to config.py**
   - Open `config.py` in your bot directory
   - Set `send_teams_alerts = True`
   - Paste your webhook URL in `teams_webhook = "YOUR_WEBHOOK_URL"`

## Example Configuration

```python
# Microsoft Teams Settings
send_teams_alerts = True
teams_webhook = "https://outlook.office.com/webhook/YOUR-WEBHOOK-ID/IncomingWebhook/YOUR-CHANNEL-ID/YOUR-CONNECTOR-ID"
```

## TradingView Alert Example

You can send alerts to different Teams channels by specifying the webhook URL in your TradingView alert:

```json
{
 "key": "YOUR_SECRET_KEY",
 "teams": "https://outlook.office.com/webhook/YOUR-CUSTOM-WEBHOOK-URL",
 "msg": "Long *BTC/USDT* at `50000`"
}
```

If you don't specify a `teams` field in your alert, it will use the default webhook URL from `config.py`.

## Message Formatting

The bot converts TradingView alert messages to Microsoft Teams MessageCard format:

- Single asterisks `*text*` become bold `**text**` in Teams
- Backticks `` `text` `` are removed (code formatting not supported in MessageCard)
- TradingView variables like `{{close}}`, `{{ticker}}` are preserved

## Troubleshooting

### Webhook not receiving messages
- Verify the webhook URL is correct
- Check that `send_teams_alerts = True` in `config.py`
- Ensure your TradingView alert includes the correct `key` matching `sec_key` in `config.py`

### Error messages in console
- Check the console output for `[X] Teams Error:` messages
- Verify the webhook URL hasn't expired (Teams webhooks can be regenerated)
- Ensure your server has internet connectivity to reach `outlook.office.com`

## Option 2: Individual Chat with Adaptive Cards (Graph API)

This option sends messages to individual users via Teams chat using Microsoft Graph API with Adaptive Cards support. This provides better observability with correlation IDs.

### Prerequisites

1. **Register an Azure AD Application**
   - Go to [Azure Portal](https://portal.azure.com)
   - Navigate to "Azure Active Directory" > "App registrations" > "New registration"
   - Name your app (e.g., "TradingView Webhook Bot")
   - Set supported account types based on your needs
   - Click "Register"

2. **Configure API Permissions**
   - In your app registration, go to "API permissions"
   - Click "Add a permission" > "Microsoft Graph" > "Application permissions"
   - Add the following permissions:
     - `Chat.ReadWrite.All` - Send messages to chats
     - `ChatMessage.Send` - Send chat messages
   - Click "Grant admin consent" for your organization

3. **Create a Client Secret**
   - Go to "Certificates & secrets" > "New client secret"
   - Add a description and expiration period
   - Copy the secret value (you won't be able to see it again!)

4. **Get an Access Token**
   You'll need to obtain an access token using your client credentials. You can use the following endpoint:
   ```
   POST https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token
   Content-Type: application/x-www-form-urlencoded

   client_id={your-client-id}
   &client_secret={your-client-secret}
   &scope=https://graph.microsoft.com/.default
   &grant_type=client_credentials
   ```

### Configuration

1. **Update config.py**
   ```python
   # Microsoft Teams API Settings (for individual chat with Adaptive Cards)
   send_teams_api_alerts = True
   teams_api_endpoint = "https://graph.microsoft.com/v1.0/chats/{chat-id}/messages"
   teams_access_token = "YOUR_ACCESS_TOKEN_HERE"
   ```

2. **Find Chat ID**
   To send messages to a specific chat, you need the chat ID. You can:
   - Use Graph API Explorer to list chats
   - Or use the endpoint: `GET https://graph.microsoft.com/v1.0/me/chats`

### TradingView Alert Example

Send alerts to individual users with correlation ID for observability:

```json
{
 "key": "YOUR_SECRET_KEY",
 "teams_to": "user@example.com",
 "correlation_id": "trade-20231101-001",
 "msg": "Long *BTC/USDT* at `50000`"
}
```

**Fields:**
- `key`: Your security key (must match `sec_key` in config.py)
- `teams_to`: The recipient's email or user ID
- `correlation_id`: Optional correlation ID for observability and tracking
- `msg`: The alert message (supports markdown formatting)

### Adaptive Card Features

The implementation automatically creates an Adaptive Card with:
- Title: "TradingView Alert"
- Message body with your alert text
- Correlation ID footer (if provided) for easy tracking and observability

### Observability

The `correlation_id` field enables:
- **Tracking**: Each alert can be uniquely identified
- **Logging**: The correlation ID is logged in console output
- **Debugging**: Easier troubleshooting of message delivery
- **Auditing**: Track which alerts were sent and when

Example console output:
```
[✓] Teams API message sent successfully. Correlation ID: trade-20231101-001
```

## Security Notes

- **Webhook URLs**: Keep your webhook URLs secret - anyone with the URL can post to your Teams channel
- **Access Tokens**: Keep your Graph API access tokens secure - store them as environment variables in production
- **Token Rotation**: Access tokens expire - implement token refresh logic for production use
- Use different webhook URLs for different channels/purposes
- Regenerate webhook URLs if they become compromised
- Use Azure Key Vault or similar services to store sensitive credentials in production

## Additional Resources

- [Microsoft Teams Incoming Webhooks Documentation](https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook)
- [MessageCard Format Reference](https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference)
