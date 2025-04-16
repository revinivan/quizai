import os
import uuid
import json
from flask import Flask, flash, request, redirect, jsonify, make_response
from werkzeug.utils import secure_filename
from openai import RateLimitError

from process_file import satgpt
from extract_quiz import extract_quiz

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 300 * 1000 * 1000

def save_response(file_name, text):
    file = open(f"{file_name}_quiz_{uuid.uuid4()}.txt", "w")
    file.write(text)
    file.close()

def load_text(file_path):
    file = open(file_path, "r")
    content = file.read()
    return content

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_quiz_stub(uploaded_file):
    text_quiz = load_text("Biology IGCSE _ Coursebook.pdf_quiz_33fb2b52-cd51-4510-9e76-4edf322af619.txt")
    quiz = extract_quiz(text_quiz + f"/n Source document: {uploaded_file}")
    return jsonify(quiz.model_dump())

def create_quiz(uploaded_file):
    try:
        response = satgpt(uploaded_file)
        save_response(uploaded_file, response['result'])
        text_quiz = response['result']
        quiz = extract_quiz(text_quiz + f"/n Source document: {uploaded_file}")
        return jsonify(quiz.model_dump())
    except RateLimitError as e:
        app.logger.error(f"OpenAI request failed: {e}")
        return jsonify({
            "error": "The OpenAI account backing this app has run out of credits. "
                     "Add credits at https://platform.openai.com/settings/organization/billing/ and try again."
        }), 503
    

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    mimetype = request.mimetype
    if request.method == 'POST':

     # check if the post request has the file part
     if mimetype == 'application/x-www-form-urlencoded':
            data = request.get_data()
            filename = secure_filename('upload.pdf')
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(f"Uploaded file: {file_path}")
            with open(file_path, 'wb') as file:
                file.write(data)
            quiz = create_quiz(file_path)
            return quiz
     elif mimetype == 'multipart/form-data':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print(f"Uploaded file: {filename}")
            quiz = create_quiz(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return quiz
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''




#  To deploy, run: gcloud run deploy --source .
# gcloud run deploy --source . --add-volume="name=uploads-in-memory-volume,type=in-memory,size-limit=1024Mi" --add-volume-mount="volume=uploads-in-memory-volume,mount-path=/uploads"
# gcloud run services update satgpt --add-volume="name=uploads-in-memory-volume,type=in-memory,size-limit=1024Mi" --add-volume-mount="volume=uploads-in-memory-volume,mount-path=/uploads"
if __name__ == "__main__":

    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))