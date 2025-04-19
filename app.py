import magic
import logging
from constants import NEXT_STAGE_COMMAND, PRESENTATION, UPLOAD_FOLDER
from presentation import create_report_buffer, generate_presentation_response
from prompts import get_system_prompt
from stages import STAGES_ARR as STAGES, StageInformation
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import os
import openai
import uuid
import shutil
from datetime import datetime
from sessions import cleanup_old_sessions, get_session_folder
from werkzeug.utils import secure_filename
from config import OPENAI_API_KEY, OPENAI_CONVERSATION_MODEL, validate_config
import base64
from flask import send_file
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

if 'FLASK_SECRET_KEY' not in os.environ:
    raise ValueError("FLASK_SECRET_KEY environment variable must be set")
app.secret_key = os.environ['FLASK_SECRET_KEY']

app.config["SESSION_TYPE"] = "filesystem"  # Store sessions on server filesystem
app.config["SESSION_PERMANENT"] = False
csrf = CSRFProtect(app)
Session(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["30 per minute"],
    storage_uri="memory://"
)

validate_config()

ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}
MAX_ATTACHMENTS_PER_SESSION = 20
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_user_info():
    return {
        "email": session.get("user_email"),
        "name": session.get("user_name"),
        "component": session.get("user_component")
    }

def handle_stage_change(new_stage_name):
    """
    Handle changing to a new stage, including:
    1. Update the session's current stage
    2. Add a stage description message to guide the AI
    3. Return the stage information
    """
    new_stage = None
    for stage in STAGES:
        if stage.name == new_stage_name:
            new_stage = stage
            break
    
    if not new_stage:
        return None
    
    session['current_stage'] = new_stage.name
    
    stage_description = new_stage.get_stage_description()
    if 'chat_history' not in session:
        raise ValueError("Chat history not initialized")
    
    chat_history = session['chat_history']
    chat_history.append({
        "sender": "user",
        "message": f"[STAGE CHANGE] We are now in the {new_stage.name} stage. {stage_description}",
        "visible": False
    })
    
    session['chat_history'] = chat_history
    return new_stage

@app.route('/api/get_stages', methods=['GET'])
def get_stages():
    stage_names = [stage.name for stage in STAGES]
    return jsonify({"stages": stage_names})

@app.route('/')
def index():
    user_info = get_user_info()
    if not all(user_info.values()):
        return redirect(url_for('initial_form'))
    return redirect(url_for('chat'))

@app.route('/initial_form.html', methods=['GET', 'POST'])
def initial_form():
    if request.method == 'POST':
        session['user_email'] = request.form.get('email')
        session['user_name'] = request.form.get('name')
        session['user_component'] = request.form.get('component')
        
        documentation_stage: StageInformation = STAGES[0]
        session['current_stage'] = documentation_stage.name
        session['chat_history'] = [
            {
                "sender": "user",
                "message": documentation_stage.get_stage_description(),
                "visible": False,
            },
            {
                "sender": "bot",
                "message": f"Welcome to the {documentation_stage.name} stage of our threat modeling process. To get started, I’ll need you to upload any relevant documentation about the service or system you want to analyze.",
                "visible": True
            },
        ]
        
        return redirect(url_for('chat'))

    return render_template('initial_form.html')

@app.route('/chat.html', methods=['GET', 'POST'])
def chat():
    user_info = get_user_info()
    if not all(user_info.values()):
        return redirect(url_for('initial_form'))
    
    if 'current_stage' not in session:
        session['current_stage'] = STAGES[0].name
    if 'chat_history' not in session:
        raise ValueError("Chat history not initialized")
    if 'attachments' not in session:
        session['attachments'] = []
    
    return render_template('chat.html', user_info=user_info, openai_model=OPENAI_CONVERSATION_MODEL)

# API Endpoints
@app.route('/api/history', methods=['GET'])
def get_history():
    if 'chat_history' not in session:
        raise ValueError("Chat history not initialized")
    
    visible_history = [msg for msg in session['chat_history'] if msg['visible']]
    return jsonify({"history": visible_history})

