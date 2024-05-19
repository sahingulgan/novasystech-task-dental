from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import subprocess
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = 'uploads'
SLICE_FOLDER = 'slices'
ALLOWED_EXTENSIONS = {'stl', 'obj'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(SLICE_FOLDER):
    os.makedirs(SLICE_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/slice', methods=['POST'])
def slice_model():
    if 'model' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['model']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(BASE_DIR,app.config['UPLOAD_FOLDER'], filename)
        print(filepath)
        file.save(filepath)

        resolution = request.form.get('resolution', 100)

        # Assuming PrusaSlicer is installed and in the PATH
        output_dir = os.path.join(SLICE_FOLDER, os.path.splitext(filename)[0])
        print(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(BASE_DIR, output_dir)
        print(output_path)
        # PrusaSlicer CLI command to slice the model
        command = f"prusa-slicer-console --sla --output {output_path} --layer-height {float(resolution) / 1000} {filepath}"
        print(command)
        try: 
            subprocess.run(command, check=True, shell=True)
        except FileNotFoundError:
            return jsonify({'error': 'PrusaSlicer executable not found. Ensure it is installed and in the PATH.'}), 500
        except subprocess.CalledProcessError as e:
            return jsonify({'error': f'Slicing failed: {str(e)}'}), 500
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

        return jsonify({'url': f'/slices/{os.path.splitext(filename)[0]}/slice.png'})

@app.route('/slices/<path:filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(SLICE_FOLDER, filename)

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
