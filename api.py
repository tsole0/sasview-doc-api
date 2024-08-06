from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/post', methods=['POST'])
def test():
    # Access files
    uploaded_files = request.files
    json_str = request.form.get('json')
    
    if json_str:
        # Directly parse the JSON string
        try:
            data = json.loads(json_str)
            sasview_version = data.get('sasview_version')
            author = data.get('author')
            changes = data.get('changes')
            branches_exist = data.get('branches_exist')
            
            # Print or return the extracted data for debugging
            print(f"SasView Version: {sasview_version}")
            print(f"Author: {author}")
            print(f"Changes: {changes}")
            print(f"Branches Exist: {branches_exist}")
        except json.JSONDecodeError:
            return "Invalid JSON data", 400

    for filename in uploaded_files:
        print("Uploaded File:", filename)
    
    return '<p>testing</p>'

if __name__ == '__main__':
    app.run(debug=True)