# Helper function to build messages for OpenAI API
def build_messages(instruction, attachments, chat_history):
    """
    Build the list of messages for the OpenAI API.
    
    Args:
        instruction (str): System prompt instruction.
        attachments (list): List of attachment dictionaries.
        chat_history (list): List of chat history messages.
    
    Returns:
        list: Messages formatted for the OpenAI API.
    """
    messages = [{"role": "system", "content": instruction}]
    
    # Add the first message from chat history (documentation stage message)
    if chat_history and len(chat_history) > 0:
        first_msg = chat_history[0]
        messages.append({
            "role": "user" if first_msg['sender'] == 'user' else "assistant", 
            "content": first_msg['message']
        })

    # Add attachment messages
    for attachment in attachments:
        file_path = attachment['path']
        filename = attachment['filename']
        file_ext = os.path.splitext(file_path)[1].lower()
        
        user_content = []
        # Handle images
        if file_ext in ['.png', '.jpg', '.jpeg']:
            with open(file_path, "rb") as file:
                base64_data = base64.b64encode(file.read()).decode("utf-8")
            mime_type = 'image/jpeg' if file_ext in ['.jpg', '.jpeg'] else 'image/png'
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{base64_data}"}
            })
        elif file_ext == '.pdf':
            with open(file_path, "rb") as file:
                base64_data = base64.b64encode(file.read()).decode("utf-8")
            user_content.append({
                "type": "file",
                "file": {
                    "filename": filename,
                    "file_data": f"data:application/pdf;base64,{base64_data}"
                }
            })

        user_content.append({
            "type": "text",
            "text": f"Here is an attachment I have for file {filename}"
        })
        
        messages.append({"role": "user", "content": user_content})
        messages.append({"role": "assistant", "content": "Thanks for the attachment"})
    
    if chat_history and len(chat_history) > 1:
        for msg in chat_history[1:]:
            if msg['sender'] == 'user':
                messages.append({"role": "user", "content": msg['message']})
            elif msg['sender'] == 'bot':
                messages.append({"role": "assistant", "content": msg['message']})
    
    return messages

@app.route('/api/chat', methods=['POST'])
@limiter.limit("30 per minute")
def chat_message():
    message = request.json.get('message')
    
    if 'chat_history' not in session:
        raise ValueError("Chat history not initialized")
    
    chat_history = session['chat_history']
    chat_history.append({
        "sender": "user",
        "message": message,
        "visible": True
    })
    
    instruction = get_system_prompt()
    attachments = session.get('attachments', [])
    messages = build_messages(instruction, attachments, chat_history)
    
    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_CONVERSATION_MODEL,
            messages=messages
        )
        bot_response = response.choices[0].message.content
    except Exception as e:
        bot_response = f"Sorry, I encountered an error"
    
    # Check if the bot response ends with NEXT_STAGE (case insensitive)
    should_advance = NEXT_STAGE_COMMAND in bot_response.upper()

    log_openai_conversation(messages, bot_response)
    chat_history.append({
        "sender": "bot",
        "message": bot_response,
        "visible": not should_advance
    })
    session['chat_history'] = chat_history

    if should_advance:
        current_stage_name = session['current_stage']
        current_index = next((i for i, stage in enumerate(STAGES) if stage.name == current_stage_name), -1)
        
        if current_index < len(STAGES) - 1:
            new_stage = handle_stage_change(STAGES[current_index + 1].name)
            if new_stage:
                return generate_ai_response_for_stage_change(new_stage)
        else:
            logging.warning("Requested to advance on the last stage, this should not happen!")
    
    return jsonify({"status": "success", "response": bot_response})

