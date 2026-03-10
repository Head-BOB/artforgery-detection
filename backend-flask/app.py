# Import the 'os' module to interact with the operating system (like creating folders and file paths)
import os

# Import necessary modules from the Flask framework
# Flask: The core class to create our web application
# request: Helps us read data (like files) sent by the user/frontend
# jsonify: Converts Python dictionaries into proper JSON format for the response
from flask import Flask, request, jsonify

# Import secure_filename to sanitize file names sent by users
# This prevents malicious users from uploading files named something like "../../../etc/passwd"
from werkzeug.utils import secure_filename

# 1. Set up the basic Flask application
app = Flask(__name__)

# Define the name of the folder where we want to save uploaded files
UPLOAD_FOLDER = 'uploads'

# Configure our Flask app to know about this folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 2. Create the 'uploads' folder if it does not already exist
# os.makedirs creates the directory, and exist_ok=True prevents an error if it's already there
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 3. Create a single API route: '/analyze' that only accepts POST requests
@app.route('/analyze', methods=['POST'])
def analyze_file():
    """
    This function handles the file upload and returns a dummy analysis response.
    """
    
    # 4. Look for a file attached to the request
    # We will check if the frontend sent the file under the key 'file' or 'image'
    if 'file' in request.files:
        uploaded_file = request.files['file']
    elif 'image' in request.files:
        uploaded_file = request.files['image']
    else:
        # If neither key is found in the request, return a JSON error with a 400 Bad Request status
        return jsonify({"error": "No file attached to the request. Please send a 'file' or 'image'."}), 400

    # 5. Check if the file name is empty (this happens if the user submitted the form without picking a file)
    if uploaded_file.filename == '':
        return jsonify({"error": "No file selected. File name is empty."}), 400

    # 6. If we successfully received a file, sanitize its name and save it
    if uploaded_file:
        # Sanitize the filename to ensure it's safe to save to our computer
        safe_filename = secure_filename(uploaded_file.filename)
        
        # Create the full file path by joining the 'uploads' folder path and the safe filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        # Save the file to the constructed path
        uploaded_file.save(save_path)
        
        # 7. After saving, return the exact dummy JSON response required
        return jsonify({
            "status": "success", 
            "authenticity_score": 88.5, 
            "message": "Dummy response active"
        }), 200

# 8. Include the code to run the app
if __name__ == '__main__':
    # Run the Flask app in debug mode on port 5000
    # debug=True automatically restarts the server if you change the code and provides helpful error logs
    app.run(debug=True, port=5000)