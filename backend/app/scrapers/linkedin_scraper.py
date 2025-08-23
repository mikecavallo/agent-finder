# scrapers/linkedin_scraper.py
import re
import json
from .anti_detection import AntiDetectionScraper
from .base_scraper import BaseScraper

class LinkedInScraper(BaseScraper, AntiDetectionScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.linkedin.com"
        self.logged_in = False
        
    async def login(self, email, password):
        """Login to LinkedIn (required for profile access)"""
        browser, context = await self.create_stealth_browser()
        
        try:
            page = await context.new_page()
            await page.goto(f"{self.base_url}/login", wait_until='networkidle')
            
            # Fill login form
            await page.fill('#username', email)
            await page.fill('#password', password)
            await self.random_delay(1, 2)
            
            # Submit form
            await page.click('button[type="submit"]')
            await page.wait_for_navigation()
            
            # Check if login successful
            if '/feed' in page.url or '/in/' in page.url:
                self.logged_in = True
                # Save session cookies
                cookies = await context.cookies()
                self.save_session_cookies(cookies, filename="linkedin_cookies.json")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"LinkedIn login error: {e}")
            return False
        finally:
            await browser.close()
    
    async def search_open_to_work(self, state, keywords, max_results=50):
        """Search for candidates with 'Open to Work' badge"""
        if not self.logged_in:
            raise Exception("Must be logged in to search LinkedIn")
            
        browser, context = await self.create_stealth_browser()
        candidates = []
        
        try:
            # Restore session
            await self.restore_session_cookies(context, filename="linkedin_cookies.json")
            page = await context.new_page()
            
            # Build search URL for people
            search_query = f"{' '.join(keywords)} \"{state}\""
            search_url = f"{self.base_url}/search/people/?keywords={search_query}&origin=GLOBAL_SEARCH_HEADER"
            
            await page.goto(search_url, wait_until='networkidle')
            await self.random_delay(3, 6)
            
            # Scroll to load more results
            await self.human_like_scroll(page)
            
            # Extract profile links
            profile_elements = await page.query_selector_all('.reusable-search__result-container')
            
            for i, element in enumerate(profile_elements[:max_results]):
                try:
                    # Check for "Open to Work" badge
                    open_to_work = await element.query_selector('.artdeco-entity-lockup__subtitle .open-to-work')
                    if not open_to_work:
                        continue
                    
                    # Get profile link
                    profile_link = await element.query_selector('a[href*="/in/"]')
                    if profile_link:
                        profile_url = await profile_link.get_attribute('href')
                        candidate = await self.extract_linkedin_profile(context, profile_url)
                        if candidate:
                            candidates.append(candidate)
                    
                    await self.random_delay(2, 4)
                    
                    # Take longer breaks every 10 profiles
                    if i > 0 and i % 10 == 0:
                        await self.random_delay(15, 30)
                        
                except Exception as e:
                    self.logger.error(f"Error processing LinkedIn profile {i}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"LinkedIn search error: {e}")
        finally:
            await browser.close()
            
        return candidates
    
    async def extract_linkedin_profile(self, context, profile_url):
        """Extract detailed LinkedIn profile information"""
        page = await context.new_page()
        
        try:
            await page.goto(profile_url, wait_until='networkidle')
            await self.random_delay(2, 4)
            
            candidate_data = {
                'source': 'linkedin',
                'profile_url': profile_url
            }
            
            # Name
            name_element = await page.query_selector('.text-heading-xlarge')
            if name_element:
                candidate_data['name'] = await name_element.text_content()
            
            # Current title and company
            headline_element = await page.query_selector('.text-body-medium.break-words')
            if headline_element:
                headline = await headline_element.text_content()
                candidate_data['current_title'] = headline
            
            # Location
            location_element = await page.query_selector('.text-body-small.inline.t-black--light.break-words')
            if location_element:
                location_text = await location_element.text_content()
                candidate_data['city'], candidate_data['state'] = self.parse_location(location_text)
            
            # Experience section
            experience_section = await page.query_selector('#experience')
            if experience_section:
                experience_items = await experience_section.query_selector_all('.artdeco-list__item')
                experience_data = []
                for item in experience_items[:3]:  # Get top 3 experiences
                    exp_text = await item.text_content()
                    experience_data.append(exp_text.strip())
                candidate_data['experience'] = '; '.join(experience_data)
            
            # Education section
            education_section = await page.query_selector('#education')
            if education_section:
                edu_items = await education_section.query_selector_all('.artdeco-list__item')
                education_data = []
                for item in edu_items[:2]:  # Get top 2 education entries
                    edu_text = await item.text_content()
                    education_data.append(edu_text.strip())
                candidate_data['education'] = '; '.join(education_data)
            
            # Skills section
            skills_section = await page.query_selector('#skills')
            if skills_section:
                skill_items = await skills_section.query_selector_all('.artdeco-list__item')
                skills_data = []
                for item in skill_items[:10]:  # Get top 10 skills
                    skill_text = await item.text_content()
                    skills_data.append(skill_text.strip())
                candidate_data['skills'] = ', '.join(skills_data)
            
            # Try to find contact info button
            contact_button = await page.query_selector('button:has-text("Contact info")')
            if contact_button:
                await contact_button.click()
                await self.random_delay(1, 2)
                
                # Extract email if visible
                email_element = await page.query_selector('[href^="mailto:"]')
                if email_element:
                    email_href = await email_element.get_attribute('href')
                    candidate_data['email'] = email_href.replace('mailto:', '')
                
                # Extract phone if visible
                phone_element = await page.query_selector('.ci-phone')
                if phone_element:
                    phone_text = await phone_element.text_content()
                    candidate_data['phone'] = self.clean_phone_number(phone_text)
            
            return candidate_data
            
        except Exception as e:
            self.logger.error(f"Error extracting LinkedIn profile {profile_url}: {e}")
            return None
        finally:
            await page.close()

    def clean_phone_number(self, phone_text: str) -> str:
        """Cleans and formats a phone number string."""
        # Remove non-digit characters and return
        return re.sub(r'\D', '', phone_text)
