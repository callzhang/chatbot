# Stardust.ai Chatbot API Documentation

## Overview

The Stardust.ai Chatbot provides a comprehensive API for AI-powered conversations, document processing, and analytics. This documentation covers all available endpoints, parameters, and response formats.

## Base URL

```
https://your-domain.com/api/v1
```

## Authentication

All API requests require authentication using an API key:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     https://your-domain.com/api/v1/chat
```

## Endpoints

### 1. Chat API

#### POST /chat

Send a message to the chatbot and receive a response.

**Request Body:**
```json
{
  "message": "Hello, how are you?",
  "model": "gpt-3.5-turbo",
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false,
  "context": {
    "session_id": "user_session_123",
    "user_id": "user_456"
  }
}
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking. How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 12,
    "total_tokens": 21
  }
}
```

#### POST /chat/stream

Stream chat responses in real-time.

**Request Body:**
```json
{
  "message": "Tell me a story",
  "model": "gpt-4",
  "stream": true
}
```

**Response (Server-Sent Events):**
```
data: {"id": "chatcmpl-123", "object": "chat.completion.chunk", "created": 1677652288, "model": "gpt-4", "choices": [{"index": 0, "delta": {"content": "Once"}, "finish_reason": null}]}

data: {"id": "chatcmpl-123", "object": "chat.completion.chunk", "created": 1677652288, "model": "gpt-4", "choices": [{"index": 0, "delta": {"content": " upon"}, "finish_reason": null}]}

data: [DONE]
```

### 2. Document Processing API

#### POST /documents/upload

Upload and process documents for RAG (Retrieval Augmented Generation).

**Request (multipart/form-data):**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@document.pdf" \
  -F "metadata={\"title\": \"My Document\", \"category\": \"research\"}" \
  https://your-domain.com/api/v1/documents/upload
```

**Response:**
```json
{
  "document_id": "doc_123",
  "filename": "document.pdf",
  "status": "processed",
  "chunks_count": 15,
  "file_size": 1024000,
  "upload_date": "2024-01-15T10:30:00Z"
}
```

#### GET /documents

List all uploaded documents.

