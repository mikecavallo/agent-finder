def get_initial_outreach_template(candidate_name: str, recruiter_name: str) -> dict:
    subject = f"Exciting Opportunity for {candidate_name} - Insurance Agent Role"
    body = f"""
Dear {candidate_name},

I hope this email finds you well.

My name is {recruiter_name} and I'm a recruiter specializing in connecting talented individuals with leading opportunities in the insurance sector.

Your profile recently caught my attention, and I believe your skills and experience would be a great fit for an exciting Insurance Agent position we are currently looking to fill.

Would you be open to a brief chat sometime next week to discuss this further? Please let me know what time works best for you.

Best regards,

{recruiter_name}
"""
    return {"subject": subject, "body": body}