def log_openai_conversation(messages, response):
    """
    Log the full conversation with OpenAI, including system messages, user messages,
    and the model's response. For attachments, only show the first 20 characters of base64 data.
    
    Args:
        messages (list): The messages sent to the OpenAI API
        response: The response received from the OpenAI API
    """
    print("\n===== OPENAI CONVERSATION LOG =====")
    
    # Log input messages
    print("\n----- INPUT MESSAGES -----")
    for i, msg in enumerate(messages):
        role = msg["role"]
        print(f"\n[{i}] {role.upper()}:")
        
        # Handle different content formats
        if isinstance(msg["content"], str):
            print(f"  {msg['content']}")
        elif isinstance(msg["content"], list):
            for item in msg["content"]:
                if item["type"] == "text":
                    print(f"  TEXT: {item['text']}")
                elif item["type"] == "image_url":
                    base64_data = item["image_url"]["url"]
                    if base64_data.startswith("data:image"):
                        # Truncate base64 data
                        truncated = base64_data[:60] + "..." if len(base64_data) > 60 else base64_data
                        print(f"  IMAGE: {truncated}")
                    else:
                        print(f"  IMAGE URL: {base64_data}")
    
    # Log response
    print("\n----- OUTPUT RESPONSE -----")
    if hasattr(response, 'choices') and response.choices:
        print(f"MODEL: {response.model}")
        print(f"RESPONSE: {response.choices[0].message.content}")
    else:
        print(f"RESPONSE: {response}")
    
    print("\n===== END OF CONVERSATION LOG =====\n")

def generate_ai_response_for_stage_change(stage):
    """Generate an AI response when changing to a new stage"""
    if stage.name == PRESENTATION:
        bot_response = generate_presentation_response()
        session['chat_history'].append({
            "sender": "bot",
            "message": bot_response,
            "visible": True
        })
        # Set presentation mode flag
        session['presentation_mode'] = True
        return jsonify({
            "status": "success",
            "new_stage": stage.name,
            "response": bot_response,
            "presentation_mode": True
        })
    else:
        instruction = get_system_prompt()
        attachments = session.get('attachments', [])
        chat_history = session['chat_history']
        messages = build_messages(instruction, attachments, chat_history)
        try:
            response = openai.ChatCompletion.create(
                model=OPENAI_CONVERSATION_MODEL,
                messages=messages
            )
            bot_response = response.choices[0].message.content
            log_openai_conversation(messages, bot_response)
            chat_history.append({
                "sender": "bot",
                "message": bot_response,
                "visible": True
            })
            session['chat_history'] = chat_history
            return jsonify({
                "status": "success",
                "new_stage": stage.name,
                "response": bot_response
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error generating response"
            }), 500

# Add this import at the top
import magic

# Add this function
def validate_file_content(file_path, expected_ext):
    """Validate that the file content matches its extension"""
    mime = magic.Magic(mime=True)
    file_mime = mime.from_file(file_path)
    
    valid_mimes = {
        '.pdf': ['application/pdf'],
        '.png': ['image/png'],
        '.jpg': ['image/jpeg'],
        '.jpeg': ['image/jpeg']
    }
    
    return file_mime in valid_mimes.get(expected_ext, [])

def validate_file_extension(file_ext):
    """
    Validate that the file extension is safe:
    - Must start with a dot
    - Must be 1-5 characters long (including the dot)
    - Must only contain alphanumeric characters after the dot
    """
    if not file_ext.startswith('.'):
        return False
    if len(file_ext) < 2 or len(file_ext) > 5:  # Including the dot
        return False
    # Check that only alphanumeric chars follow the dot
    return bool(re.match(r'^\.[a-zA-Z0-9]+$', file_ext))

@app.route('/api/add_attachment', methods=['POST'])
@limiter.limit("30 per minute")
def add_attachment():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS or not validate_file_extension(file_ext):
        return jsonify({"error": "Invalid file type. Only PDFs and images are allowed."}), 400
    
    if request.content_length > MAX_ATTACHMENT_SIZE:
        return jsonify({"error": f"File too large. Maximum size is {MAX_ATTACHMENT_SIZE/1024/1024}MB"}), 400
    
    if 'attachments' not in session:
        session['attachments'] = []
    
    attachments = session['attachments']
    if len(attachments) >= MAX_ATTACHMENTS_PER_SESSION:
        return jsonify({"error": f"Maximum number of attachments ({MAX_ATTACHMENTS_PER_SESSION}) reached"}), 400
    
    filename = secure_filename(file.filename)
    attachment_id = str(uuid.uuid4())
    file_path = os.path.join(get_session_folder(), f"{attachment_id}{file_ext}")
    file.save(file_path)
    
    if not validate_file_content(file_path, file_ext):
        os.remove(file_path)  # Remove the invalid file
        return jsonify({"error": "File content doesn't match its extension"}), 400

    attachments.append({
        "id": attachment_id,
        "filename": filename,
        "path": file_path,
        "uploaded_at": datetime.now().isoformat()
    })
    session['attachments'] = attachments
    
    cleanup_old_sessions()
    return jsonify({"attachment_id": attachment_id, "filename": filename})

