# StreamIt – Architecture Freeze

## Platforms
- Website (watch + app downloads)
- Windows application (streaming)
- Android application (streaming)

## Backend
- Django + Django REST Framework
- JWT authentication
- Google OAuth
- Single backend for all clients

## Video Streaming
- External video provider
- Backend only handles authorization
- Video data does NOT pass through backend

## Clients
- Website: Next.js
- Windows app: Electron (web wrapper)
- Android app: React Native

## Rules
- One backend, no exceptions
- No client talks directly to video provider
- APIs are frozen before UI work
