<div align="center">
  <h1>StreamIt Backend</h1>
  <p><strong>Real-Time Watch-Together Infrastructure</strong></p>
  <p>
    <img alt="Python" src="https://img.shields.io/badge/Python-3.11-blue" />
    <img alt="Django" src="https://img.shields.io/badge/Django-4.2-green" />
    <img alt="DRF" src="https://img.shields.io/badge/DRF-API-red" />
    <img alt="Channels" src="https://img.shields.io/badge/Channels-ASGI-informational" />
    <img alt="Redis" src="https://img.shields.io/badge/Redis-Realtime-critical" />
  </p>
</div>

<p>StreamIt is a real-time backend system that powers a synchronized watch-together platform.</p>

<p>It allows multiple users to:</p>
<ul>
  <li>Join shared rooms</li>
  <li>Watch videos in sync</li>
  <li>Chat in real time</li>
  <li>Resume sessions after disconnection</li>
  <li>Track watch progress</li>
  <li>Discover live public rooms</li>
</ul>

<p>This repository contains the backend service only (no frontend).</p>

<h2>What StreamIt Does (Simple Explanation)</h2>
<p>Imagine a group of people watching the same movie together online.</p>

<p>StreamIt ensures:</p>
<ul>
  <li>Only one person (the host) controls playback</li>
  <li>Everyone stays perfectly synchronized</li>
  <li>Late joiners immediately catch up</li>
  <li>Chat works in real time</li>
  <li>If the host disconnects, the room does not instantly die</li>
  <li>Rooms can be public or private</li>
  <li>Watch progress can be saved and resumed</li>
</ul>

<p>This is the server infrastructure that makes all of that possible.</p>

<h2>Core Features</h2>
<h3>Authentication</h3>
<ul>
  <li>Email + password login</li>
  <li>Guest login</li>
  <li>JWT-secured WebSockets</li>
  <li>Custom Django user model</li>
</ul>

<h3>Room System</h3>
<ul>
  <li>Public rooms</li>
  <li>Private rooms</li>
  <li>Password protected</li>
  <li>Host approval required</li>
  <li>Host-only playback control</li>
  <li>Explicit room deletion</li>
  <li>Grace period if host disconnects</li>
</ul>

<h3>Real-Time Sync (WebSockets)</h3>
<ul>
  <li>Live presence tracking</li>
  <li>USER_JOINED / USER_LEFT</li>
  <li>Host-only PLAY, PAUSE, SEEK</li>
  <li>Automatic playback sync for late joiners</li>
  <li>Chat history on connect</li>
  <li>Structured event protocol</li>
</ul>

<h3>Grace Period System</h3>
<p>If the host disconnects:</p>
<ul>
  <li>Room enters GRACE state</li>
  <li>Participants stay connected</li>
  <li>Host can reconnect within allowed time</li>
  <li>If grace expires, room transitions to EXPIRED</li>
</ul>

<p>No accidental room destruction due to bad Wi-Fi.</p>

<h3>Media Provider Integration</h3>
<ul>
  <li>External video embed URL generation</li>
  <li>Support for: color, autoPlay, nextEpisode, episodeSelector, progress</li>
  <li>Server-generated canonical embed URLs</li>
</ul>

<h3>Watch Progress Tracking</h3>
<ul>
  <li>Stores progress per user, room, and content ID</li>
  <li>Idempotent updates</li>
  <li>Resume support</li>
  <li>Does not interfere with playback authority</li>
</ul>

<h3>Public Room Discovery</h3>
<ul>
  <li>Lists live public rooms</li>
  <li>Viewer count derived from live presence</li>
  <li>Private rooms are never exposed</li>
</ul>

<h2>Architecture Overview</h2>
<p>StreamIt uses a hybrid HTTP + WebSocket architecture.</p>

<h3>Stack</h3>
<table>
  <thead>
    <tr>
      <th align="left">Layer</th>
      <th align="left">Technology</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Language</td>
      <td>Python 3.11</td>
    </tr>
    <tr>
      <td>Framework</td>
      <td>Django 4.2</td>
    </tr>
    <tr>
      <td>API</td>
      <td>Django REST Framework</td>
    </tr>
    <tr>
      <td>Realtime</td>
      <td>Django Channels</td>
    </tr>
    <tr>
      <td>ASGI Server</td>
      <td>Daphne</td>
    </tr>
    <tr>
      <td>Cache/Fan-out</td>
      <td>Redis (real-time fan-out + cache)</td>
    </tr>
    <tr>
      <td>Database</td>
      <td>SQLite (development)</td>
    </tr>
    <tr>
      <td>Auth</td>
      <td>JWT (SimpleJWT)</td>
    </tr>
  </tbody>
</table>

