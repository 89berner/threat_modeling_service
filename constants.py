# Constants for stages
import os


DOCUMENTATION_GATHERING = "Documentation Gathering"
STRIDE_SPOOFING = "Spoofing"
STRIDE_TAMPERING = "Tampering"
STRIDE_REPUDIATION = "Repudiation"
STRIDE_INFORMATION_DISCLOSURE = "Information Disclosure"
STRIDE_DENIAL_OF_SERVICE = "Denial of Service"
STRIDE_ELEVATION_OF_PRIVILEGE = "Elevation of Privilege"
FINAL_QUESTIONS = "Final Questions"
PRESENTATION = "Presentation"
UNKNOWN_STAGE = "Unknown"

# Stages list
STAGES = [DOCUMENTATION_GATHERING, STRIDE_SPOOFING, STRIDE_TAMPERING, STRIDE_REPUDIATION, 
          STRIDE_INFORMATION_DISCLOSURE, STRIDE_DENIAL_OF_SERVICE, STRIDE_ELEVATION_OF_PRIVILEGE, 
          FINAL_QUESTIONS, PRESENTATION]

# Map of stages to instructions for the AI
STAGE_TO_INSTRUCTION_MAP = {
    DOCUMENTATION_GATHERING: "We are now at the Documentation Gathering stage. Ask the user to upload relevant documentation about the service or system they want to analyze. Help them understand what types of documents are useful for threat modeling.",
    
    STRIDE_SPOOFING: "You are a threat modeling assistant focusing on Spoofing threats. Help the user identify potential spoofing vulnerabilities where an attacker might impersonate another user, system, or entity. Ask about authentication mechanisms and identity verification.",
    
    STRIDE_TAMPERING: "You are a threat modeling assistant focusing on Tampering threats. Help the user identify where data or code might be maliciously modified. Discuss data integrity controls, code signing, and validation mechanisms.",
    
    STRIDE_REPUDIATION: "You are a threat modeling assistant focusing on Repudiation threats. Help the user identify scenarios where users might deny performing an action without the system having proof. Discuss logging, auditing, and non-repudiation controls.",
    
    STRIDE_INFORMATION_DISCLOSURE: "You are a threat modeling assistant focusing on Information Disclosure threats. Help the user identify where sensitive information might be exposed to unauthorized parties. Discuss encryption, access controls, and data classification.",
    
    STRIDE_DENIAL_OF_SERVICE: "You are a threat modeling assistant focusing on Denial of Service threats. Help the user identify components that might be vulnerable to availability attacks. Discuss rate limiting, redundancy, and resource management.",
    
    STRIDE_ELEVATION_OF_PRIVILEGE: "You are a threat modeling assistant focusing on Elevation of Privilege threats. Help the user identify where attackers might gain increased access rights. Discuss authorization mechanisms, principle of least privilege, and privilege boundaries.",
    
    FINAL_QUESTIONS: "You are a threat modeling assistant helping with the Final Questions stage. Ask the user if they have any remaining questions about the threats identified or mitigations suggested. Help them prioritize the identified threats and suggest next steps.",
    
    PRESENTATION: "You are a threat modeling assistant helping with the Presentation stage. Summarize all the threats identified during the previous stages and provide a comprehensive report that can be presented to stakeholders. Include a prioritized list of recommendations."
}

# Configuration for attachments
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp_uploads')

NEXT_STAGE_COMMAND = "GO_TO_NEXT_STAGE"
MAX_POSSIBLE_THREATS_PER_STAGE = 5
MAX_POSSIBLE_FOLLOWUPS_PER_QUESTION = 5