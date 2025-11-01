# Microsoft Teams Webhook Setup Guide

This guide explains how to configure Microsoft Teams webhooks for the TradingView Webhook Bot.

## Setting up Teams Incoming Webhook

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

## Security Notes

- Keep your webhook URLs secret - anyone with the URL can post to your Teams channel
- Use different webhook URLs for different channels/purposes
- Regenerate webhook URLs if they become compromised

## Additional Resources

- [Microsoft Teams Incoming Webhooks Documentation](https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook)
- [MessageCard Format Reference](https://docs.microsoft.com/en-us/outlook/actionable-messages/message-card-reference)
