# Nanobot Home Assistant Integration

A custom component that integrates [nanobot](https://github.com/licheng5625/nanobot) as a conversation agent for Home Assistant.

## Overview

This integration allows nanobot to act as your Home Assistant's conversation agent. Nanobot connects to HA via WebSocket and handles all conversation requests through its LLM-powered agent.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Home Assistant                           │
│  ┌─────────────────┐     ┌──────────────────────────────┐  │
│  │   Assist UI     │────▶│  custom_components/nanobot   │  │
│  │   (user speaks) │     │  ConversationEntity          │  │
│  └─────────────────┘     └──────────────────────────────┘  │
│                                     │                       │
│                          WebSocket API (:8123)              │
│                     ws://ha:8123/api/websocket              │
└─────────────────────────────────│───────────────────────────┘
                                  │
                    ┌─────────────▼───────────────────┐
                    │            nanobot              │
                    │  - Connects to HA WebSocket     │
                    │  - Subscribes to request events │
                    │  - Processes with LLM           │
                    │  - Fires response events        │
                    │  - Can control HA via REST API  │
                    └─────────────────────────────────┘
```

## Installation

### Manual Installation

1. Copy the `nanobot` folder to your Home Assistant's `custom_components` directory:
   ```
   custom_components/
   └── nanobot/
       ├── __init__.py
       ├── config_flow.py
       ├── const.py
       ├── conversation.py
       ├── manifest.json
       └── strings.json
   ```

2. Restart Home Assistant

3. Go to **Settings** → **Devices & Services** → **Add Integration** → Search for **Nanobot**

### HACS Installation (Coming Soon)

This integration will be available through HACS in the future.

## Configuration

### Home Assistant Side

After adding the integration, no additional configuration is needed on the HA side. The integration will:
- Create a conversation entity (`conversation.nanobot`)
- Listen for response events from nanobot
- Fire request events when users speak to Assist

### Nanobot Side

Configure nanobot to connect to your Home Assistant instance:

```yaml
# ~/.nanobot/config.yaml or config.json
channels:
  homeassistant:
    enabled: true
    url: "ws://your-ha-ip:8123/api/websocket"
    accessToken: "your-long-lived-access-token"
```

#### Getting a Long-Lived Access Token

1. Log in to Home Assistant Web UI
2. Click your user profile (bottom left)
3. Scroll to **Long-Lived Access Tokens**
4. Click **Create Token**
5. Copy the token to your nanobot config

## Usage

1. Start nanobot with the homeassistant channel enabled
2. In Home Assistant, go to **Settings** → **Voice Assistants**
3. Create or edit an assistant and select **Nanobot** as the conversation agent
4. Use the Assist feature to talk to nanobot

## Events

The integration uses Home Assistant events for communication:

| Event | Direction | Description |
|-------|-----------|-------------|
| `nanobot_conversation_request` | HA → Nanobot | User input from Assist |
| `nanobot_conversation_response` | Nanobot → HA | AI response |
| `nanobot_notification` | Nanobot → HA | Async notification (optional) |

### Request Format
```json
{
  "request_id": "uuid-string",
  "message": "user's message",
  "conversation_id": "optional-session-id",
  "language": "en"
}
```

### Response Format
```json
{
  "request_id": "uuid-string",
  "response": "AI response text",
  "conversation_id": "session-id"
}
```

> **Note**: The same `request_id` can receive multiple responses. The first response is returned to the conversation UI; subsequent responses are automatically converted to persistent notifications.

### Notification Format (Optional)
```json
{
  "title": "Notification Title",
  "message": "Notification body",
  "notification_id": "optional-unique-id"
}
```

## Async Notifications

When nanobot runs background tasks (e.g., subagent spawn), follow-up responses are automatically converted to Home Assistant persistent notifications. This works because:

1. **First response**: Returned to the conversation UI as normal
2. **Subsequent responses** (same `request_id`): Converted to persistent notifications

This enables nanobot to report back after long-running tasks without blocking the conversation.

## Device Control

Nanobot can control Home Assistant devices through the REST API. When configured with a valid access token, nanobot can:
- Query device states
- Turn devices on/off
- Adjust settings (brightness, temperature, etc.)
- Run automations and scripts

## Requirements

- Home Assistant 2024.1.0 or newer
- Nanobot with homeassistant channel enabled

## Troubleshooting

### Nanobot not responding

1. Check nanobot logs for connection status
2. Verify the access token is valid
3. Ensure nanobot can reach Home Assistant's WebSocket endpoint

### Connection refused

1. Check if Home Assistant is running
2. Verify the URL in nanobot config (use `host.docker.internal` if running in Docker)
3. Check firewall settings

## License

MIT License - See [LICENSE](LICENSE) for details.

## Related Projects

- [nanobot](https://github.com/licheng5625/nanobot) - The AI agent that powers this integration
