# scrapers/indeed_scraper.py
import re
import asyncio
from urllib.parse import urlencode, urlparse
from .anti_detection import AntiDetectionScraper
from .base_scraper import BaseScraper

class IndeedScraper(BaseScraper, AntiDetectionScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.indeed.com"
        
    async def search_candidates(self, state, keywords, experience_level="", max_results=50):
        """Search for open-to-work candidates on Indeed"""
        browser, context = await self.create_stealth_browser()
        candidates = []
        
        try:
            page = await context.new_page()
            
            # Build search URL
            search_params = {
                'q': f"{' '.join(keywords)} open to work",
                'l': state,
                'filter': '0',  # All jobs
                'radius': '50',  # 50 mile radius
                'sort': 'date'  # Most recent first
            }
            
            search_url = f"{self.base_url}/resumes?{urlencode(search_params)}"
            
            await page.goto(search_url, wait_until='networkidle')
            await self.random_delay(3, 6)
            
            # Handle potential CAPTCHA or blocking
            if await self.check_for_captcha(page):
                await self.solve_captcha(page)
            
            # Extract candidate profiles
            profile_links = await page.query_selector_all('[data-jk] a')
            
            for i, link in enumerate(profile_links[:max_results]):
                if i > 0 and i % 10 == 0:  # Every 10 profiles, take a break
                    await self.random_delay(10, 20)
                
                try:
                    profile_url = await link.get_attribute('href')
                    if profile_url and '/viewjob?jk=' in profile_url:
                        candidate = await self.extract_candidate_profile(context, profile_url)
                        if candidate:
                            candidates.append(candidate)
                            
                    await self.random_delay(2, 4)
                    
                except Exception as e:
                    self.logger.error(f"Error processing profile {i}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Indeed scraping error: {e}")
        finally:
            await browser.close()
            
        return candidates
    
    async def extract_candidate_profile(self, context, profile_url):
        """Extract detailed candidate information"""
        page = await context.new_page()
        
        try:
            full_url = f"{self.base_url}{profile_url}" if profile_url.startswith('/') else profile_url
            await page.goto(full_url, wait_until='networkidle')
            
            # Extract candidate information
            candidate_data = {
                'source': 'indeed',
                'profile_url': full_url
            }
            
            # Name extraction
            name_element = await page.query_selector('[data-testid="job-title"]')
            if name_element:
                candidate_data['name'] = await name_element.text_content()
            
            # Company and title
            company_element = await page.query_selector('[data-testid="company-name"]')
            if company_element:
                candidate_data['current_company'] = await company_element.text_content()
            
            # Location
            location_element = await page.query_selector('[data-testid="job-location"]')
            if location_element:
                location_text = await location_element.text_content()
                candidate_data['city'], candidate_data['state'] = self.parse_location(location_text)
            
            # Description/Summary
            description_element = await page.query_selector('.jobsearch-jobDescriptionText')
            if description_element:
                candidate_data['description'] = await description_element.text_content()
            
            # Try to find contact information
            contact_info = await self.extract_contact_info(page)
            candidate_data.update(contact_info)
            
            # Try to download resume if available
            resume_link = await page.query_selector('a[href*="resume"]')
            if resume_link:
                resume_url = await resume_link.get_attribute('href')
                candidate_data['resume_path'] = await self.download_resume(context, resume_url, candidate_data.get('name', 'unknown'))
            
            return candidate_data
            
        except Exception as e:
            self.logger.error(f"Error extracting profile {profile_url}: {e}")
            return None
        finally:
            await page.close()

    async def extract_contact_info(self, page):
        """Extracts contact information from an Indeed profile page."""
        contact_data = {"email": None, "phone": None}
        # Indeed often hides contact info behind a button or requires login.
        # This is a placeholder for actual extraction logic if it becomes available.
        self.logger.info("Indeed contact info extraction is a placeholder.")
        return contact_data