**Response:**
```json
{
  "documents": [
    {
      "id": "doc_123",
      "filename": "document.pdf",
      "file_type": "pdf",
      "file_size": 1024000,
      "upload_date": "2024-01-15T10:30:00Z",
      "processed": true,
      "chunks_count": 15
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

#### DELETE /documents/{document_id}

Delete a document and all its chunks.

**Response:**
```json
{
  "message": "Document deleted successfully",
  "document_id": "doc_123"
}
```

### 3. RAG Query API

#### POST /rag/query

Query documents using RAG (Retrieval Augmented Generation).

**Request Body:**
```json
{
  "query": "What is machine learning?",
  "document_ids": ["doc_123", "doc_456"],
  "max_chunks": 5,
  "similarity_threshold": 0.7,
  "include_metadata": true
}
```

**Response:**
```json
{
  "query": "What is machine learning?",
  "relevant_chunks": [
    {
      "text": "Machine learning is a subset of artificial intelligence...",
      "score": 0.95,
      "document_id": "doc_123",
      "chunk_index": 5,
      "metadata": {
        "page": 3,
        "section": "Introduction"
      }
    }
  ],
  "context": "Machine learning is a subset of artificial intelligence...",
  "total_chunks_found": 1
}
```

### 4. Analytics API

#### GET /analytics/usage

Get usage analytics and statistics.

**Query Parameters:**
- `start_date`: Start date (ISO 8601 format)
- `end_date`: End date (ISO 8601 format)
- `granularity`: `day`, `week`, `month`

**Response:**
```json
{
  "period": {
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "granularity": "day"
  },
  "metrics": {
    "total_sessions": 1250,
    "unique_users": 450,
    "total_messages": 5670,
    "avg_session_duration": 8.5,
    "popular_models": {
      "gpt-3.5-turbo": 0.6,
      "gpt-4": 0.3,
      "gpt-4-vision": 0.1
    }
  },
  "daily_data": [
    {
      "date": "2024-01-01",
      "sessions": 45,
      "users": 32,
      "messages": 180
    }
  ]
}
```

#### GET /analytics/performance

Get performance metrics.

**Response:**
```json
{
  "response_times": {
    "avg": 1.2,
    "p50": 0.8,
    "p95": 3.5,
    "p99": 8.2
  },
  "error_rates": {
    "total_requests": 10000,
    "errors": 25,
    "error_rate": 0.0025
  },
  "model_performance": {
    "gpt-3.5-turbo": {
      "avg_response_time": 1.1,
      "success_rate": 0.998
    },
    "gpt-4": {
      "avg_response_time": 2.3,
      "success_rate": 0.995
    }
  }
}
```

### 5. User Management API

#### GET /users/profile

Get user profile information.

**Response:**
```json
{
  "user_id": "user_123",
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2024-01-01T00:00:00Z",
  "subscription": {
    "plan": "premium",
    "expires_at": "2024-12-31T23:59:59Z"
  },
  "usage": {
    "messages_this_month": 150,
    "documents_uploaded": 5,
    "api_calls_this_month": 200
  }
}
```

#### PUT /users/profile

Update user profile.

**Request Body:**
```json
{
  "username": "new_username",
  "email": "newemail@example.com",
  "preferences": {
    "default_model": "gpt-4",
    "theme": "dark",
    "language": "en"
  }
}
```

### 6. Webhook API

#### POST /webhooks

Register webhooks for real-time notifications.

**Request Body:**
```json
{
  "url": "https://your-app.com/webhook",
  "events": ["chat.completed", "document.processed", "error.occurred"],
  "secret": "your-webhook-secret"
}
```

**Response:**
```json
{
  "webhook_id": "webhook_123",
  "url": "https://your-app.com/webhook",
  "events": ["chat.completed", "document.processed", "error.occurred"],
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Error Handling

All API endpoints return appropriate HTTP status codes and error messages:

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request is invalid",
    "details": {
      "field": "message",
      "issue": "Message cannot be empty"
    }
  },
  "request_id": "req_123"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid API key
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limits

API rate limits are applied per API key:

- **Free Tier**: 100 requests/hour
- **Premium Tier**: 1000 requests/hour
- **Enterprise**: Custom limits

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## SDKs and Libraries

### Python SDK

```python
from stardust_chatbot import StardustClient

client = StardustClient(api_key="your-api-key")

# Send a chat message
response = client.chat.send(
    message="Hello, world!",
    model="gpt-3.5-turbo"
)

print(response.choices[0].message.content)
```

### JavaScript SDK

```javascript
import { StardustClient } from 'stardust-chatbot-js';

const client = new StardustClient('your-api-key');

// Send a chat message
const response = await client.chat.send({
  message: 'Hello, world!',
  model: 'gpt-3.5-turbo'
});

console.log(response.choices[0].message.content);
```

## Examples

### Complete Chat Example

```python
import requests

# Initialize client
headers = {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
}

# Send message
response = requests.post(
    'https://your-domain.com/api/v1/chat',
    headers=headers,
    json={
        'message': 'Explain quantum computing',
        'model': 'gpt-4',
        'temperature': 0.7,
        'max_tokens': 500
    }
)

result = response.json()
print(result['choices'][0]['message']['content'])
```

### Document Upload and Query Example

```python
# Upload document
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    upload_response = requests.post(
        'https://your-domain.com/api/v1/documents/upload',
        headers={'Authorization': 'Bearer YOUR_API_KEY'},
        files=files
    )

document_id = upload_response.json()['document_id']

# Query document
query_response = requests.post(
    'https://your-domain.com/api/v1/rag/query',
    headers=headers,
    json={
        'query': 'What is the main topic?',
        'document_ids': [document_id],
        'max_chunks': 3
    }
)

print(query_response.json()['context'])
```

## Support

For API support and questions:

- **Documentation**: [https://docs.stardust.ai](https://docs.stardust.ai)
- **GitHub Issues**: [https://github.com/your-username/chatbot/issues](https://github.com/your-username/chatbot/issues)
- **Email**: api-support@stardust.ai
- **Discord**: [Join our community](https://discord.gg/stardust-ai)
