<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard — Argon2id Benchmark</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, sans-serif; background: #f5f5f5; }
        .navbar { background: #4a90d9; color: #fff; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
        .navbar h1 { font-size: 1.25rem; }
        .navbar form button { background: transparent; border: 1px solid #fff; color: #fff; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; font-size: 0.875rem; }
        .navbar form button:hover { background: rgba(255,255,255,0.1); }
        .container { max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        .card { background: #fff; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 1rem; }
        .card h2 { font-size: 1.25rem; margin-bottom: 1rem; }
        .info { font-size: 0.9rem; color: #555; line-height: 1.8; }
        .info strong { color: #333; }
        .badge { display: inline-block; background: #27ae60; color: #fff; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; }
    </style>
</head>
<body>
<nav class="navbar">
    <h1>Argon2id Benchmark</h1>
    <form method="POST" action="{{ route('logout') }}">
        @csrf
        <button type="submit">Logout</button>
    </form>
</nav>
<div class="container">
    <div class="card">
        <h2>Dashboard</h2>
        <div class="info">
            <p><strong>Nama:</strong> {{ auth()->user()->name }}</p>
            <p><strong>Email:</strong> {{ auth()->user()->email }}</p>
            <p><strong>Password Hash:</strong> <span class="badge">Argon2id</span></p>
            <p><strong>Hash Preview:</strong> <code>{{ substr(auth()->user()->password, 0, 50) }}...</code></p>
            <p><strong>Login At:</strong> {{ now()->format('d M Y H:i:s') }}</p>
        </div>
    </div>
</div>
</body>
</html>
