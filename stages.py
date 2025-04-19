from constants import DOCUMENTATION_GATHERING, FINAL_QUESTIONS, MAX_POSSIBLE_FOLLOWUPS_PER_QUESTION, MAX_POSSIBLE_THREATS_PER_STAGE, NEXT_STAGE_COMMAND, PRESENTATION, STRIDE_DENIAL_OF_SERVICE, STRIDE_ELEVATION_OF_PRIVILEGE, STRIDE_INFORMATION_DISCLOSURE, STRIDE_REPUDIATION, STRIDE_SPOOFING, STRIDE_TAMPERING

STAGES_ARR = []

class StageInformation:
    def __init__(self):
        self.name = ""
        self.description = ""
        self.objective = ""
        self.common_problems = []
        
    def set_name(self, name):
        self.name = name
        
    def set_description(self, description):
        self.description = description
        
    def set_objective(self, objective):
        self.objective = objective
        
    def add_common_problem(self, problem):
        self.common_problems.append(problem)
        
    def get_stage_description(self):
        prompt = f"""
Stage name: {self.name}
Description: {self.description}
Objective: {self.objective}
"""
        if len(self.common_problems) > 0:
            prompt += f"Common problems: {', '.join(self.common_problems)}"
        return prompt

def get_end_comment():
    return f"""Avoid discussing additional mitigations to implement, instead concentrate on discovering risks or identifying which controls or safeguards are absent. When you believe you've examined sufficient potential risks, ask the user to proceed to the next stage by concluding with the keyword {NEXT_STAGE_COMMAND}. Limit your analysis to {MAX_POSSIBLE_THREATS_PER_STAGE} distinct potential threats for this stage (do not ask all of them in the same message and do not request more than {MAX_POSSIBLE_FOLLOWUPS_PER_QUESTION} per potential threat). You can answer unlimited questions from the user without changing stages. Only ask one question at a time to prevent user confusion."""

def add_documentation_gathering_stage():
    stage_information = StageInformation()
    stage_information.set_name(DOCUMENTATION_GATHERING)
    stage_information.set_description("This initial stage focuses on collecting all relevant documentation about the service under review")
    stage_information.set_objective(f"Guide the user to upload all available documentation for the service. They may only upload PDFs or images. Inform them that once they have completed uploading all materials, they should proceed to the next stage. When they indicate they've finished uploading documentation, respond with this keyword: {NEXT_STAGE_COMMAND}")
    STAGES_ARR.append(stage_information)

def add_spoofing_stage():
    stage_information = StageInformation()
    stage_information.set_name(STRIDE_SPOOFING)
    stage_information.set_description("This stage examines Spoofing threats from the STRIDE model. We'll explore vulnerabilities related to identity verification and authentication mechanisms.")
    stage_information.set_objective("Examine and evaluate risks connected to identity impersonation and fraudulent authentication." + get_end_comment())
    stage_information.add_common_problem("Insufficient or missing authentication/authorization mechanisms")
    stage_information.add_common_problem("Lack of password rotation policies")
    STAGES_ARR.append(stage_information)

def add_tampering_stage():
    stage_information = StageInformation()
    stage_information.set_name(STRIDE_TAMPERING)
    stage_information.set_description("This stage addresses Tampering threats from the STRIDE model. We'll investigate vulnerabilities concerning unauthorized alterations to data or code.")
    stage_information.set_objective("Detect and evaluate risks related to unauthorized alterations of data, code, or system configurations." + get_end_comment())
    stage_information.add_common_problem("Inadequate input validation in user interfaces")
    stage_information.add_common_problem("Absence of data integrity verification during transfers")
    STAGES_ARR.append(stage_information)

def add_repudiation_stage():
    stage_information = StageInformation()
    stage_information.set_name(STRIDE_REPUDIATION)
    stage_information.set_description("This stage covers Repudiation threats from the STRIDE model. We'll analyze vulnerabilities related to action tracking and user accountability.")
    stage_information.set_objective("Uncover and assess risks where users might deny their actions due to inadequate audit trails or logging mechanisms." + get_end_comment())
    stage_information.add_common_problem("Inadequate or missing user activity logging")
    stage_information.add_common_problem("Insecurely maintained audit records")
    STAGES_ARR.append(stage_information)

def add_information_disclosure_stage():
    stage_information = StageInformation()
    stage_information.set_name(STRIDE_INFORMATION_DISCLOSURE)
    stage_information.set_description("This stage evaluates Information Disclosure threats from the STRIDE model. We'll analyze vulnerabilities concerning data privacy and confidentiality.")
    stage_information.set_objective("Pinpoint and evaluate risks associated with unauthorized exposure of sensitive information." + get_end_comment())
    stage_information.add_common_problem("Unencrypted storage of confidential information")
    stage_information.add_common_problem("System details revealed in error messages")
    STAGES_ARR.append(stage_information)

def add_denial_of_service_stage():
    stage_information = StageInformation()
    stage_information.set_name(STRIDE_DENIAL_OF_SERVICE)
    stage_information.set_description("This stage assesses Denial of Service threats from the STRIDE model. We'll examine vulnerabilities affecting system reliability and availability.")
    stage_information.set_objective("Identify and evaluate risks related to service interruptions and resource depletion attacks." + get_end_comment())
    stage_information.add_common_problem("Missing request rate limitations on API endpoints")
    stage_information.add_common_problem("Limited resource scaling capabilities during high demand")
    STAGES_ARR.append(stage_information)

def add_elevation_of_privilege_stage():
    stage_information = StageInformation()
    stage_information.set_name(STRIDE_ELEVATION_OF_PRIVILEGE)
    stage_information.set_description("This stage explores Elevation of Privilege threats from the STRIDE model. We'll investigate vulnerabilities in permission systems and access controls.")
    stage_information.set_objective("Discover and evaluate risks where users might obtain higher system privileges than intended." + get_end_comment())
    stage_information.add_common_problem("Default administrative privileges for standard users")
    stage_information.add_common_problem("Insufficient access restrictions on critical system functions")
    STAGES_ARR.append(stage_information)

def add_final_questions_stage():
    stage_information = StageInformation()
    stage_information.set_name(FINAL_QUESTIONS)
    stage_information.set_description("This stage is for yout to ask any remaining inquiries or concerns you might have about the service that has not been discussed already")
    stage_information.set_objective("You must address any unresolved issues or confirm all significant threats have been properly identified and examined. When finished or asked over 5 questions, conclude with: " + NEXT_STAGE_COMMAND)
    STAGES_ARR.append(stage_information)

def add_presentation_stage():
    stage_information = StageInformation()
    stage_information.set_name(PRESENTATION)
    stage_information.set_description("In this concluding stage, we'll compile all discovered threats and provide strategic recommendations.")
    stage_information.set_objective("Deliver a comprehensive overview of the threat assessment findings and suggest practical mitigation strategies. Include only those risks that were explicitly discussed and identified during the previous conversation stages.")
    STAGES_ARR.append(stage_information)


add_documentation_gathering_stage()
add_spoofing_stage()
add_tampering_stage()
add_repudiation_stage()
add_information_disclosure_stage()
add_denial_of_service_stage()
add_elevation_of_privilege_stage()
add_final_questions_stage()
add_presentation_stage()