from datetime import datetime
import os
import shutil
import uuid
from flask import session

from constants import UPLOAD_FOLDER

def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def get_session_folder():
    session_id = get_session_id()
    folder = os.path.join(UPLOAD_FOLDER, session_id)
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def cleanup_old_sessions(max_age_hours=24):
    try:
        now = datetime.now()
        for session_id in os.listdir(UPLOAD_FOLDER):
            session_path = os.path.join(UPLOAD_FOLDER, session_id)
            if os.path.isdir(session_path):
                # Check folder modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(session_path))
                age_hours = (now - mtime).total_seconds() / 3600
                if age_hours > max_age_hours:
                    shutil.rmtree(session_path)
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
