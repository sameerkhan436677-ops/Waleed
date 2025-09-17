const express = require("express");
const fs = require("fs");
const path = require("path");
const pino = require("pino");
const multer = require("multer");
const {
    makeInMemoryStore,
    useMultiFileAuthState,
    delay,
    makeCacheableSignalKeyStore,
    Browsers,
    fetchLatestBaileysVersion,
    makeWASocket,
    isJidBroadcast
} = require("@whiskeysockets/baileys");

const app = express();
const PORT = 5000;

// Create necessary directories
if (!fs.existsSync("temp")) {
    fs.mkdirSync("temp");
}
if (!fs.existsSync("uploads")) {
    fs.mkdirSync("uploads");
}
if (!fs.existsSync("public")) {
    fs.mkdirSync("public");
}

const upload = multer({ dest: "uploads/" });

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Store active client instances and tasks
const activeClients = new Map();
const activeTasks = new Map();
const activeUsers = new Set(); 

app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/status', (req, res) => {
    res.json({
        activeClients: activeClients.size,
        activeTasks: activeTasks.size,
        activeUsers: activeUsers.size 
    });
});

app.get("/code", async (req, res) => {
    const num = req.query.number.replace(/[^0-9]/g, "");
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
    const sessionPath = path.join("temp", sessionId);
    
    activeUsers.add(sessionId);

    if (!fs.existsSync(sessionPath)) {
        fs.mkdirSync(sessionPath, { recursive: true });
    }

    try {
        const { state, saveCreds } = await useMultiFileAuthState(sessionPath);
        const { version } = await fetchLatestBaileysVersion();
        
        const waClient = makeWASocket({
            version,
            auth: {
                creds: state.creds,
                keys: makeCacheableSignalKeyStore(state.keys, pino({ level: "fatal" }).child({ level: "fatal" }))
            },
            printQRInTerminal: false,
            logger: pino({ level: "fatal" }).child({ level: "fatal" }),
            browser: Browsers.ubuntu('Chrome'),
            syncFullHistory: false,
            generateHighQualityLinkPreview: true,
            shouldIgnoreJid: jid => isJidBroadcast(jid),
            getMessage: async key => {
                return {}
            }
        });

        if (!waClient.authState.creds.registered) {
            await delay(1500);
            
            const phoneNumber = num.replace(/[^0-9]/g, "");
            const code = await waClient.requestPairingCode(phoneNumber);
            
            activeClients.set(sessionId, {  
                client: waClient,  
                number: num,  
                authPath: sessionPath  
            });  

            res.send(`  
                <div style="padding: 20px; background-color: #f9f9f9; border-radius: 8px; border: 1px solid #ddd; text-align: center;">
                    <h2>Pairing Code: ${code}</h2>  
                    <p style="font-size: 16px;">Save this code to pair your device.</p>
                    <a href="/">Go Back to Home</a>  
                </div>  
            `);  
        }  

        waClient.ev.on("creds.update", saveCreds);  
        waClient.ev.on("connection.update", async (s) => {  
            const { connection, lastDisconnect } = s;  
            if (connection === "open") {  
                console.log(`WhatsApp Connected for ${num}! Session ID: ${sessionId}`);  
            } else if (connection === "close" && lastDisconnect?.error?.output?.statusCode !== 401) {  
                console.log(`Reconnecting for Session ID: ${sessionId}...`);  
                await delay(10000);  
                initializeClient(sessionId, num, sessionPath);  
            }  
        });

    } catch (err) {
        console.error("Error in pairing:", err);
        activeUsers.delete(sessionId);
        res.status(500).send(`<div><h2>Error: ${err.message}</h2><br><a href="/">Go Back</a></div>`);
    }
});

