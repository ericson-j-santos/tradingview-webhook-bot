# ----------------------------------------------- #
# Plugin Name           : TradingView-Webhook-Bot #
# Author Name           : fabston                 #
# File Name             : handler.py              #
# ----------------------------------------------- #

import re
import smtplib
import ssl
import uuid
from email.mime.text import MIMEText

import requests
import tweepy
from discord_webhook import DiscordEmbed, DiscordWebhook
from slack_webhook import Slack
from telegram import Bot

import config

# OpenTelemetry imports
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


def send_alert(data):
    msg = data["msg"].encode("latin-1", "backslashreplace").decode("unicode_escape")
    
    with tracer.start_as_current_span("send_alert") as span:
        span.set_attribute("alert.message_length", len(msg))
        
        if config.send_telegram_alerts:
            with tracer.start_as_current_span("send_telegram") as tg_span:
                tg_bot = Bot(token=config.tg_token)
                try:
                    channel = data.get("telegram", config.channel)
                    tg_span.set_attribute("telegram.channel", str(channel))
                    tg_bot.sendMessage(
                        channel,
                        msg,
                        parse_mode="MARKDOWN",
                    )
                    tg_span.set_attribute("telegram.success", True)
                except Exception as e:
                    tg_span.set_attribute("telegram.success", False)
                    tg_span.set_attribute("error.message", str(e))
                    tg_span.record_exception(e)
                    print("[X] Telegram Error:\n>", e)

    if config.send_discord_alerts:
        with tracer.start_as_current_span("send_discord") as discord_span:
            try:
                webhook_url = data.get("discord", config.discord_webhook)
                discord_span.set_attribute("discord.webhook_set", bool(webhook_url))
                
                webhook = DiscordWebhook(
                    url="https://discord.com/api/webhooks/" + webhook_url
                )
                embed = DiscordEmbed(title=msg)
                webhook.add_embed(embed)
                webhook.execute()
                discord_span.set_attribute("discord.success", True)
            except Exception as e:
                discord_span.set_attribute("discord.success", False)
                discord_span.set_attribute("error.message", str(e))
                discord_span.record_exception(e)
                print("[X] Discord Error:\n>", e)

    if config.send_slack_alerts:
        with tracer.start_as_current_span("send_slack") as slack_span:
            try:
                webhook_url = data.get("slack", config.slack_webhook)
                slack_span.set_attribute("slack.webhook_set", bool(webhook_url))
                
                slack = Slack(url="https://hooks.slack.com/services/" + webhook_url)
                slack.post(text=msg)
                slack_span.set_attribute("slack.success", True)
            except Exception as e:
                slack_span.set_attribute("slack.success", False)
                slack_span.set_attribute("error.message", str(e))
                slack_span.record_exception(e)
                print("[X] Slack Error:\n>", e)

    if config.send_teams_alerts:
        with tracer.start_as_current_span("send_teams") as teams_span:
            try:
                # Try to get Teams webhook URL from the alert data
                teams_url = data.get("teams", config.teams_webhook)
                teams_span.set_attribute("teams.webhook_set", bool(teams_url))
                
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
                    teams_span.set_attribute("teams.success", True)
                    teams_span.set_attribute("teams.status_code", response.status_code)
            except Exception as e:
                teams_span.set_attribute("teams.success", False)
                teams_span.set_attribute("error.message", str(e))
                teams_span.record_exception(e)
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
                    raise ValueError("Invalid endpoint. Must be a Microsoft Graph API URL.")
                
                # Sanitize the teams_to value to prevent URL manipulation
                # Only allow alphanumeric, @, ., -, and _ characters (email addresses and IDs)
                if not re.match(r'^[a-zA-Z0-9@.\-_]+$', teams_to):
                    raise ValueError(f"Invalid teams_to format: {teams_to}")
                
                # Generate a unique attachment ID (use correlation_id if provided, otherwise generate UUID)
                attachment_id = correlation_id if correlation_id else str(uuid.uuid4())
                
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
                        "content": f"<attachment id=\"{attachment_id}\"></attachment>"
                    },
                    "attachments": [
                        {
                            "id": attachment_id,
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
                
                # Construct the API endpoint by replacing placeholders
                # Support both {chat-id} and {user-id} placeholders for flexibility
                # Only one should exist in the configured endpoint
                api_endpoint = config.teams_api_endpoint.replace("{chat-id}", teams_to).replace("{user-id}", teams_to)
                
                response = requests.post(api_endpoint, json=message_payload, headers=headers)
                response.raise_for_status()
                
                if correlation_id:
                    print(f"[✓] Teams API message sent successfully. Correlation ID: {correlation_id}")
                else:
                    print("[✓] Teams API message sent successfully.")
                    
        except Exception as e:
            print("[X] Teams API Error:\n>", e)

    if config.send_twitter_alerts:
        with tracer.start_as_current_span("send_twitter") as twitter_span:
            tw_auth = tweepy.OAuthHandler(config.tw_ckey, config.tw_csecret)
            tw_auth.set_access_token(config.tw_atoken, config.tw_asecret)
            tw_api = tweepy.API(tw_auth)
            try:
                tw_api.update_status(
                    status=msg.replace("*", "").replace("_", "").replace("`", "")
                )
                twitter_span.set_attribute("twitter.success", True)
            except Exception as e:
                twitter_span.set_attribute("twitter.success", False)
                twitter_span.set_attribute("error.message", str(e))
                twitter_span.record_exception(e)
                print("[X] Twitter Error:\n>", e)

    if config.send_email_alerts:
        with tracer.start_as_current_span("send_email") as email_span:
            try:
                email_msg = MIMEText(
                    msg.replace("*", "").replace("_", "").replace("`", "")
                )
                email_msg["Subject"] = config.email_subject
                email_msg["From"] = config.email_sender
                email_msg["To"] = config.email_sender
                context = ssl.create_default_context()
                
                email_span.set_attribute("email.recipients_count", len(config.email_receivers))
                
                with smtplib.SMTP_SSL(
                    config.email_host, config.email_port, context=context
                ) as server:
                    server.login(config.email_user, config.email_password)
                    server.sendmail(
                        config.email_sender, config.email_receivers, email_msg.as_string()
                    )
                    server.quit()
                email_span.set_attribute("email.success", True)
            except Exception as e:
                email_span.set_attribute("email.success", False)
                email_span.set_attribute("error.message", str(e))
                email_span.record_exception(e)
                print("[X] Email Error:\n>", e)
