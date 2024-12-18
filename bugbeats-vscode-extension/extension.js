const vscode = require('vscode');
const axios = require('axios');

// Flask API URL
const FLASK_API_URL = 'https://bug-beats-5b49ab3807c5.herokuapp.com/';

let userId = null; // Store the logged-in Spotify user ID
let outputChannel = null; // Output channel for messages and debugging

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('BugBeats extension activated.');

    // Initialize the output channel
    outputChannel = vscode.window.createOutputChannel("BugBeats");

    // Add a "Run and Check" button to the status bar
    const runButton = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    runButton.text = "$(play) Run and Check";
    runButton.command = 'bugbeats-vscode-extension.runAndCheck';
    runButton.tooltip = "Run the active file and check for errors";
    runButton.show();

    context.subscriptions.push(runButton);

    // Add a "Stop" button to the status bar
    const stopButton = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 99);
    stopButton.text = "$(primitive-square) Stop Playback";
    stopButton.command = 'bugbeats-vscode-extension.stopPlayback';
    stopButton.tooltip = "Stop Spotify playback";
    stopButton.show();

    context.subscriptions.push(stopButton);

    // Register the "Run and Check" command
    const runCommand = vscode.commands.registerCommand('bugbeats-vscode-extension.runAndCheck', async () => {
        console.log('Run and Check triggered.');

        if (!userId) {
            vscode.window.showErrorMessage("Please log in to Spotify first.");
            return;
        }

        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage("No active editor detected.");
            return;
        }

        const filePath = editor.document.uri.fsPath;
        const language = editor.document.languageId;

        console.log(`Executing file: ${filePath}, Language: ${language}`);

        try {
            // Execute the file locally
            const result = executeFile(filePath, language);
            console.log('Execution Result:', result);
            displayMessage(`File executed successfully:\n${result}`, "success");

            // Trigger the success track via Flask API
            await triggerPlaylist('vscode/success', userId);
        } catch (error) {
            console.error('Execution Error:', error.message);

            const errorCode = getErrorCode(error.message);
            console.log(`Detected Error Code: ${errorCode}`);
            displayMessage(`Error detected (${errorCode}):\n${error.message}`, "error");

            // Trigger an error-specific track via Flask API
            await triggerErrorTrack(errorCode, userId);
        }
    });

    context.subscriptions.push(runCommand);

    // Register the "Stop Playback" command
    const stopCommand = vscode.commands.registerCommand('bugbeats-vscode-extension.stopPlayback', async () => {
        console.log('Stop Playback triggered.');

        if (!userId) {
            vscode.window.showErrorMessage("Please log in to Spotify first.");
            return;
        }

        try {
            await stopPlayback(userId);
        } catch (error) {
            console.error('Failed to stop playback:', error.message);
        }
    });

    context.subscriptions.push(stopCommand);

    // Check login status on activation
    checkLoginStatus();
}

// Function to check login status and retrieve user ID
async function checkLoginStatus() {
    try {
        const response = await axios.get(`${FLASK_API_URL}vscode/check_login_status`);
        if (response.data.logged_in && response.data.user_id) {
            console.log("User already logged in:", response.data.user_id);
            userId = response.data.user_id; // Save the logged-in user ID
        } else {
            console.log("User not logged in. Opening Spotify login page...");
            vscode.env.openExternal(vscode.Uri.parse(`${FLASK_API_URL}login`));
        }
    } catch (error) {
        console.error("Failed to check login status:", error.message);
        vscode.window.showErrorMessage("Failed to check login status. Ensure the Flask server is running.");
    }
}

// Function to execute the active file based on its language
function executeFile(filePath, language) {
    const child_process = require('child_process');
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
        default:
            throw new Error(`Unsupported language: ${language}`);
    }

    return child_process.execSync(command, { encoding: 'utf-8' });
}

// Function to trigger a success playlist or error-specific track
async function triggerPlaylist(endpoint, userId) {
    try {
        const url = `${FLASK_API_URL}${endpoint}`;
        const response = await axios.post(url, { user_id: userId });
        console.log('Playlist Triggered:', response.data);
    } catch (error) {
        console.error('Failed to trigger playlist:', error.message);
    }
}

// Function to trigger error-specific track
async function triggerErrorTrack(errorCode, userId) {
    try {
        const url = `${FLASK_API_URL}vscode/error/${errorCode}`;
        const response = await axios.post(url, { user_id: userId });
        console.log('Error Track Triggered:', response.data);
    } catch (error) {
        console.error('Failed to trigger error track:', error.message);
    }
}

// Function to stop Spotify playback
async function stopPlayback(userId) {
    try {
        const url = `${FLASK_API_URL}vscode/stop`;
        await axios.post(url, { user_id: userId });
        console.log('Playback stopped successfully.');
    } catch (error) {
        console.error('Failed to stop playback:', error.message);
        throw error;
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

// Function to display messages in the output channel
function displayMessage(message, type) {
    if (outputChannel) {
        outputChannel.clear();
        outputChannel.appendLine(`[${type.toUpperCase()}]: ${message}`);
        outputChannel.show(true);
    }
}

module.exports = {
    activate,
    deactivate: () => {
        if (outputChannel) outputChannel.dispose();
    }
};
