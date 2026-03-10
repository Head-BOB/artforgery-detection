import os

from flask import Flask, request, jsonify

from werkzeug.utils import secure_filename

app = Flask(__name__)


UPLOAD_FOLDER = 'uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/analyze', methods=['POST'])
def analyze_file():
    """
    This function handles the file upload and returns a dummy analysis response.
    """
    
    if 'file' in request.files:
        uploaded_file = request.files['file']
    elif 'image' in request.files:
        uploaded_file = request.files['image']
    else:
        return jsonify({"error": "No file attached to the request. Please send a 'file' or 'image'."}), 400

    if uploaded_file.filename == '':
        return jsonify({"error": "No file selected. File name is empty."}), 400

    if uploaded_file:
        safe_filename = secure_filename(uploaded_file.filename)
        
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        uploaded_file.save(save_path)
        
        return jsonify({
            "status": "success", 
            "authenticity_score": 88.5, 
            "message": "Dummy response active"
        }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)