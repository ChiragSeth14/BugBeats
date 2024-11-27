import requests
import subprocess

def get_vscode_status():
    # Run VS Code's diagnostic command
    result = subprocess.run(["code", "--status"], stdout=subprocess.PIPE, text=True)
    return result.stdout

def trigger_playlist(endpoint):
    # Send a POST request to the Flask API
    url = f"http://127.0.0.1:5000/vscode/{endpoint}"
    response = requests.post(url)
    print(response.json())

def main():
    vscode_status = get_vscode_status()
    if "error" in vscode_status:
        print("Errors detected. Playing error playlist.")
        trigger_playlist("error")
    else:
        print("No errors detected. Playing success playlist.")
        trigger_playlist("success")

if __name__ == "__main__":
    main()

# import requests
# import subprocess
# from pathlib import Path

# # Flask API URL
# FLASK_API_URL = "http://127.0.0.1:5000/vscode/"

# def check_file_for_errors(filepath):
#     """Run pylint on a specific file and check for errors."""
#     try:
#         result = subprocess.run(["pylint", filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#         output = result.stdout + result.stderr
#         return output
#     except FileNotFoundError:
#         print("Pylint is not installed. Install it using `pip install pylint`.")
#         return ""

# def trigger_playlist(endpoint):
#     """Send a POST request to the Flask API."""
#     url = f"{FLASK_API_URL}{endpoint}"
#     response = requests.post(url)
#     print(response.json())

# def analyze_files_in_directory(directory):
#     """Analyze all Python files in the given directory for errors."""
#     has_errors = False
#     for filepath in Path(directory).rglob("*.py"):
#         print(f"Checking file: {filepath}")
#         lint_output = check_file_for_errors(str(filepath))
#         if "error" in lint_output.lower() or "E:" in lint_output:  # "E:" is the pylint error prefix
#             print(f"Errors found in {filepath}:\n{lint_output}")
#             has_errors = True
#         else:
#             print(f"No errors in {filepath}.")

#     return has_errors

# def get_vscode_status():
#     """Run VS Code's diagnostic command."""
#     try:
#         result = subprocess.run(["code", "--status"], stdout=subprocess.PIPE, text=True)
#         return result.stdout
#     except FileNotFoundError:
#         print("The `code` command is not available. Ensure VS Code is in your PATH.")
#         return ""

# def main():
#     directory = "."  # Analyze the current directory
#     print(f"Analyzing Python files in directory: {directory}")
#     has_errors = analyze_files_in_directory(directory)

#     if has_errors:
#         print("Errors detected. Playing error playlist.")
#         trigger_playlist("error")
#     else:
#         print("No errors detected. Playing success playlist.")
#         trigger_playlist("success")

# if __name__ == "__main__":
#     main()