async function initializeClient(sessionId, num, sessionPath) {
    try {
        const { state, saveCreds } = await useMultiFileAuthState(sessionPath);
        const { version } = await fetchLatestBaileysVersion();
        
        const waClient = makeWASocket({
            version,
            auth: {
                creds: state.creds,
                keys: makeCacheableSignalKeyStore(state.keys, pino({ level: "fatal" }).child({ level: "fatal" }))
            },
            printQRInTerminal: false,
            logger: pino({ level: "fatal" }).child({ level: "fatal" }),
            browser: Browsers.ubuntu('Chrome'),
            syncFullHistory: false
        });

        activeClients.set(sessionId, {  
            client: waClient,  
            number: num,  
            authPath: sessionPath  
        });  

        waClient.ev.on("creds.update", saveCreds);  
        waClient.ev.on("connection.update", async (s) => {  
            const { connection, lastDisconnect } = s;  
            if (connection === "open") {  
                console.log(`Reconnected successfully for Session ID: ${sessionId}`);  
            } else if (connection === "close" && lastDisconnect?.error?.output?.statusCode !== 401) {  
                console.log(`Reconnecting again for Session ID: ${sessionId}...`);  
                await delay(10000);  
                initializeClient(sessionId, num, sessionPath);  
            }  
        });

    } catch (err) {
        console.error(`Reconnection failed for Session ID: ${sessionId}`, err);
    }
}

