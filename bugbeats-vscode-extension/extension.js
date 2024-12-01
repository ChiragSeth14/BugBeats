// const vscode = require('vscode');
// const axios = require('axios');
// const child_process = require('child_process'); // For running Python scripts

// // Flask API URL
// const FLASK_API_URL = 'http://127.0.0.1:5000/vscode/';

// /**
//  * @param {vscode.ExtensionContext} context
//  */
// function activate(context) {
//     console.log('BugBeats extension activated.');
//     vscode.window.showInformationMessage('BugBeats extension activated.');

//     // Add a status bar button
//     const runButton = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
//     runButton.text = "$(play) Run and Check"; // Play icon with text
//     runButton.command = 'bugbeats-vscode-extension.runAndCheck';
//     runButton.tooltip = "Run the active Python file and check for errors";
//     runButton.show();

//     // Add the button to subscriptions
//     context.subscriptions.push(runButton);

//     // Register the command for running the active file
//     const runCommand = vscode.commands.registerCommand('bugbeats-vscode-extension.runAndCheck', async () => {
//         console.log('Run and check command triggered.');
//         vscode.window.showInformationMessage('Running file and checking for errors.');

//         // Get the active editor
//         const editor = vscode.window.activeTextEditor;

//         if (!editor) {
//             vscode.window.showErrorMessage('No active editor detected.');
//             return;
//         }

//         const filePath = editor.document.uri.fsPath;
//         const language = editor.document.languageId;

//         console.log(`Active file: ${filePath}`);
//         console.log(`Language of the active file: ${language}`);

//         // Ensure the file is a Python file
//         if (language !== 'python') {
//             vscode.window.showErrorMessage('The active file is not a Python file.');
//             return;
//         }

//         // Run the file and capture output
//         try {
//             const result = child_process.execSync(`python "${filePath}"`, { encoding: 'utf-8' });
//             console.log('Python Output:', result);
//             vscode.window.showInformationMessage('File ran successfully. Playing success track.');
//             await triggerPlaylist('success');
//         } catch (error) {
//             console.error('Python Error:', error.stderr || error.message);

//             // Extract error message
//             const errorMessage = error.stderr || error.message;
//             console.log(`Error message: ${errorMessage}`);

//             // Map error types to specific codes
//             const errorCode = getErrorCode(errorMessage);
//             console.log(`Mapped error code: ${errorCode}`);

//             vscode.window.showErrorMessage(`Error detected: ${errorMessage}. Playing error-specific track.`);
//             await triggerErrorTrack(errorCode);
//         }
//     });

//     // Add the command to subscriptions
//     context.subscriptions.push(runCommand);
// }

// // Function to trigger success playlist or error-specific track via Flask API
// async function triggerPlaylist(endpoint) {
//     try {
//         const url = `${FLASK_API_URL}${endpoint}`;
//         console.log(`Triggering playlist or track for endpoint: ${url}`);
//         const response = await axios.post(url);
//         console.log('Flask API Response:', response.data);
//         vscode.window.showInformationMessage(response.data.message || 'Playlist or track triggered.');
//     } catch (error) {
//         if (axios.isAxiosError(error)) {
//             console.error(`Failed to trigger playlist or track: ${error.response?.status} - ${error.response?.statusText}`);
//         } else {
//             console.error('Failed to trigger playlist or track:', error.message);
//         }
//         vscode.window.showErrorMessage('Failed to connect to the Flask server.');
//     }
// }

// // Function to trigger error-specific track via Flask API
// async function triggerErrorTrack(errorCode) {
//     try {
//         const url = `${FLASK_API_URL}error/${errorCode}`;
//         console.log(`Triggering error track for code: ${errorCode}`);
//         const response = await axios.post(url);
//         console.log('Flask API Response:', response.data);
//         vscode.window.showInformationMessage(response.data.message || 'Error-specific track triggered.');
//     } catch (error) {
//         if (axios.isAxiosError(error)) {
//             console.error(`Failed to trigger error-specific track: ${error.response?.status} - ${error.response?.statusText}`);
//         } else {
//             console.error('Failed to trigger error-specific track:', error.message);
//         }
//         vscode.window.showErrorMessage('Failed to connect to the Flask server.');
//     }
// }

// // Function to map error messages to error codes
// function getErrorCode(errorMessage) {
//     if (errorMessage.includes('SyntaxError')) return 'syntax_error';
//     if (errorMessage.includes('NameError')) return 'name_error';
//     if (errorMessage.includes('TypeError')) return 'type_error';
//     if (errorMessage.includes('IndexError')) return 'index_error';
//     if (errorMessage.includes('KeyError')) return 'key_error';
//     return 'unknown_error';
// }

// // Deactivate the extension
// function deactivate() {
//     console.log('BugBeats extension deactivated.');
// }

// module.exports = {
//     activate,
//     deactivate
// };

const vscode = require('vscode');
const axios = require('axios');
const child_process = require('child_process'); // For running Python scripts

