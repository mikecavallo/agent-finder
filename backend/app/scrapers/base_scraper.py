import logging
import os
import json
from datetime import datetime
from ..utils.file_manager import save_file

class BaseScraper:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def parse_location(self, location_text: str):
        """Parses location text into city and state."""
        # This is a basic implementation, can be improved with more complex regex or external libraries
        parts = [p.strip() for p in location_text.split(',')]
        city = parts[0] if parts else None
        state = parts[1] if len(parts) > 1 else None
        return city, state

    async def download_resume(self, context, resume_url: str, candidate_name: str) -> str:
        """Downloads a resume and saves it to the local filesystem."""
        self.logger.info(f"Attempting to download resume from {resume_url} for {candidate_name}")
        try:
            page = await context.new_page()
            response = await page.goto(resume_url, wait_until='domcontentloaded')
            
            if response.status == 200 and 'application/pdf' in response.headers.get('content-type', ''):
                content = await response.body()
                resume_filename = f"{candidate_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                save_path = await save_file(content, resume_filename, 'resumes')
                if save_path:
                    self.logger.info(f"Resume downloaded and saved to {save_path}")
                    return save_path
                else:
                    self.logger.error(f"Failed to save resume file for {candidate_name}")
                    return None
            else:
                self.logger.warning(f"URL {resume_url} did not return a PDF or status was not 200. Content-Type: {response.headers.get('content-type')}, Status: {response.status}")
                # Attempt to find a download link on the page if it's not a direct PDF
                download_link = await page.query_selector('a[href*=".pdf" i]')
                if download_link:
                    pdf_url = await download_link.get_attribute('href')
                    self.logger.info(f"Found potential PDF link on page: {pdf_url}. Attempting to download.")
                    # Recursive call, but ensure it doesn't loop infinitely
                    return await self.download_resume(context, pdf_url, candidate_name)
                else:
                    self.logger.warning(f"No direct PDF or PDF download link found on {resume_url}")
                    return None
        except Exception as e:
            self.logger.error(f"Failed to download resume from {resume_url}: {e}")
            return None
        finally:
            await page.close()

    async def check_for_captcha(self, page) -> bool:
        """Checks if a CAPTCHA is present on the page."""
        # This is a placeholder. Implement actual CAPTCHA detection logic.
        captcha_indicators = [
            '#captcha',
            '.g-recaptcha',
            'text=Are you a robot?'
        ]
        for selector in captcha_indicators:
            if await page.query_selector(selector):
                self.logger.warning(f"CAPTCHA indicator found: {selector}")
                return True
        return False

    async def solve_captcha(self, page):
        """Attempts to solve a CAPTCHA. Placeholder for 2Captcha integration."""
        self.logger.warning("CAPTCHA solving logic is a placeholder. Integrate 2Captcha or similar service.")
        # Example: Interact with 2Captcha API here
        # await page.wait_for_selector('#captcha_solution_input')
        # await page.fill('#captcha_solution_input', 'solved_captcha_text')
        # await page.click('#captcha_submit_button')
        await page.wait_for_timeout(5000) # Simulate solving time

    def save_session_cookies(self, cookies: list, filename="session_cookies.json"):
        """Saves Playwright session cookies to a file."""
        try:
            os.makedirs('data/sessions', exist_ok=True)
            with open(os.path.join('data/sessions', filename), 'w') as f:
                json.dump(cookies, f)
            self.logger.info(f"Session cookies saved to data/sessions/{filename}")
        except Exception as e:
            self.logger.error(f"Failed to save session cookies: {e}")

    def restore_session_cookies(self, context, filename="session_cookies.json"):
        """Restores Playwright session cookies from a file."""
        try:
            filepath = os.path.join('data/sessions', filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    cookies = json.load(f)
                context.add_cookies(cookies)
                self.logger.info(f"Session cookies restored from data/sessions/{filepath}")
                return True
            else:
                self.logger.info(f"No session cookies found at {filepath}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to restore session cookies: {e}")
            return False

