const vscode = require('vscode');
const axios = require('axios');
const child_process = require('child_process'); // For running commands

// Flask API URL
const FLASK_API_URL = 'https://bug-beats-5b49ab3807c5.herokuapp.com/';

let outputChannel = null; // Declare a global output channel

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('BugBeats extension activated.');

    // Initialize the output channel
    outputChannel = vscode.window.createOutputChannel("BugBeats");

    // Add a status bar button for "Run and Check"
    const runButton = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    runButton.text = "$(play) Run and Check"; // Play icon with text
    runButton.command = 'bugbeats-vscode-extension.runAndCheck';
    runButton.tooltip = "Run the active file and check for errors";
    runButton.show();

    context.subscriptions.push(runButton);

    // Add a status bar button for "Stop"
    const stopButton = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 99);
    stopButton.text = "$(primitive-square) Stop Playback"; // Stop icon with text
    stopButton.command = 'bugbeats-vscode-extension.stopPlayback';
    stopButton.tooltip = "Stop Spotify playback";
    stopButton.show();

    context.subscriptions.push(stopButton);

    // Register the command for running the active file
    const runCommand = vscode.commands.registerCommand('bugbeats-vscode-extension.runAndCheck', async () => {
        console.log('Run and check command triggered.');

        const editor = vscode.window.activeTextEditor;

        if (!editor) {
            vscode.window.showErrorMessage('No active editor detected.');
            return;
        }

        const filePath = editor.document.uri.fsPath;
        const language = editor.document.languageId;

        console.log(`Active file: ${filePath}`);
        console.log(`Language: ${language}`);

        try {
            // Execute the file based on its language
            const result = executeFile(filePath, language);
            console.log('Execution Output:', result);
            displayMessage(`File executed successfully:\n${result}`, "success");
            await triggerPlaylist('vscode/success');
        } catch (error) {
            console.error('Execution Error:', error.message);

            const errorCode = getErrorCode(error.message);
            console.log(`Error Code: ${errorCode}`);
            displayMessage(`Error detected (${errorCode}):\n${error.message}`, "error");
            await triggerErrorTrack(errorCode);
        }
    });

    context.subscriptions.push(runCommand);

    // Register the command for stopping playback
    const stopCommand = vscode.commands.registerCommand('bugbeats-vscode-extension.stopPlayback', async () => {
        console.log('Stop playback command triggered.');
        await stopPlayback();
    });

    context.subscriptions.push(stopCommand);

    // Auto-login and auto-refresh tokens on startup
    checkLoginStatusAndRefreshTokenIfNeeded();
}

// Function to check login status and refresh token
async function checkLoginStatusAndRefreshTokenIfNeeded() {
    try {
        const response = await axios.get(`${FLASK_API_URL}vscode/check_login_status`);
        if (!response.data.logged_in) {
            console.log("User not logged in. Opening Spotify login page...");
            vscode.env.openExternal(vscode.Uri.parse(`${FLASK_API_URL}login`));
        } else {
            console.log("User is already logged in. Refreshing token...");
            await axios.post(`${FLASK_API_URL}vscode/refresh_token`);
        }
    } catch (error) {
        console.error("Failed to check login status or refresh token:", error.message);
    }
}

// Function to execute the file based on its language
function executeFile(filePath, language) {
    let command;

    switch (language) {
        case 'python':
            command = `python "${filePath}"`;
            break;
        case 'javascript':
        case 'typescript':
            command = `node "${filePath}"`;
            break;
        case 'java':
            command = `javac "${filePath}" && java "${filePath.replace('.java', '')}"`;
            break;
        case 'cpp':
            command = `g++ "${filePath}" -o "${filePath.replace(/\.[^/.]+$/, '')}" && "${filePath.replace(/\.[^/.]+$/, '')}"`;
            break;
        case 'c':
            command = `gcc "${filePath}" -o "${filePath.replace(/\.[^/.]+$/, '')}" && "${filePath.replace(/\.[^/.]+$/, '')}"`;
            break;
        case 'bash':
            command = `bash "${filePath}"`;
            break;
        case 'ruby':
            command = `ruby "${filePath}"`;
            break;
        case 'php':
            command = `php "${filePath}"`;
            break;
        case 'go':
            command = `go run "${filePath}"`;
            break;
        default:
            throw new Error(`Unsupported language: ${language}`);
    }

    return child_process.execSync(command, { encoding: 'utf-8' });
}

// Function to display persistent messages
function displayMessage(message, type) {
    if (outputChannel) {
        outputChannel.clear(); // Clear previous messages
        outputChannel.appendLine(`[${type.toUpperCase()}]: ${message}`);
        outputChannel.show(true); // Show the output channel
    }
}

// Function to stop Spotify playback via Flask API
async function stopPlayback() {
    try {
        const url = `${FLASK_API_URL}vscode/stop`;
        console.log(`Sending stop playback request to: ${url}`);
        await axios.post(url);
        console.log('Playback stopped successfully.');
    } catch (error) {
        console.error('Failed to stop playback:', error.message);
    }
}

// Function to trigger success playlist or error-specific track via Flask API
async function triggerPlaylist(endpoint) {
    try {
        const url = `${FLASK_API_URL}${endpoint}`;
        console.log(`Triggering playlist or track for endpoint: ${url}`);
        await axios.post(url);
    } catch (error) {
        console.error('Failed to trigger playlist or track:', error.message);
        displayMessage("Please make sure your Spotify device is active.", "error");
    }
}

// Function to trigger error-specific track via Flask API
async function triggerErrorTrack(errorCode) {
    try {
        const url = `${FLASK_API_URL}vscode/error/${errorCode}`;
        console.log(`Triggering error track for code: ${errorCode}`);
        await axios.post(url);
    } catch (error) {
        console.error('Failed to trigger error-specific track:', error.message);
        displayMessage("Please make sure your Spotify device is active.", "error");
    }
}

// Function to map error messages to error codes
function getErrorCode(errorMessage) {
    if (errorMessage.includes('SyntaxError')) return 'syntax_error';
    if (errorMessage.includes('NameError')) return 'name_error';
    if (errorMessage.includes('TypeError')) return 'type_error';
    if (errorMessage.includes('IndexError')) return 'index_error';
    if (errorMessage.includes('KeyError')) return 'key_error';
    return 'unknown_error';
}

// Deactivate the extension
function deactivate() {
    if (outputChannel) {
        outputChannel.dispose(); // Clean up the output channel
    }
    console.log('BugBeats extension deactivated.');
}

module.exports = {
    activate,
    deactivate
};