// Flask API URL
const FLASK_API_URL = 'http://127.0.0.1:5000/vscode/';

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('BugBeats extension activated.');
    vscode.window.showInformationMessage('BugBeats extension activated.');

    // Add a status bar button for "Run and Check"
    const runButton = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    runButton.text = "$(play) Run and Check"; // Play icon with text
    runButton.command = 'bugbeats-vscode-extension.runAndCheck';
    runButton.tooltip = "Run the active Python file and check for errors";
    runButton.show();

    // Add the button to subscriptions
    context.subscriptions.push(runButton);

    // Add a status bar button for "Stop"
    const stopButton = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 99);
    stopButton.text = "$(primitive-square) Stop Playback"; // Stop icon with text
    stopButton.command = 'bugbeats-vscode-extension.stopPlayback';
    stopButton.tooltip = "Stop Spotify playback";
    stopButton.show();

    // Add the button to subscriptions
    context.subscriptions.push(stopButton);

    // Register the command for running the active file
    const runCommand = vscode.commands.registerCommand('bugbeats-vscode-extension.runAndCheck', async () => {
        console.log('Run and check command triggered.');
        vscode.window.showInformationMessage('Running file and checking for errors.');

        // Get the active editor
        const editor = vscode.window.activeTextEditor;

        if (!editor) {
            vscode.window.showErrorMessage('No active editor detected.');
            return;
        }

        const filePath = editor.document.uri.fsPath;
        const language = editor.document.languageId;

        console.log(`Active file: ${filePath}`);
        console.log(`Language of the active file: ${language}`);

        // Ensure the file is a Python file
        if (language !== 'python') {
            vscode.window.showErrorMessage('The active file is not a Python file.');
            return;
        }

        // Run the file and capture output
        try {
            const result = child_process.execSync(`python "${filePath}"`, { encoding: 'utf-8' });
            console.log('Python Output:', result);
            vscode.window.showInformationMessage('File ran successfully. Playing success track.');
            await triggerPlaylist('success');
        } catch (error) {
            console.error('Python Error:', error.stderr || error.message);

            // Extract error message
            const errorMessage = error.stderr || error.message;
            console.log(`Error message: ${errorMessage}`);

            // Map error types to specific codes
            const errorCode = getErrorCode(errorMessage);
            console.log(`Mapped error code: ${errorCode}`);

            vscode.window.showErrorMessage(`Error detected: ${errorMessage}. Playing error-specific track.`);
            await triggerErrorTrack(errorCode);
        }
    });

    context.subscriptions.push(runCommand);

    // Register the command for stopping playback
    const stopCommand = vscode.commands.registerCommand('bugbeats-vscode-extension.stopPlayback', async () => {
        console.log('Stop playback command triggered.');
        vscode.window.showInformationMessage('Stopping Spotify playback...');
        await stopPlayback();
    });

    context.subscriptions.push(stopCommand);
}

// Function to stop Spotify playback via Flask API
async function stopPlayback() {
    try {
        const url = `${FLASK_API_URL}stop`;
        console.log(`Sending stop playback request to: ${url}`);
        const response = await axios.post(url);
        console.log('Flask API Response:', response.data);
        vscode.window.showInformationMessage(response.data.message || 'Playback stopped.');
    } catch (error) {
        if (axios.isAxiosError(error)) {
            console.error(`Failed to stop playback: ${error.response?.status} - ${error.response?.statusText}`);
        } else {
            console.error('Failed to stop playback:', error.message);
        }
        vscode.window.showErrorMessage('Failed to stop Spotify playback.');
    }
}

// Function to trigger success playlist or error-specific track via Flask API
async function triggerPlaylist(endpoint) {
    try {
        const url = `${FLASK_API_URL}${endpoint}`;
        console.log(`Triggering playlist or track for endpoint: ${url}`);
        const response = await axios.post(url);
        console.log('Flask API Response:', response.data);
        vscode.window.showInformationMessage(response.data.message || 'Playlist or track triggered.');
    } catch (error) {
        if (axios.isAxiosError(error)) {
            console.error(`Failed to trigger playlist or track: ${error.response?.status} - ${error.response?.statusText}`);
        } else {
            console.error('Failed to trigger playlist or track:', error.message);
        }
        vscode.window.showErrorMessage('Failed to connect to the Flask server.');
    }
}

// Function to trigger error-specific track via Flask API
async function triggerErrorTrack(errorCode) {
    try {
        const url = `${FLASK_API_URL}error/${errorCode}`;
        console.log(`Triggering error track for code: ${errorCode}`);
        const response = await axios.post(url);
        console.log('Flask API Response:', response.data);
        vscode.window.showInformationMessage(response.data.message || 'Error-specific track triggered.');
    } catch (error) {
        if (axios.isAxiosError(error)) {
            console.error(`Failed to trigger error-specific track: ${error.response?.status} - ${error.response?.statusText}`);
        } else {
            console.error('Failed to trigger error-specific track:', error.message);
        }
        vscode.window.showErrorMessage('Failed to connect to the Flask server.');
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
    console.log('BugBeats extension deactivated.');
}

module.exports = {
    activate,
    deactivate
};


