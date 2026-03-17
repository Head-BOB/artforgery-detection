import os
import time
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# --- CONFIGURATION ---
MOCK_MODE = False  # Set to False to use the real PyTorch AI!

if not MOCK_MODE:
    # Import your custom AI pipeline scripts
    from model_inference import load_engine, analyze_painting
    from preprocessing import process_image
    from xaiengine import generate_heatmap_base64 
    
    # Load the AI brain into the CPU memory exactly ONE time when the server boots.
    # This prevents the server from crashing by trying to load a 300MB model on every single request.
    print("Loading Triple-Branch Engine into Memory...")
    # MAKE SURE YOUR .pth FILE IS INSIDE A FOLDER NAMED 'models' NEXT TO THIS SCRIPT!
    engine = load_engine("models/ArtForgeryEngine_V2_Advanced.pth")
    print("Engine Ready & Waiting for Java UI!")

app = Flask(__name__)

# Configure where the server will temporarily save the uploaded images from Java
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/analyze', methods=['POST'])
def analyze():
    # 1. CATCH THE IMAGE FROM JAVA
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided in the request"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Empty filename submitted"}), 400

    if file:
        # Secure the filename and save it locally so OpenCV/PIL can read it
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f"\n--- New Analysis Request: {filename} ---")

        # 2. DEVELOPMENT MOCK RESPONSE (Safety Fallback)
        if MOCK_MODE:
            print("MOCK MODE ACTIVE: Simulating AI analysis...")
            time.sleep(2) # Fake a 2-second processing delay
            
            # A tiny 1x1 pixel blank image encoded in base64 just so Java doesn't crash
            dummy_base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
            
            os.remove(filepath) # Clean up the folder
            
            return jsonify({
                "final_score": 88.5,
                "cnn_confidence": 92.0,
                "vit_confidence": 85.0,
                "hybrid_confidence": 89.0,
                "heatmap_image": dummy_base64_image,
                "message": "SUCCESS: Server caught the image! (Mock Data)"
            }), 200

        # 3. THE REAL AI INFERENCE PIPELINE
        else:
            try:
                # Step A: Chop the image into multi-scale tensors (128, 256, 512)
                print("Step A: Extracting multi-scale patches & edges...")
                image_tensors = process_image(filepath)
                
                # Step B: Pass the massive batch of patches through the Triple-Branch Engine
                print("Step B: Running Deep Learning Inference...")
                scores = analyze_painting(engine, image_tensors)
                
                # Step C: Generate the Explainable AI visual heatmap
                print("Step C: Generating XAI Heatmap...")
                heatmap_b64 = generate_heatmap_base64(filepath, engine)
                
                # Step D: Nuke the temporary image file to save hard drive space
                os.remove(filepath)
                print("Analysis Complete! Sending JSON response back to Java.")

                # Return the exact JSON structure your Java UI is expecting
                return jsonify({
                    "final_score": scores["final_score"],
                    "cnn_confidence": scores["cnn_confidence"],
                    "vit_confidence": scores["vit_confidence"],
                    "hybrid_confidence": scores["hybrid_confidence"],
                    "heatmap_image": heatmap_b64,
                    "message": "SUCCESS: AI Analysis Complete"
                }), 200
                
            except Exception as e:
                print(f"CRITICAL ERROR during AI Analysis: {str(e)}")
                # If it crashes, delete the image so it doesn't permanently clog your uploads folder
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("API Server is ONLINE")
    print("Listening for Java UI requests on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)