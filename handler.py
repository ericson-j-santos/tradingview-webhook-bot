# ----------------------------------------------- #
# Plugin Name           : TradingView-Webhook-Bot #
# Author Name           : fabston                 #
# File Name             : handler.py              #
# ----------------------------------------------- #

import smtplib
import ssl
from email.mime.text import MIMEText

import requests
import tweepy
from discord_webhook import DiscordEmbed, DiscordWebhook
from slack_webhook import Slack
from telegram import Bot

import config


def send_alert(data):
    msg = data["msg"].encode("latin-1", "backslashreplace").decode("unicode_escape")
    if config.send_telegram_alerts:
        tg_bot = Bot(token=config.tg_token)
        try:
            tg_bot.sendMessage(
                data["telegram"],
                msg,
                parse_mode="MARKDOWN",
            )
        except KeyError:
            tg_bot.sendMessage(
                config.channel,
                msg,
                parse_mode="MARKDOWN",
            )
        except Exception as e:
            print("[X] Telegram Error:\n>", e)

    if config.send_discord_alerts:
        try:
            webhook = DiscordWebhook(
                url="https://discord.com/api/webhooks/" + data["discord"]
            )
            embed = DiscordEmbed(title=msg)
            webhook.add_embed(embed)
            webhook.execute()
        except KeyError:
            webhook = DiscordWebhook(
                url="https://discord.com/api/webhooks/" + config.discord_webhook
            )
            embed = DiscordEmbed(title=msg)
            webhook.add_embed(embed)
            webhook.execute()
        except Exception as e:
            print("[X] Discord Error:\n>", e)

    if config.send_slack_alerts:
        try:
            slack = Slack(url="https://hooks.slack.com/services/" + data["slack"])
            slack.post(text=msg)
        except KeyError:
            slack = Slack(
                url="https://hooks.slack.com/services/" + config.slack_webhook
            )
            slack.post(text=msg)
        except Exception as e:
            print("[X] Slack Error:\n>", e)

    if config.send_teams_alerts:
        try:
            # Try to get Teams webhook URL from the alert data
            teams_url = data.get("teams", config.teams_webhook)
            if teams_url:
                # Microsoft Teams expects a JSON payload with a text or card
                # Using MessageCard format for better formatting
                teams_payload = {
                    "@type": "MessageCard",
                    "@context": "https://schema.org/extensions",
                    "summary": "Trading Alert",
                    "themeColor": "0078D7",
                    "title": "TradingView Alert",
                    "text": msg.replace("*", "**").replace("`", "")
                }
                response = requests.post(teams_url, json=teams_payload)
                response.raise_for_status()
        except Exception as e:
            print("[X] Teams Error:\n>", e)

    # Microsoft Teams API - Send individual chat with Adaptive Card
    if config.send_teams_api_alerts:
        try:
            # Get recipient from alert data or use a default
            teams_to = data.get("teams_to")
            correlation_id = data.get("correlation_id", "")
            
            if teams_to and config.teams_access_token:
                # Validate that the configured endpoint is a Microsoft Graph API endpoint
                # to prevent SSRF attacks
                if not config.teams_api_endpoint.startswith("https://graph.microsoft.com/"):
                    print("[X] Teams API Error: Invalid endpoint. Must be a Microsoft Graph API URL.")
                    return
                
                # Sanitize the teams_to value to prevent URL manipulation
                # Only allow alphanumeric, @, ., -, and _ characters
                import re
                if not re.match(r'^[a-zA-Z0-9@.\-_]+$', teams_to):
                    print(f"[X] Teams API Error: Invalid teams_to format: {teams_to}")
                    return
                
                # Create Adaptive Card payload
                adaptive_card = {
                    "type": "AdaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "size": "Medium",
                            "weight": "Bolder",
                            "text": "TradingView Alert"
                        },
                        {
                            "type": "TextBlock",
                            "text": msg,
                            "wrap": True
                        }
                    ],
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "version": "1.4"
                }
                
                # Add correlation_id to card if provided
                if correlation_id:
                    adaptive_card["body"].append({
                        "type": "TextBlock",
                        "text": f"Correlation ID: {correlation_id}",
                        "size": "Small",
                        "isSubtle": True,
                        "wrap": True
                    })
                
                # Prepare the message payload
                message_payload = {
                    "body": {
                        "contentType": "html",
                        "content": f"<attachment id=\"{correlation_id}\"></attachment>"
                    },
                    "attachments": [
                        {
                            "id": correlation_id,
                            "contentType": "application/vnd.microsoft.card.adaptive",
                            "content": adaptive_card
                        }
                    ]
                }
                
                # Headers for Graph API
                headers = {
                    "Authorization": f"Bearer {config.teams_access_token}",
                    "Content-Type": "application/json"
                }
                
                # Send to individual chat via Graph API
                # Note: The endpoint needs to be constructed with the actual chat ID
                # For sending to a user, we would typically need to create or find a chat first
                # This is a simplified version - in production, you'd need proper chat resolution
                api_endpoint = config.teams_api_endpoint.replace("{to}", teams_to)
                
                response = requests.post(api_endpoint, json=message_payload, headers=headers)
                response.raise_for_status()
                
                if correlation_id:
                    print(f"[✓] Teams API message sent successfully. Correlation ID: {correlation_id}")
                else:
                    print("[✓] Teams API message sent successfully.")
                    
        except Exception as e:
            print("[X] Teams API Error:\n>", e)

    if config.send_twitter_alerts:
        tw_auth = tweepy.OAuthHandler(config.tw_ckey, config.tw_csecret)
        tw_auth.set_access_token(config.tw_atoken, config.tw_asecret)
        tw_api = tweepy.API(tw_auth)
        try:
            tw_api.update_status(
                status=msg.replace("*", "").replace("_", "").replace("`", "")
            )
        except Exception as e:
            print("[X] Twitter Error:\n>", e)

    if config.send_email_alerts:
        try:
            email_msg = MIMEText(
                msg.replace("*", "").replace("_", "").replace("`", "")
            )
            email_msg["Subject"] = config.email_subject
            email_msg["From"] = config.email_sender
            email_msg["To"] = config.email_sender
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                config.email_host, config.email_port, context=context
            ) as server:
                server.login(config.email_user, config.email_password)
                server.sendmail(
                    config.email_sender, config.email_receivers, email_msg.as_string()
                )
                server.quit()
        except Exception as e:
            print("[X] Email Error:\n>", e)