app.post("/send-message", upload.single("messageFile"), async (req, res) => {
    const { target, targetType, delaySec, prefix } = req.body;
    const taskId = `task_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
    
    let sessionId;
    let clientInfo;
    for (const [key, value] of activeClients.entries()) {
        sessionId = key;
        clientInfo = value;
        break;
    }

    if (!sessionId || !clientInfo) {
        return res.status(400).send(`<h2>Error: No active WhatsApp session found</h2><br><a href="/">Go Back</a>`);
    }

    const { client: waClient } = clientInfo;
    const filePath = req.file?.path;

    if (!target || !filePath || !targetType || !delaySec) {
        return res.status(400).send(`<h2>Error: Missing required fields</h2><br><a href="/">Go Back</a>`);
    }

    try {
        const messages = fs.readFileSync(filePath, "utf-8").split("\n").filter(msg => msg.trim() !== "");
        let index = 0;

        const taskInfo = {
            sessionId,
            isSending: true,
            stopRequested: false,
            totalMessages: messages.length,
            sentMessages: 0,
            target,
            startTime: new Date()
        };
        
        activeTasks.set(taskId, taskInfo);
        
        res.send(`
            <script>
                localStorage.setItem('wa_task_id', '${taskId}');
                window.location.href = '/task-status?taskId=${taskId}';
            </script>
        `);
        
        while (taskInfo.isSending && !taskInfo.stopRequested) {  
            let msg = messages[index];  
            if (prefix && prefix.trim() !== "") {  
                msg = `${prefix.trim()} ${msg}`;  
            }  
            
            const recipient = targetType === "group" ? target + "@g.us" : target + "@s.whatsapp.net";

            await waClient.sendMessage(recipient, { text: msg });  
            console.log(`[${taskId}] Sent message to ${target}`);  

            taskInfo.sentMessages++;
            index = (index + 1) % messages.length;  
            await delay(delaySec * 1000);  
        }  

        taskInfo.endTime = new Date();
        taskInfo.isSending = false;

    } catch (error) {
        console.error(`[${taskId}] Error:`, error);
        taskInfo.error = error.message;
        taskInfo.isSending = false;
    } finally {
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
        }
    }
});

app.get("/task-status", (req, res) => {
    const taskId = req.query.taskId;
    if (!taskId || !activeTasks.has(taskId)) {
        return res.status(404).send(`<h2>Error: Invalid Task ID</h2><br><a href="/">Go Back</a>`);
    }

    const taskInfo = activeTasks.get(taskId);
    res.send(`
        <html>
        <head>
            <title>Task Status</title>
            <style>
                body { background-color: #f0f2f5; font-family: Arial, sans-serif; color: #333; text-align: center; padding: 20px; }
                .container { max-width: 800px; margin: 0 auto; padding: 20px; background-color: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.1); border-radius: 8px; }
                h1 { color: #075e54; }
                .task-id { font-size: 24px; background-color: #e7f7e7; padding: 15px; border-radius: 10px; display: inline-block; margin: 20px 0; }
                .status-item { margin: 15px 0; font-size: 18px; }
                .status-value { font-weight: bold; color: #25d366; }
                a { display: inline-block; margin-top: 30px; padding: 10px 20px; background-color: #25d366; color: white; text-decoration: none; font-weight: bold; border-radius: 8px; }
                .progress-container { width: 80%; height: 20px; background-color: #eee; border-radius: 10px; margin: 20px auto; overflow: hidden; }
                .progress-bar { height: 100%; background-color: #25d366; width: ${Math.min(100, Math.floor((taskInfo.sentMessages / taskInfo.totalMessages) * 100))}%; transition: width 0.5s; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Task Status</h1>
                <div class="task-id">Your Task ID: ${taskId}</div>
                <div class="status-item">Status: <span class="status-value">${taskInfo.isSending ? 'RUNNING' : taskInfo.stopRequested ? 'STOPPED' : 'COMPLETED'}</span></div>
                <div class="status-item">Target: <span class="status-value">${taskInfo.target}</span></div>
                <div class="status-item">Messages Sent: <span class="status-value">${taskInfo.sentMessages} / ${taskInfo.totalMessages}</span></div>
                <div class="progress-container"><div class="progress-bar"></div></div>
                <div class="status-item">Start Time: <span class="status-value">${taskInfo.startTime.toLocaleString()}</span></div>
                ${taskInfo.endTime ? `<div class="status-item">End Time: <span class="status-value">${taskInfo.endTime.toLocaleString()}</span></div>` : ''}
                ${taskInfo.error ? `<div class="status-item" style="color:red;">Error: ${taskInfo.error}</div>` : ''}
                <form action="/stop-task" method="POST" style="margin-top:20px;">
                    <input type="hidden" name="taskId" value="${taskId}">
                    <button type="submit" style="background-color: #dc3545;">Stop This Task</button>
                </form>
                <a href="/">Return to Home</a>
            </div>
        </body>
        </html>
    `);
});

app.post("/stop-task", async (req, res) => {
    const { taskId } = req.body;

    if (!activeTasks.has(taskId)) {
        return res.status(404).send(`<h2>Error: Invalid Task ID</h2><br><a href="/">Go Back</a>`);
    }

    try {
        const taskInfo = activeTasks.get(taskId);
        taskInfo.stopRequested = true;
        taskInfo.isSending = false;
        taskInfo.endTime = new Date();

        res.send(`
            <div style="text-align: center; padding: 20px;">
                <h2>Task ${taskId} stopped successfully</h2>
                <p>Messages sent: ${taskInfo.sentMessages}</p>
                <p>Start time: ${taskInfo.startTime.toLocaleString()}</p>
                <p>End time: ${taskInfo.endTime.toLocaleString()}</p>
                <br><a href="/">Go Back to Home</a>
            </div>
        `);
    } catch (error) {
        console.error(`Error stopping task ${taskId}:`, error);
        res.status(500).send(`<h2>Error stopping task</h2><p>${error.message}</p><br><a href="/">Go Back</a>`);
    }
});

// Updated route to fetch and list groups
app.get("/get-groups", async (req, res) => {
    const num = req.query.number.replace(/[^0-9]/g, "");

    let clientInfo;
    for (const [key, value] of activeClients.entries()) {
        if (value.number === num) {
            clientInfo = value;
            break;
        }
    }

    if (!clientInfo) {
        return res.status(400).json({ error: "No active session found for this number. Please make sure the number is correct and a session is linked." });
    }

    try {
        const { client: waClient } = clientInfo;
        const groupData = await waClient.groupFetchAllParticipating();
        const groups = Object.values(groupData).map(group => ({
            name: group.subject,
            uid: group.id.split('@')[0]
        }));
        
        res.json({ groups });
    } catch (error) {
        console.error("Error fetching groups:", error);
        res.status(500).json({ error: "Failed to fetch groups. Make sure you are connected." });
    }
});

process.on('SIGINT', () => {
    console.log('Shutting down gracefully...');
    activeClients.forEach(({ client }, sessionId) => {
        client.end();
        console.log(`Closed connection for Session ID: ${sessionId}`);
        activeUsers.delete(sessionId);
    });
    process.exit();
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