<h2>How It Works</h2>
<h3>HTTP (REST APIs)</h3>
<p>Handles:</p>
<ul>
  <li>Login</li>
  <li>Room creation</li>
  <li>Join requests</li>
  <li>Approvals</li>
  <li>Deletion</li>
  <li>Watch progress</li>
</ul>

<h3>WebSockets</h3>
<p>Handles:</p>
<ul>
  <li>Real-time playback sync</li>
  <li>Presence</li>
  <li>Chat</li>
  <li>Host grace handling</li>
</ul>

<h3>Redis is used for</h3>
<ul>
  <li>Channel layer fan-out</li>
  <li>Live room state cache</li>
  <li>Viewer counters</li>
  <li>Grace TTL enforcement</li>
</ul>

<h3>Database remains authoritative for</h3>
<ul>
  <li>Room lifecycle</li>
  <li>Participants</li>
  <li>Playback state</li>
  <li>Watch progress</li>
</ul>

<details>
  <summary><strong>Test Coverage</strong></summary>
  <p>This backend includes automated tests for:</p>
  <ul>
    <li>Room lifecycle transitions</li>
    <li>Grace period expiry</li>
    <li>Host authority enforcement</li>
    <li>Redis integration</li>
    <li>Public room listing</li>
    <li>Media embed builder</li>
    <li>Watch progress persistence</li>
    <li>WebSocket playback rules</li>
  </ul>
  <p>Run tests:</p>
  <pre><code>python manage.py test
</code></pre>
  <p>No manual room creation required. Everything is auto-created during tests.</p>
</details>

<h2>Setup</h2>
<h3>Clone and Install</h3>
<pre><code>git clone &lt;repo&gt;
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
</code></pre>

<h3>Run Database Migrations</h3>
<pre><code>python manage.py migrate
</code></pre>

<h3>Create Admin User (Optional)</h3>
<pre><code>python manage.py createsuperuser
</code></pre>

<h3>Start Redis</h3>
<p>Make sure Redis is running on:</p>
<pre><code>127.0.0.1:6379
</code></pre>

<h3>Start Server</h3>
<pre><code>python manage.py runserver
</code></pre>

<details>
  <summary><strong>API Overview</strong></summary>
  <p>Base path: <code>/api/</code></p>

  <h3>Auth</h3>
  <ul>
    <li><code>POST /api/auth/login/</code></li>
    <li><code>POST /api/auth/guest/</code></li>
    <li><code>POST /api/auth/logout/</code></li>
  </ul>

  <h3>Rooms</h3>
  <ul>
    <li><code>POST /api/rooms/create/</code></li>
    <li><code>POST /api/rooms/join/</code></li>
    <li><code>POST /api/rooms/approve/</code></li>
    <li><code>POST /api/rooms/delete/</code></li>
    <li><code>GET /api/rooms/public/</code></li>
  </ul>

  <h3>Watch Progress</h3>
  <ul>
    <li><code>POST /api/rooms/progress/save/</code></li>
    <li><code>GET /api/rooms/progress/get/</code></li>
  </ul>
</details>

<details>
  <summary><strong>WebSocket Endpoint</strong></summary>
  <pre><code>ws://localhost:8000/ws/room/&lt;room_code&gt;/?token=&lt;JWT&gt;
</code></pre>
  <p>JWT is mandatory.</p>
</details>

<h2>Design Principles</h2>
<p>This backend was built with strict rules:</p>
<ul>
  <li>No async ORM inside WebSocket consumers</li>
  <li>Redis writes are centralized</li>
  <li>Database is authoritative for lifecycle</li>
  <li>Host authority is absolute</li>
  <li>Tests define expected behavior</li>
  <li>Changelog acts as behavioral contract</li>
</ul>

<h2>Stability Guarantees</h2>
<ul>
  <li>Playback authority cannot be hijacked</li>
  <li>Rooms cannot resurrect after expiration</li>
  <li>Grace period is enforced server-side</li>
  <li>Public listing never exposes private rooms</li>
  <li>Chat disable does not break playback</li>
  <li>Watch progress does not interfere with sync</li>
</ul>

<h2>Roadmap</h2>
<p>Planned future phases:</p>
<ul>
  <li>PostgreSQL production migration</li>
  <li>Dockerized deployment</li>
  <li>Horizontal scaling</li>
  <li>Rate limiting</li>
  <li>Audit logging</li>
  <li>Frontend integration</li>
  <li>Provider abstraction layer</li>
  <li>Metrics and monitoring</li>
</ul>

<h2>Project Status</h2>
<ul>
  <li>Phase 0: Realtime stabilization</li>
  <li>Phase 1: Lifecycle state machine</li>
  <li>Phase 2: Media provider integration and progress tracking</li>
  <li>Phase 3: Advanced room analytics (planned)</li>
</ul>

<h2>Author</h2>
<p>Built as a structured, industrial-grade backend architecture project focused on real-time systems, authority enforcement, and state correctness.</p>