@app.route('/api/delete_attachment', methods=['POST'])
def delete_attachment():
    attachment_id = request.json.get('attachment_id')
    
    if 'attachments' not in session:
        return jsonify({"status": "error", "message": "No attachments found"}), 404
    
    attachments = session['attachments']
    attachment_to_delete = next((att for att in attachments if att['id'] == attachment_id), None)
    
    if attachment_to_delete:
        try:
            if os.path.exists(attachment_to_delete['path']):
                os.remove(attachment_to_delete['path'])
        except Exception as e:
            print(f"Error deleting file")
        
        attachments = [att for att in attachments if att['id'] != attachment_id]
        session['attachments'] = attachments
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Attachment not found"}), 404

@app.route('/api/get_attachments', methods=['GET'])
def get_attachments():
    if 'attachments' not in session:
        session['attachments'] = []
    
    safe_attachments = [{"id": att["id"], "filename": att["filename"]} for att in session['attachments']]
    return jsonify({"attachments": safe_attachments})

@app.route('/api/previous_stage', methods=['POST'])
def previous_stage():
    logging.info("Received request for previous stage")
    current_stage_name = session.get('current_stage', STAGES[0].name)
    current_index = next((i for i, stage in enumerate(STAGES) if stage.name == current_stage_name), -1)
    
    if current_index > 0:
        new_stage = handle_stage_change(STAGES[current_index - 1].name)
        if new_stage:
            return generate_ai_response_for_stage_change(new_stage)
    
    return jsonify({"status": "error", "message": "Already at first stage"}), 400

@app.route('/api/change_stage', methods=['POST'])
def change_stage():
    logging.info("Received request for change the stage")
    stage_name = request.json.get('stage')
    
    if any(stage.name == stage_name for stage in STAGES):
        new_stage = handle_stage_change(stage_name)
        if new_stage:
            return generate_ai_response_for_stage_change(new_stage)
    
    return jsonify({"status": "error", "message": "Invalid stage"}), 400

@app.route('/api/next_stage', methods=['POST'])
def next_stage():
    logging.info("Received request for next stage")
    current_stage_name = session.get('current_stage', STAGES[0].name)
    current_index = next((i for i, stage in enumerate(STAGES) if stage.name == current_stage_name), -1)
    
    if current_index < len(STAGES) - 1:
        new_stage = handle_stage_change(STAGES[current_index + 1].name)
        if new_stage:
            return generate_ai_response_for_stage_change(new_stage)
    
    return jsonify({"status": "error", "message": "Already at last stage"}), 400

@app.route('/api/clear_session', methods=['POST'])
def clear_session():
    try:
        session_folder = get_session_folder()
        if os.path.exists(session_folder):
            shutil.rmtree(session_folder)
    except Exception as e:
        print(f"Error clearing session files")
    
    session.clear()
    
    return jsonify({"status": "success"})

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        "openai_model": OPENAI_CONVERSATION_MODEL,
        "max_attachments": MAX_ATTACHMENTS_PER_SESSION,
        "max_attachment_size_mb": MAX_ATTACHMENT_SIZE / 1024 / 1024
    })

@app.route('/api/current_stage', methods=['GET'])
def get_current_stage():
    current_stage = session.get('current_stage', STAGES[0].name)
    presentation_mode = session.get('presentation_mode', False)
    return jsonify({
        "current_stage": current_stage,
        "presentation_mode": presentation_mode
    })

@app.route('/api/download_report', methods=['GET'])
def download_report():
    if session.get('current_stage') != PRESENTATION or not session.get('presentation_mode'):
        return jsonify({"error": "Report not available"}), 400
    
    # Get user info for filename
    user_info = get_user_info()
    servicename = user_info['component']
    timestamp = datetime.now().strftime("%Y_%m_%d")
    filename = f"{servicename}_{timestamp}_threat_model_report.pdf"
    
    # Create PDF in memory
    buffer = create_report_buffer()
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

@app.teardown_appcontext
def cleanup_on_shutdown(exception=None):
    cleanup_old_sessions()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
