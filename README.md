# 🚀 Galactic WhatsApp Sender Protocol 🚀

Welcome, operator, to the **Galactic WhatsApp Sender Protocol**—your command center for automated communications. This advanced Node.js application allows you to send scheduled messages to individual contacts or entire groups from a sleek, futuristic web interface.

This protocol is built using cutting-edge technologies like **Baileys**, **Express**, and a custom-designed user interface to ensure a seamless and powerful user experience.

---

### ✨ Features That Will Blow Your Mind

* **⚡️ Pairing Code Authentication:** No QR codes needed! Simply enter your WhatsApp number to generate a unique pairing code and link your device.
* **🌌 Futuristic Web UI:** A custom-built, retro-cyberpunk interface that makes you feel like you're operating a high-tech console from the year 2050.
* **🤖 Automated Message Blasting:** Upload a `.txt` file with your messages, set a custom delay, and watch the system transmit your payload to a target number or group.
* **🔭 Group UID Retrieval:** Select the "group" option and the system will automatically scan your paired account and list all your active group IDs, so you don't have to look for them manually.
* **📊 Real-time Task Status:** Track the progress of your message transmissions with a dedicated status page, showing sent messages, completion percentage, and any mission-critical errors.

---

### ⚙️ System Requirements

To run this protocol on your local machine, you'll need the following components installed:

* **Node.js**: `v16` or higher
* **npm** (Node Package Manager)

---

### 📥 Installation and Setup

Follow these simple steps to bring the system online:

1.  **Clone the Repository:**
    ```bash
    git clone [Your Repository URL Here]
    cd whatsapp-sender
    ```
2.  **Install Dependencies:**
    ```bash
    npm install
    ```
3.  **Initiate the Server:**
    ```bash
    npm start
    ```
    Your command line should display a confirmation message:
    ```
    server running on http://localhost:5000
    futuristic whatsapp sender protocol online. Port: 5000
    ```
4.  **Access the Console:**
    Open your browser and navigate to `http://localhost:5000`.

---

### 🕹️ How to Use the Protocol

1.  **Generate a Pairing Code:**
    * Enter your WhatsApp number (with country code, e.g., `91xxxxxxxxxx`) in the "Initiate Pairing Sequence" section.
    * Click "Generate Pairing Code."
    * A unique code will appear. Follow the on-screen instructions on your phone to link your device.
2.  **Retrieve Group UIDs (Optional):**
    * Once paired, select "group UID" in the "Transmit Message Payload" section. A new box will appear.
    * Enter your paired WhatsApp number and click "Fetch My Groups." The UIDs and names of your groups will be displayed below.
3.  **Transmit Messages:**
    * Fill out the "Transmit Message Payload" form.
    * **Target Type:** Choose "Target Number" or "Group UID."
    * **Target:** Enter the number or paste the group UID.
    * **Message File:** Upload a `.txt` file containing your messages (one message per line).
    * **Delay:** Set the delay in seconds between each message.
    * Click "Start Sending Messages" to begin the transmission.
4.  **Monitor Your Mission:**
    * You will be redirected to a **Task Status Interface** where you can track the mission's progress in real-time.
    * To stop a running task, use the "Task Control Interface" on the main page with its unique task ID.

**Note:** The system will create `temp` and `uploads` directories in your project folder to store session data and message files. Do not delete them while the server is running.
