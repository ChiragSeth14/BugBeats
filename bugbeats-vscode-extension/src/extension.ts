import * as vscode from 'vscode';
import axios from 'axios'; // For making HTTP requests

// Flask API URL
const FLASK_API_URL = 'http://127.0.0.1:5000/vscode/';

export function activate(context: vscode.ExtensionContext) {
    console.log('BugBeats extension is now active.');

    // Subscribe to diagnostics changes
    vscode.languages.onDidChangeDiagnostics(handleDiagnostics);

    // Handle file save event
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((document) => {
            handleDiagnostics();
        })
    );
}

//Function to handle diagnostics (errors/warnings)
async function handleDiagnostics() {
    const editor = vscode.window.activeTextEditor;

    if (!editor) {
        console.log('No active editor detected.');
        return;
    }

    // Get the current file's diagnostics
    const diagnostics = vscode.languages.getDiagnostics(editor.document.uri);

    // Check for errors
    const hasErrors = diagnostics.some((diagnostic) =>
        diagnostic.severity === vscode.DiagnosticSeverity.Error
    );

    if (hasErrors) {
        console.log('Errors detected. Playing error playlist.');
        await triggerPlaylist('error');
    } else {
        console.log('No errors detected. Playing success playlist.');
        await triggerPlaylist('success');
    }
}

// Function to trigger the appropriate playlist via Flask API
async function triggerPlaylist(endpoint: string) {
    try {
        const response = await axios.post(`${FLASK_API_URL}${endpoint}`);
        vscode.window.showInformationMessage(response.data.message || 'Playlist triggered.');
    } catch (error) {
		if (error instanceof Error) {
			console.error('Failed to trigger playlist:', error.message);
		} else {
			console.error('Failed to trigger playlist: An unknown error occurred.');
		}
		
        vscode.window.showErrorMessage('Failed to connect to the Flask server.');
    }
}

// Deactivate the extension
export function deactivate() {
    console.log('BugBeats extension is now deactivated.');
}
