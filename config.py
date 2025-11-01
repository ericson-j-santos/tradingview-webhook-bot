# ----------------------------------------------- #
# Plugin Name           : TradingView-Webhook-Bot #
# Author Name           : fabston                 #
# File Name             : config.py               #
# ----------------------------------------------- #

# TradingView Example Alert Message:
# {
# "key":"9T2q394M92", "telegram":"-1001298977502", "discord":"789842349670960670/BFeBBrCt-w2Z9RJ2wlH6TWUjM5bJuC29aJaJ5OQv9sE6zCKY_AlOxxFwRURkgEl852s3", "slack":"T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX", "teams":"https://outlook.office.com/webhook/...", "teams_to":"user@example.com", "correlation_id":"trade-123", "msg":"Long #{{ticker}} at `{{close}}`"
# }

sec_key = (
    ""  # Can be anything. Has to match with "key" in your TradingView alert message
)

# Telegram Settings
send_telegram_alerts = False
tg_token = ""  # Bot token. Get it from @Botfather
channel = 0  # Channel ID (ex. -1001487568087)

# Discord Settings
send_discord_alerts = False
discord_webhook = ""  # Discord Webhook URL (https://support.discordapp.com/hc/de/articles/228383668-Webhooks-verwenden)

# Slack Settings
send_slack_alerts = False
slack_webhook = ""  # Slack Webhook URL (https://api.slack.com/messaging/webhooks)

# Microsoft Teams Settings
send_teams_alerts = False
teams_webhook = ""  # Microsoft Teams Webhook URL (https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook)

# Microsoft Teams API Settings (for individual chat with Adaptive Cards)
send_teams_api_alerts = False
teams_api_endpoint = "https://graph.microsoft.com/v1.0/chats/{chat-id}/messages"  # Teams Graph API endpoint
teams_access_token = ""  # Microsoft Teams access token for Graph API

# Twitter Settings
send_twitter_alerts = False
tw_ckey = ""
tw_csecret = ""
tw_atoken = ""
tw_asecret = ""

# Email Settings
send_email_alerts = False
email_sender = ""  # Your email address
email_receivers = ["", ""]  # Receivers, can be multiple
email_subject = "Trade Alert!"

email_port = 465  # SMTP SSL Port (ex. 465)
email_host = ""  # SMTP host (ex. smtp.gmail.com)
email_user = ""  # SMTP Login credentials
email_password = ""  # SMTP Login credentials
