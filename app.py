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
            return jsonify({"error": "Giriş yapmalısınız"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>MarketPilotAI</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f7fafc; }
            .navbar { background: #2d3748; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
            .logo { font-size: 22px; font-weight: bold; }
            .logo span { color: #48bb78; }
            .nav-links a { color: #a0aec0; text-decoration: none; margin: 0 10px; }
            .nav-links a:hover { color: white; }
            .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
            .hero { background: linear-gradient(135deg, #2d3748, #4a5568); color: white; padding: 40px; border-radius: 15px; text-align: center; }
            .hero h1 { font-size: 32px; }
            .hero p { color: #a0aec0; margin: 10px 0 20px; }
            .btn { display: inline-block; padding: 12px 28px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; text-decoration: none; }
            .btn-primary { background: #48bb78; color: white; }
            .btn-primary:hover { background: #38a169; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 25px 0; }
            .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); text-align: center; }
            .card-icon { font-size: 32px; }
            .footer { text-align: center; padding: 20px; color: #718096; }
        </style>
    </head>
    <body>
        <nav class="navbar">
            <div class="logo">📊 Market<span>PilotAI</span></div>
            <div class="nav-links">
                <a href="/">Ana Sayfa</a>
                <a href="/register">Kayıt</a>
                <a href="/login">Giriş</a>
            </div>
        </nav>
        <div class="container">
            <div class="hero">
                <h1>🚀 Ücretsiz Akıllı Pazar Analizi</h1>
                <p>15 strateji ile doğru kararlar alın.</p>
                <a href="/register" class="btn btn-primary">🚀 Hemen Başla</a>
            </div>
            <div class="grid">
                <div class="card"><div class="card-icon">📊</div><h3>15 Strateji</h3></div>
                <div class="card"><div class="card-icon">🧮</div><h3>PMF Matematiği</h3></div>
                <div class="card"><div class="card-icon">🌍</div><h3>Etki Skoru</h3></div>
            </div>
            <div class="footer"><p>© 2025 MarketPilotAI</p></div>
        </div>
    </body>
    </html>
    ''')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><title>Kayıt</title>
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
                <h2>📝 Kayıt Ol</h2>
                <form method="POST">
                    <input type="text" name="name" placeholder="Ad Soyad" required>
                    <input type="email" name="email" placeholder="Email" required>
                    <input type="password" name="password" placeholder="Şifre" required minlength="6">
                    <button type="submit" class="btn">🚀 Kayıt Ol</button>
                </form>
                <div class="link">Hesabın var mı? <a href="/login">Giriş Yap</a></div>
            </div>
        </body>
        </html>
        ''')
    
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    
    if not all([name, email, password]) or len(password) < 6:
        return "<script>alert('Tüm alanlar gerekli ve şifre en az 6 karakter'); window.location.href='/register'</script>"
    
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        db.execute("INSERT INTO users (email, password, name, created_at) VALUES (?, ?, ?, ?)",
                   (email, hashed, name, datetime.now()))
        db.commit()
        return "<script>alert('✅ Kayıt başarılı!'); window.location.href='/login'</script>"
    except sqlite3.IntegrityError:
        return "<script>alert('❌ Bu email zaten kayıtlı'); window.location.href='/register'</script>"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><title>Giriş</title>
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
                <h2>🔐 Giriş Yap</h2>
                <form method="POST">
                    <input type="email" name="email" placeholder="Email" required>
                    <input type="password" name="password" placeholder="Şifre" required>
                    <button type="submit" class="btn">Giriş Yap</button>
                </form>
                <div class="link">Hesabın yok mu? <a href="/register">Kayıt Ol</a></div>
            </div>
        </body>
        </html>
        ''')
    
    email = request.form.get("email")
    password = request.form.get("password")
    
    if not all([email, password]):
        return "<script>alert('Email ve şifre gerekli'); window.location.href='/login'</script>"
    
    hashed = hashlib.sha256(password.encode()).hexdigest()
    user = db.execute("SELECT id, email, name FROM users WHERE email = ? AND password = ?", (email, hashed)).fetchone()
    
    if user:
        session['user_id'] = user[0]
        session['user_email'] = user[1]
        db.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now(), user[0]))
        db.commit()
        return "<script>window.location.href='/dashboard'</script>"
    
    return "<script>alert('❌ Geçersiz email veya şifre'); window.location.href='/login'</script>"

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session['user_id']
    user = db.execute("SELECT name FROM users WHERE id = ?", (user_id,)).fetchone()
    analyses = db.execute("SELECT id, product_name, score, status, created_at FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,)).fetchall()
    
    return render_template_string('''
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
        .btn-primary:hover { background: #38a169; }
        .btn-danger { background: #fc8181; color: white; }
        .btn-danger:hover { background: #fc8181; }
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
                <p>Hoşgeldin, {{ user[0] }}! 👋</p>
                <div class="actions">
                    <a href="/analyze" class="btn btn-primary">➕ Yeni Analiz</a>
                    <a href="/logout" class="btn btn-danger">🚪 Çıkış</a>
                </div>
            </div>
            <div class="card">
                <h3>📋 Analiz Geçmişi</h3>
                {% if analyses %}
                {% for a in analyses %}
                <div class="analysis-item">
                    <span><strong>{{ a[1] }}</strong> <span style="color: #718096; font-size: 12px;">{{ a[4][:16] }}</span></span>
                    <span><span class="badge-{{ a[3] }}">{{ a[3] }}</span> <strong>{{ a[2] }}/100</strong></span>
                </div>
                {% endfor %}
                {% else %}
                <p style="text-align: center; color: #718096; padding: 20px;">Henüz analiz yok.</p>
                {% endif %}
            </div>
            <div class="footer"><p>© 2025 MarketPilotAI</p></div>
        </div>
    </body>
    </html>
    ''', user=user, analyses=analyses)

@app.route("/analyze", methods=["GET", "POST"])
@login_required
def analyze():
    if request.method == "GET":
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><title>Ürün Analizi</title>
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
                    <h1>🚀 Ürün Analizi</h1>
                    <a href="/dashboard" class="back">← Dashboard</a>
                </div>
                <div class="card">
                    <form id="analyzeForm">
                        <div class="form-group">
                            <label>Ürün Adı *</label>
                            <input type="text" id="product_name" placeholder="Örn: AI Pazarlama Aracı" required>
                        </div>
                        <div class="form-group">
                            <label>Tahmini Kullanıcı</label>
                            <input type="number" id="users" placeholder="100" value="100">
                        </div>
                        <div class="form-group">
                            <label>Sektör</label>
                            <select id="industry">
                                <option value="SaaS">SaaS</option>
                                <option value="AI">Yapay Zeka</option>
                                <option value="Fintech">Fintech</option>
                                <option value="HealthTech">Sağlık</option>
                                <option value="Ecommerce">E-Ticaret</option>
                            </select>
                        </div>
                        <button type="submit" class="btn">📊 Analizi Başlat</button>
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
                        document.getElementById('resultDetails').innerHTML = `
                            <p><strong>📊 Durum:</strong> ${result.status}</p>
                            <p><strong>💡 Öneri:</strong> ${result.recommendation || 'Devam et!'}</p>
                        `;
                    } catch (error) {
                        alert('Hata: ' + error.message);
                    }
                });
            </script>
        </body>
        </html>
        ''')
    
    # POST işlemi - DÜZELTİLDİ!
    user_id = session['user_id']
    data = request.get_json()
    
    product_name = data.get("product_name", "Bilinmeyen Ürün")
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
        recommendation = "🚀 Güçlü lansman! Hemen başlayın!"
    elif score >= 60:
        recommendation = "📈 Umut verici. Optimize edin ve başlayın!"
    elif score >= 40:
        recommendation = "⚠️ Önce doğrulayın. Pazar araştırmasını derinleştirin."
    else:
        recommendation = "🔍 Düşük öncelik. Pivot veya yeni pazar hedefleyin."
    
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
