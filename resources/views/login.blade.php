<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login — Argon2id Benchmark</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .card { background: #fff; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        h1 { margin-bottom: 1.5rem; font-size: 1.5rem; text-align: center; }
        .form-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.25rem; font-weight: 600; font-size: 0.875rem; }
        input { width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; }
        input:focus { outline: none; border-color: #4a90d9; }
        button { width: 100%; padding: 0.75rem; background: #4a90d9; color: #fff; border: none; border-radius: 4px; font-size: 1rem; cursor: pointer; margin-top: 0.5rem; }
        button:hover { background: #357abd; }
        .link { text-align: center; margin-top: 1rem; font-size: 0.875rem; }
        .link a { color: #4a90d9; text-decoration: none; }
        .error { color: #e74c3c; font-size: 0.8rem; margin-top: 0.25rem; }
    </style>
</head>
<body>
<div class="card">
    <h1>Login</h1>
    @if(session('status'))
        <div style="color: #27ae60; margin-bottom: 1rem; font-size: 0.875rem;">{{ session('status') }}</div>
    @endif
    <form method="POST" action="{{ route('login') }}">
        @csrf
        <div class="form-group">
            <label for="email">Email</label>
            <input type="email" id="email" name="email" value="{{ old('email') }}" required autofocus>
            @error('email')<div class="error">{{ $message }}</div>@enderror
        </div>
        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required>
            @error('password')<div class="error">{{ $message }}</div>@enderror
        </div>
        <button type="submit">Login</button>
    </form>
    <div class="link">Belum punya akun? <a href="{{ route('register') }}">Register</a></div>
</div>
</body>
</html>
