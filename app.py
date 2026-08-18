from flask import Flask, request, jsonify, session
import sqlite3
import hashlib
import secrets
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Veritabanı bağlantısı
def get_db():
    conn = sqlite3.connect('marketpilot.db')
    conn.row_factory = sqlite3.Row
    return conn

# Tabloları oluştur
def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            name TEXT,
            created_at DATETIME
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_name TEXT,
            score REAL,
            status TEXT,
            created_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Ana sayfa
@app.route("/")
def home():
    return '''
    <h1>🚀 MarketPilotAI</h1>
    <p>Free Smart Market Analysis Tool</p>
    <a href="/register">Register</a> | <a href="/login">Login</a>
    '''

# Kayıt
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return '''
        <form method="POST">
            <input type="text" name="name" placeholder="Full Name" required><br>
            <input type="email" name="email" placeholder="Email" required><br>
            <input type="password" name="password" placeholder="Password" required minlength="6"><br>
            <button type="submit">Register</button>
        </form>
        <a href="/login">Already have an account? Login</a>
        '''
    
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    
    if not all([name, email, password]):
        return "All fields required"
    
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        conn = get_db()
        conn.execute("INSERT INTO users (email, password, name, created_at) VALUES (?, ?, ?, ?)",
                     (email, hashed, name, datetime.now()))
        conn.commit()
        conn.close()
        return '<script>alert("Registration successful!"); window.location.href="/login"</script>'
    except:
        return '<script>alert("Email already exists"); window.location.href="/register"</script>'

# Giriş
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return '''
        <form method="POST">
            <input type="email" name="email" placeholder="Email" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Login</button>
        </form>
        <a href="/register">Don't have an account? Register</a>
        '''
    
    email = request.form.get("email")
    password = request.form.get("password")
    
    if not all([email, password]):
        return "Email and password required"
    
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, hashed)).fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        return '<script>window.location.href="/dashboard"</script>'
    
    return '<script>alert("Invalid email or password"); window.location.href="/login"</script>'

# Dashboard
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return '<script>window.location.href="/login"</script>'
    
    conn = get_db()
    analyses = conn.execute(
        "SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (session['user_id'],)
    ).fetchall()
    conn.close()
    
    html = f'''
    <h1>📊 Dashboard</h1>
    <p>Welcome, {session['user_name']}!</p>
    <a href="/analyze">New Analysis</a> | <a href="/logout">Logout</a>
    <hr>
    <h3>Analysis History</h3>
    '''
    
    if analyses:
        for a in analyses:
            html += f'<p>{a["product_name"]} - {a["score"]}/100 - {a["status"]} ({a["created_at"]})</p>'
    else:
        html += '<p>No analyses yet.</p>'
    
    return html

# Analiz
@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    if 'user_id' not in session:
        return '<script>window.location.href="/login"</script>'
    
    if request.method == "GET":
        return '''
        <form id="analyzeForm">
            <input type="text" id="product_name" placeholder="Product Name" required><br>
            <button type="submit">Analyze</button>
        </form>
        <div id="result"></div>
        <a href="/dashboard">Back to Dashboard</a>
        
        <script>
        document.getElementById('analyzeForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const data = { product_name: document.getElementById('product_name').value };
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            document.getElementById('result').innerHTML = 
                '<h2>Score: ' + result.score + '/100</h2>' +
                '<p>Status: ' + result.status + '</p>' +
                '<p>Recommendation: ' + result.recommendation + '</p>';
        });
        </script>
        '''
    
    import random
    data = request.get_json()
    product_name = data.get("product_name", "Unknown")
    score = random.randint(45, 95)
    
    if score >= 80:
        status = "EXCELLENT"
        recommendation = "Strong launch! Start now!"
    elif score >= 60:
        status = "GOOD"
        recommendation = "Promising. Optimize and launch!"
    elif score >= 40:
        status = "WARNING"
        recommendation = "Validate first. Deepen research."
    else:
        status = "CRITICAL"
        recommendation = "Low priority. Pivot or target new market."
    
    conn = get_db()
    conn.execute(
        "INSERT INTO analyses (user_id, product_name, score, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (session['user_id'], product_name, score, status, datetime.now())
    )
    conn.commit()
    conn.close()
    
    return jsonify({"score": score, "status": status, "recommendation": recommendation})

# Çıkış
@app.route("/logout")
def logout():
    session.clear()
    return '<script>window.location.href="/"</script>'

# Başlat
if __name__ == "__main__":
    port = int(10000)
    app.run(host="0.0.0.0", port=port, debug=True)
