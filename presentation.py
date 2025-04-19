import os
from config import OPENAI_REPORTING_MODEL
from prompts import generate_presentation_findings
import openai
from flask import session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet
import io
from pdf2image import convert_from_path
import tempfile
from PIL import Image as PILImage

def generate_presentation_response():
    # Build conversation string from visible chat history, excluding attachments
    conversation = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in session['chat_history'] if msg['visible']])
    prompt = generate_presentation_findings(conversation)
    messages = [{"role": "user", "content": prompt}]
    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_REPORTING_MODEL,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating presentation: {str(e)}"

def create_report_buffer():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    temp_files = []

    try:
        # Table of Contents
        story.append(Paragraph("Table of Contents", styles['Heading1']))
        story.append(Paragraph("1. Session Details", styles['Normal']))
        story.append(Paragraph("2. Findings and Recommendations", styles['Normal']))
        story.append(Paragraph("3. Conversation Transcript", styles['Normal']))
        story.append(Paragraph("4. User-Provided Documentation", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(PageBreak())

        # Helper function for section titles - modified to not add page break
        def add_section_title(title):
            story.append(Paragraph(title, styles['Heading1']))
            story.append(Spacer(1, 12))  # Add some space after the title instead of a page break

        # Session Details
        add_section_title("Session Details")
        # Get user information from session
        user_email = session.get('user_email', 'Not provided')
        user_name = session.get('user_name', 'Not provided')
        service_name = session.get('user_component', 'Not provided')
        
        # Add user information to the report
        story.append(Paragraph(f"<b>User Email:</b> {user_email}", styles['Normal']))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>User Name:</b> {user_name}", styles['Normal']))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Service Name:</b> {service_name}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(PageBreak())

        add_section_title("Findings and Recommendations")
        presentation_response = next(
            (msg['message'] for msg in session['chat_history'][::-1] if msg['sender'] == 'bot' and msg['visible']),
            "No findings available"
        )
        for line in presentation_response.split('\n'):
            if line.strip():  # Only add non-empty lines
                story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 6)) # Add a small space between paragraphs
        story.append(Spacer(1, 12))
        story.append(PageBreak())

        add_section_title("Conversation Transcript")
        for i, msg in enumerate(session['chat_history']):
            if msg['visible']:
                story.append(Paragraph(f"<b>{msg['sender'].capitalize()}:</b>", styles['Normal']))
                story.append(Spacer(1, 6))
                
                # Split the message by newlines and add each line as a separate paragraph
                for line in msg['message'].split('\n'):
                    if line.strip():  # Only add non-empty lines
                        story.append(Paragraph(line, styles['Normal']))
                        story.append(Spacer(1, 3))  # Small space between lines
                
                story.append(Spacer(1, 12))
                if i < len(session['chat_history']) - 1:
                    story.append(HRFlowable(width="90%", thickness=1, lineCap='round', 
                                            color="#D3D3D3", spaceBefore=6, spaceAfter=6))

        story.append(PageBreak())

        add_section_title("User-Provided Documentation")
        attachments = session.get('attachments', [])
        for att in attachments:
            file_path = att['path']
            if os.path.exists(file_path):
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    pil_img = PILImage.open(file_path)
                    img_width, img_height = pil_img.size
                    
                    # Calculate aspect ratio
                    aspect_ratio = img_width / img_height
                    
                    target_width = 450
                    target_height = target_width / aspect_ratio
                    
                    story.append(Paragraph(f"<b>Attachment:</b> {att['filename']}", styles['Normal']))
                    story.append(Spacer(1, 12))
                    
                    img = Image(file_path, width=target_width, height=target_height)
                    story.append(img)
                    story.append(PageBreak())
                elif file_path.lower().endswith('.pdf'):
                    pages = convert_from_path(file_path)
                    for i, page in enumerate(pages):
                        temp_fd, temp_image_path = tempfile.mkstemp(suffix='.png')
                        os.close(temp_fd)
                        page.save(temp_image_path, 'PNG')
                        
                        pil_img = PILImage.open(temp_image_path)
                        img_width, img_height = pil_img.size
                        
                        aspect_ratio = img_width / img_height
                        
                        target_width = 450
                        target_height = target_width / aspect_ratio
                        
                        # Add caption
                        story.append(Paragraph(f"<b>Attachment:</b> {att['filename']} (Page {i+1})", styles['Normal']))
                        story.append(Spacer(1, 12))
                        
                        # Create ReportLab Image with fixed dimensions
                        img = Image(temp_image_path, width=target_width, height=target_height)
                        story.append(img)
                        story.append(PageBreak())
                        temp_files.append(temp_image_path)

        doc.build(story)
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"Error deleting temporary file {temp_file}: {e}")

    buffer.seek(0)
    return buffer