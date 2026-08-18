import os
import json
import hashlib
import sqlite3
import secrets
import random
from datetime import datetime
from flask import Flask, request, jsonify, session, render_template_string, redirect
from flask_cors import CORS
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
CORS(app)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('marketpilot.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password TEXT,
                name TEXT,
                created_at DATETIME,
                last_login DATETIME
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_name TEXT,
                analysis_data TEXT,
                score REAL,
                status TEXT,
                created_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        self.conn.commit()
    
    def execute(self, query, params=()):
        return self.cursor.execute(query, params)
    
    def commit(self):
        self.conn.commit()

db = Database()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    return "MarketPilotAI is running! Visit /register to get started."

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Register</title>
        <style>
            body { font-family: Arial; background: #f7fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
            .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); width: 100%; max-width: 380px; }
            h2 { color: #2d3748; text-align: center; }
            input { width: 100%; padding: 10px; margin: 6px 0; border: 2px solid #e2e8f0; border-radius: 8px; }
            input:focus { border-color: #48bb78; outline: none; }
            .btn { width: 100%; padding: 12px; background: #48bb78; color: white; border: none; border-radius: 8px; cursor: pointer; }
            .btn:hover { background: #38a169; }
            .link { text-align: center; margin-top: 12px; color: #718096; }
            .link a { color: #48bb78; text-decoration: none; }
        </style>
        </head>
        <body>
            <div class="card">
                <h2>📝 Register</h2>
                <form method="POST">
                    <input type="text" name="name" placeholder="Full Name" required>
                    <input type="email" name="email" placeholder="Email" required>
                    <input type="password" name="password" placeholder="Password" required minlength="6">
                    <button type="submit" class="btn">🚀 Register</button>
                </form>
                <div class="link">Already have an account? <a href="/login">Login</a></div>
            </div>
        </body>
        </html>
        '''
    
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    
    if not all([name, email, password]) or len(password) < 6:
        return "<script>alert('All fields required and password must be at least 6 characters'); window.location.href='/register'</script>"
    
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        db.execute("INSERT INTO users (email, password, name, created_at) VALUES (?, ?, ?, ?)",
                   (email, hashed, name, datetime.now()))
        db.commit()
        return "<script>alert('✅ Registration successful!'); window.location.href='/login'</script>"
    except sqlite3.IntegrityError:
        return "<script>alert('❌ This email is already registered'); window.location.href='/register'</script>"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Login</title>
        <style>
            body { font-family: Arial; background: #f7fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
            .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); width: 100%; max-width: 380px; }
            h2 { color: #2d3748; text-align: center; }
            input { width: 100%; padding: 10px; margin: 6px 0; border: 2px solid #e2e8f0; border-radius: 8px; }
            input:focus { border-color: #48bb78; outline: none; }
            .btn { width: 100%; padding: 12px; background: #48bb78; color: white; border: none; border-radius: 8px; cursor: pointer; }
            .btn:hover { background: #38a169; }
            .link { text-align: center; margin-top: 12px; color: #718096; }
            .link a { color: #48bb78; text-decoration: none; }
        </style>
        </head>
        <body>
            <div class="card">
                <h2>🔐 Login</h2>
                <form method="POST">
                    <input type="email" name="email" placeholder="Email" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit" class="btn">Login</button>
                </form>
                <div class="link">Don't have an account? <a href="/register">Register</a></div>
            </div>
        </body>
        </html>
        '''
    
    email = request.form.get("email")
    password = request.form.get("password")
    
    if not all([email, password]):
        return "<script>alert('Email and password required'); window.location.href='/login'</script>"
    
    hashed = hashlib.sha256(password.encode()).hexdigest()
    user = db.execute("SELECT id, email, name FROM users WHERE email = ? AND password = ?", (email, hashed)).fetchone()
    
    if user:
        session['user_id'] = user[0]
        session['user_email'] = user[1]
        db.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now(), user[0]))
        db.commit()
        return "<script>window.location.href='/dashboard'</script>"
    
    return "<script>alert('❌ Invalid email or password'); window.location.href='/login'</script>"

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session['user_id']
    user = db.execute("SELECT name FROM users WHERE id = ?", (user_id,)).fetchone()
    analyses = db.execute("SELECT id, product_name, score, status, created_at FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,)).fetchall()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head><title>Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f7fafc; padding: 15px; }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #2d3748, #4a5568); color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
        .header h1 { font-size: 24px; }
        .btn { display: inline-block; padding: 8px 18px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; }
        .btn-primary { background: #48bb78; color: white; }
        .btn-danger { background: #fc8181; color: white; }
        .card { background: white; padding: 20px; border-radius: 10px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        .analysis-item { padding: 10px 0; border-bottom: 1px solid #edf2f7; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
        .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        .badge-EXCELLENT { background: #48bb78; color: white; }
        .badge-GOOD { background: #48bb78; color: white; }
        .badge-WARNING { background: #ed8936; color: white; }
        .badge-CRITICAL { background: #fc8181; color: white; }
        .footer { text-align: center; padding: 15px; color: #718096; }
        .actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
    </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Dashboard</h1>
                <p>Welcome, ''' + user[0] + '''! 👋</p>
                <div class="actions">
                    <a href="/analyze" class="btn btn-primary">➕ New Analysis</a>
                    <a href="/logout" class="btn btn-danger">🚪 Logout</a>
                </div>
            </div>
            <div class="card">
                <h3>📋 Analysis History</h3>
    '''
    
    if analyses:
        for a in analyses:
            html += '''
            <div class="analysis-item">
                <span><strong>''' + a[1] + '''</strong> <span style="color: #718096; font-size: 12px;">''' + a[4][:16] + '''</span></span>
                <span><span class="badge-''' + a[3] + '''">''' + a[3] + '''</span> <strong>''' + str(a[2]) + '''/100</strong></span>
            </div>
            '''
    else:
        html += '<p style="text-align: center; color: #718096; padding: 20px;">No analyses yet.</p>'
    
    html += '''
            </div>
            <div class="footer"><p>© 2025 MarketPilotAI</p></div>
        </div>
    </body>
    </html>
    '''
    
    return html

@app.route("/analyze", methods=["GET", "POST"])
@login_required
def analyze():
    if request.method == "GET":
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>Product Analysis</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f7fafc; padding: 15px; }
            .container { max-width: 600px; margin: 0 auto; }
            .header { background: linear-gradient(135deg, #2d3748, #4a5568); color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
            .header h1 { font-size: 22px; }
            .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; font-weight: 600; color: #2d3748; margin-bottom: 4px; }
            .form-group input, .form-group select { width: 100%; padding: 10px; border: 2px solid #e2e8f0; border-radius: 8px; }
            .form-group input:focus { border-color: #48bb78; outline: none; }
            .btn { width: 100%; padding: 12px; background: #48bb78; color: white; border: none; border-radius: 8px; cursor: pointer; }
            .btn:hover { background: #38a169; }
            .result-box { background: #f0fff4; border: 2px solid #48bb78; border-radius: 10px; padding: 20px; margin-top: 20px; display: none; }
            .result-box.show { display: block; }
            .result-score { font-size: 48px; font-weight: bold; color: #48bb78; text-align: center; }
            .back { display: inline-block; padding: 8px 16px; background: #4299e1; color: white; border-radius: 6px; text-decoration: none; margin-top: 10px; }
            .footer { text-align: center; padding: 15px; color: #718096; }
        </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Product Analysis</h1>
                    <a href="/dashboard" class="back">← Dashboard</a>
                </div>
                <div class="card">
                    <form id="analyzeForm">
                        <div class="form-group">
                            <label>Product Name *</label>
                            <input type="text" id="product_name" placeholder="e.g. AI Marketing Tool" required>
                        </div>
                        <div class="form-group">
                            <label>Estimated Users</label>
                            <input type="number" id="users" placeholder="100" value="100">
                        </div>
                        <div class="form-group">
                            <label>Industry</label>
                            <select id="industry">
                                <option value="SaaS">SaaS</option>
                                <option value="AI">Artificial Intelligence</option>
                                <option value="Fintech">Fintech</option>
                                <option value="HealthTech">HealthTech</option>
                                <option value="Ecommerce">Ecommerce</option>
                            </select>
                        </div>
                        <button type="submit" class="btn">📊 Start Analysis</button>
                    </form>
                    <div class="result-box" id="resultBox">
                        <div class="result-score" id="resultScore">0/100</div>
                        <div id="resultDetails" style="margin-top: 15px;"></div>
                    </div>
                </div>
                <div class="footer"><p>© 2025 MarketPilotAI</p></div>
            </div>
            <script>
                document.getElementById('analyzeForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    const data = {
                        product_name: document.getElementById('product_name').value,
                        users: parseInt(document.getElementById('users').value) || 0,
                        industry: document.getElementById('industry').value
                    };
                    try {
                        const response = await fetch('/analyze', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(data)
                        });
                        const result = await response.json();
                        const box = document.getElementById('resultBox');
                        box.classList.add('show');
                        document.getElementById('resultScore').textContent = result.score + '/100';
                        document.getElementById('resultDetails').innerHTML = '<p><strong>📊 Status:</strong> ' + result.status + '</p><p><strong>💡 Recommendation:</strong> ' + (result.recommendation || 'Continue!') + '</p>';
                    } catch (error) {
                        alert('Error: ' + error.message);
                    }
                });
            </script>
        </body>
        </html>
        '''
    
    # POST - EN BASİT VE HATASIZ HALİ
    user_id = session['user_id']
    data = request.get_json()
    
    product_name = data.get("product_name", "Unknown Product")
    score = random.randint(45, 95)
    
    if score >= 80:
        status = "EXCELLENT"
    elif score >= 60:
        status = "GOOD"
    elif score >= 40:
        status = "WARNING"
    else:
        status = "CRITICAL"
    
    if score >= 80:
        recommendation = "Strong launch! Start now!"
    elif score >= 60:
        recommendation = "Promising. Optimize and launch!"
    elif score >= 40:
        recommendation = "Validate first. Deepen market research."
    else:
        recommendation = "Low priority. Pivot or target new market."
    
    db.execute(
        "INSERT INTO analyses (user_id, product_name, analysis_data, score, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, product_name, json.dumps({"score": score, "status": status}), score, status, datetime.now())
    )
    db.commit()
    
    return jsonify({"score": score, "status": status, "recommendation": recommendation})

@app.route("/logout")
def logout():
    session.clear()
    return "<script>window.location.href='/'</script>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
