# ai/resume_analyzer.py
import openai
import json
import asyncio
from typing import Dict, List
from ..utils.pdf_parser import extract_text_from_pdf

class ResumeAnalyzer:
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        
    async def analyze_resume(self, resume_path: str = None, resume_text: str = None) -> Dict:
        """Analyze resume for insurance agent suitability"""
        
        if resume_path and not resume_text:
            resume_text = extract_text_from_pdf(resume_path)
        
        if not resume_text or len(resume_text.strip()) < 100:
            return {"score": 0, "analysis": "Insufficient resume content for analysis"}
        
        analysis_prompt = self.get_analysis_prompt(resume_text)
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert insurance industry recruiter with 15 years of experience evaluating candidates for insurance agent positions."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            return {"score": 0, "analysis": f"Analysis error: {str(e)}"}
    
    def get_analysis_prompt(self, resume_text: str) -> str:
        """Generate analysis prompt for insurance agent evaluation"""
        return f"""
        Analyze this resume for insurance agent suitability. Score 1-10 (10 being perfect fit) and provide a concise 2-3 sentence analysis.

        SCORING CRITERIA (weight in parentheses):
        - Sales experience (30%): B2B/B2C sales, commission-based roles, sales achievements
        - Customer service background (25%): Client-facing roles, problem resolution, relationship building
        - Insurance/financial experience (20%): Insurance, banking, finance, real estate experience
        - Communication skills (15%): Presentations, training, public speaking, writing
        - Education/licenses (10%): Relevant degree, insurance licenses, certifications

        BONUS POINTS:
        - Existing insurance licenses (+2 points)
        - Proven sales numbers/achievements (+1 point)
        - Leadership/management experience (+1 point)
        - Bilingual capabilities (+0.5 points)

        RED FLAGS (deduct points):
        - Job hopping (many jobs < 1 year) (-1 to -2 points)
        - No customer-facing experience (-2 points)
        - Gaps in employment without explanation (-1 point)

        Resume Content:
        {resume_text[:3000]}  # Limit to first 3000 chars for API efficiency

        Respond with ONLY valid JSON in this exact format:
        {{
            "score": 7.5,
            "analysis": "Strong sales background with 5 years in automotive sales and excellent customer service record. Previous experience in financial services makes this candidate highly suitable for insurance agent role.",
            "key_strengths": ["Sales experience", "Customer service", "Financial background"],
            "concerns": ["Limited insurance-specific experience"],
            "recommendation": "Highly recommend for interview"
        }}
        """
    
    async def batch_analyze_resumes(self, candidates: List[Dict]) -> List[Dict]:
        """Analyze multiple resumes concurrently"""
        tasks = []
        
        for candidate in candidates:
            if candidate.get('resume_path') and not candidate.get('ai_score'):
                task = self.analyze_resume(resume_path=candidate['resume_path'])
                tasks.append((candidate['id'], task))
        
        # Process in batches of 5 to avoid rate limits
        batch_size = 5
        results = {}
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*[task for _, task in batch], return_exceptions=True)
            
            for (candidate_id, _), result in zip(batch, batch_results):
                if not isinstance(result, Exception):
                    results[candidate_id] = result
                else:
                    results[candidate_id] = {"score": 0, "analysis": f"Analysis failed: {str(result)}"}
            
            # Rate limiting between batches
            await asyncio.sleep(1)
        
        return results
