def get_system_prompt():
    return """You're a seasoned security engineer specializing in threat modeling.
Your job is to walk users through spotting security risks in their systems, sticking strictly to identifying them, not fixing or softening them.
No need for fancy manners or extra politeness.
Be thorough and toss out clarifying questions to dig into the system and uncover potential threats fully.
You are allowed to only ask one question per message, if you want to ask multiple just ask one and wait for the answer to ask another.
"""

def get_initial_user_message():
    return """
Here’s the kickoff for the Documentation Gathering phase in our threat modeling process. To jump in, upload the key docs for your system. That could mean:  
Old threat model reports  

Pics or diagrams of the system architecture or workflows  

Any other useful docs in PDF form

Once you’ve dumped all your files, tell me you’re done or hit “next stage” so we can roll into the threat modeling itself.  
Got any questions before we start? If not, go ahead and upload whatever docs you’ve got.
"""

def generate_presentation_findings(conversation):
    return f"""I have a chat between a user and a threat modeling assistant. I need you to sift through it and pull out the findings they pinpointed—either by the assistant or the user. If any mitigations were mentioned, include those too. List them for me, ranked from most critical to least critical.  
Use this format:
Finding: X
Recommended Mitigation: X
Criticality: X (Options are VERY HIGH, HIGH, MEDIUM, LOW)  
Stick to only the findings clearly called out in the conversation, do not add any yourself.  

Here is the chat:  
{conversation}  
Now kick off your response with “Here are the findings for the threat modeling session:” and dont add any extra text or questions after the list.
"""