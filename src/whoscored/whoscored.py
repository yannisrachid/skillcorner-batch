from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from pyvirtualdisplay import Display
import time
# from IPython.display import clear_output
# from shared_functions import *
import json
import os
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class WhoScored():

    ############################################################################
    def __init__(self):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        self.display = Display(visible=0, size=(1920, 1080))
        self.display.start()
        
        # proxy = get_proxy() # Use proxy
        # options.add_argument('--proxy-server="http={};https={}"'.format(proxy, proxy))
        prefs = {'profile.managed_default_content_settings.images': 2} # don't load images to make faster
        options.add_experimental_option('prefs', prefs)

        chrome_driver_path = '/usr/bin/chromedriver'
        service = Service(chrome_driver_path)

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logging.info("Initializing WhoScored scraper")
        # clear_output()

        
    ############################################################################
    def close(self):
        logging.info("Closing WhoScored scraper")
        if hasattr(self, 'driver'):
            self.driver.quit()
        if hasattr(self, 'display'):
            self.display.stop()

        
    ############################################################################
    def get_season_link(self, year, league):
        #error, valid = check_season(year, league, 'WhoScored')
        #if not valid:
        #    print(error)
        #    return -1
        
        links = {
            'EPL': 'https://www.whoscored.com/Regions/252/Tournaments/2/England-Premier-League',
            'La Liga': 'https://www.whoscored.com/Regions/206/Tournaments/4/Spain-LaLiga',
            'Bundesliga': 'https://www.whoscored.com/Regions/81/Tournaments/3/Germany-Bundesliga',
            'Serie A': 'https://www.whoscored.com/Regions/108/Tournaments/5/Italy-Serie-A',
            'Ligue 1': 'https://www.whoscored.com/Regions/74/Tournaments/22/France-Ligue-1',
            'Argentina Liga Profesional': 'https://www.whoscored.com/Regions/11/Tournaments/68/Argentina-Liga-Profesional',
            'EFL Championship': 'https://www.whoscored.com/Regions/252/Tournaments/7/England-Championship',
            'EFL1': 'https://www.whoscored.com/Regions/252/Tournaments/8/England-League-One',
            'EFL2': 'https://www.whoscored.com/Regions/252/Tournaments/9/England-League-Two',
            # Edd Webster added these leagues (twitter: https://twitter.com/eddwebster)
            'Liga Nos': 'https://www.whoscored.com/Regions/177/Tournaments/21/Portugal-Liga-NOS',
            'Eredivisie': 'https://www.whoscored.com/Regions/155/Tournaments/13/Netherlands-Eredivisie',
            'Russian Premier League': 'https://www.whoscored.com/Regions/182/Tournaments/77/Russia-Premier-League',
            'Brasileirao': 'https://www.whoscored.com/Regions/31/Tournaments/95/Brazil-Brasileir%C3%A3o',
            'MLS': 'https://www.whoscored.com/Regions/233/Tournaments/85/USA-Major-League-Soccer',
            'Super Lig': 'https://www.whoscored.com/Regions/225/Tournaments/17/Turkey-Super-Lig',
            'Jupiler Pro League': 'https://www.whoscored.com/Regions/22/Tournaments/18/Belgium-Jupiler-Pro-League',
            'Bundesliga II': 'https://www.whoscored.com/Regions/81/Tournaments/6/Germany-Bundesliga-II',
            'Champions League': 'https://www.whoscored.com/Regions/250/Tournaments/12/Europe-Champions-League',
            'Europa League': 'https://www.whoscored.com/Regions/250/Tournaments/30/Europe-Europa-League',
            'FA Cup': 'https://www.whoscored.com/Regions/252/Tournaments/29/England-League-Cup',
            'League Cup': 'https://www.whoscored.com/Regions/252/Tournaments/29/England-League-Cup',
            'World Cup': 'https://www.whoscored.com/Regions/247/Tournaments/36/International-FIFA-World-Cup',
            'European Championship': 'https://www.whoscored.com/Regions/247/Tournaments/124/International-European-Championship',
            'AFCON': 'https://www.whoscored.com/Regions/247/Tournaments/104/International-Africa-Cup-of-Nations'
            # End of Edd Webster leagues
        }
        
        if (league=='Argentina Liga Profesional' and year in [2016,2021]) \
                or league in ['Brasileirao','MLS','World Cup','European Championship','AFCON']:
            year_str = str(year)
        else:
            year_str = '{}/{}'.format(year-1, year)
        
        # Repeatedly try to get the league's homepage
        done = False
        while not done:
            try:
                self.driver.get(links[league])
                done = True
            except:
                self.close()
                self.__init__()
                time.sleep(5)
        print('League page status: {}'.format(self.driver.execute_script('return document.readyState')))
        
        # Wait for season dropdown to be accessible, then find the link to the chosen season
        for el in self.driver.find_elements(By.TAG_NAME, 'select'):
            if el.get_attribute('id') == 'seasons':
                for subel in el.find_elements(By.TAG_NAME, 'option'):
                    if subel.text==year_str:
                        return 'https://www.whoscored.com'+subel.get_attribute('value')
        return -1

    def handle_cookie_consent(self):
        # self.save_html("before_cookie_consent.html")
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            agree_button_xpath = (
                "//div[contains(@class, 'qc-cmp2-footer')]//button[contains(@class, 'css-1wc0q5e')]"
                "/span[text()='AGREE']/parent::button"
            )
            
            try:
                agree_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, agree_button_xpath))
                )
                self.driver.execute_script("arguments[0].click();", agree_button)
                print("Cookie consent handled successfully")
                time.sleep(5)
                # self.save_html("after_cookie_consent.html")
                return True
            except Exception as e:
                print(f"Error clicking AGREE button: {str(e)}")
                
            try:
                close_button_xpath = "//button[@aria-label='Close']"
                close_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, close_button_xpath))
                )
                self.driver.execute_script("arguments[0].click();", close_button)
                print("Closed cookie consent dialog")
                time.sleep(2)
                self.save_html("after_closing_consent_dialog.html")
                return True
            except Exception as e:
                print(f"Error closing consent dialog: {str(e)}")
            
            print("Could not handle cookie consent")
            return False
        except Exception as e:
            print(f"Failed to handle cookie consent: {str(e)}")
            self.capture_screenshot("cookie_consent_error.png")
            self.save_html("cookie_consent_error.html")
            return False
        
    def save_html(self, filename):
        try:
            html_content = self.driver.page_source
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"HTML content saved to {filename}")
        except Exception as e:
            print(f"Error saving HTML content: {str(e)}")

    ############################################################################
    def get_match_links(self, year, league):
        logging.info(f"Getting match links for {league} {year}")
        # Go to season page
        season_link = self.get_season_link(year, league)
        if season_link == -1:
            print("Failed to get season link.")
            return -1
        
        self.driver.get(season_link)
        logging.info(f'Season page status: {self.driver.execute_script("return document.readyState")}')

        if not self.handle_cookie_consent():
            logging.warning("Failed to handle cookie consent, continuing anyway...")
        
        if not self.handle_cookie_consent():
            print("Failed to handle cookie consent, continuing anyway...")
        
        # Gather the links. Make this a set to avoid repeat match links.
        links = set()
        stage_elements = self.driver.find_elements(By.XPATH, '//*[@id="stages"]/option')
        stage_urls = ['https://www.whoscored.com' + el.get_attribute('value') for el in stage_elements]
        if not stage_urls:
            stage_urls = [self.driver.current_url]
        
        logging.info(f"Number of stages found: {len(stage_urls)}")
        
        # Iterate through the stages
        for stage_url in stage_urls:
            logging.info(f"Processing stage: {stage_url}")
            self.driver.get(stage_url)

            """
            # Go to the fixtures
            fixtures_button = WebDriverWait(
                self.driver, 
                10, 
                ignored_exceptions=[TimeoutException]
            ).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#sub-navigation > ul:nth-child(1) > li:nth-child(2) > a:nth-child(1)")
            ))
            self.driver.execute_script('arguments[0].click()', fixtures_button)
            """
        
            print('{} status: {}'.format(stage_url, 
                                         self.driver.execute_script('return document.readyState')))

            max_attempts = 10
            attempts = 0
            current_date = None

            while attempts < max_attempts:
                attempts += 1
                time.sleep(2)  # Reduced wait time

                logging.info(f"--- Attempt {attempts} ---")
                
                try:
                    date_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "toggleDatePicker"))
                    )
                    new_date = date_element.text
                    if new_date != current_date:
                        logging.info(f"Date changed: {new_date}")
                        current_date = new_date
                    else:
                        logging.info("Date didn't change, page might not have updated")
                        if attempts > 1:
                            break
                except Exception as e:
                    logging.error(f"Error getting date: {str(e)}")
                
                match_elements = self.driver.find_elements(By.XPATH, "//a[contains(@class, 'Match-module_score')]")
                new_links = set(el.get_attribute('href') for el in match_elements if el.get_attribute('href'))
                links.update(new_links)

                logging.info(f"New links found: {len(new_links)}")
                logging.info(f"Total unique links: {len(links)}")
                
                if not new_links and attempts > 1:
                    logging.info("No new links found. Stopping.")
                    break
                
                try:
                    prev_week_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "dayChangeBtn-prev"))
                    )
                    
                    if not prev_week_button.is_enabled():
                        logging.info("Previous week button is disabled. Stopping.")
                        break
                    
                    logging.info("Clicking previous week button...")
                    self.driver.execute_script("arguments[0].click();", prev_week_button)
                    time.sleep(3)  # Reduced wait time after click
                except Exception as e:
                    logging.error(f"Error with previous week button: {str(e)}")
                    break

        match_data_just_links = {link.replace("Show", "Live") if "Show" in link else link: '' for link in links}
        
        # save_filename = f'json_data/{league}_{year}_match_data.json'.replace(' ', '_')
        # with open(save_filename, 'w') as f:
        #     json.dump(match_data_just_links, f, indent=2)
        # logging.info(f'Match links saved to {save_filename}')
        
        return match_data_just_links
    

    def check_captcha(self):
        try:
            captcha = self.driver.find_element(By.ID, "captcha-container")
            if captcha.is_displayed():
                print("Captcha detected. Please solve it manually.")
                input("Press Enter after solving the captcha...")
                return True
        except NoSuchElementException:
            return False

    def capture_screenshot(self, filename):
        try:
            self.driver.save_screenshot(filename)
            print(f"Screenshot saved as {filename}")
        except Exception as e:
            print(f"Failed to capture screenshot: {str(e)}")

    def bypass_bot_detection(self):
        self.driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """)
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
        
    ############################################################################
    def scrape_matches(self, year, league):
        #error, valid = check_season(year, league, 'WhoScored')
        #if not valid:
        #    print(error)
        #    return -1

        logging.info(f"Starting to scrape matches for {league} {year}")

        # Read match links from file or get them with selenium
        # save_filename = f'json_data/{league}_{year}_match_data.json'.replace(' ', '_')
        # if os.path.exists(save_filename):
        #    with open(save_filename, 'r') as f:
        #        match_data = json.load(f)
        #else:
        match_data = self.get_match_links(year, league)
        if match_data == -1:
            return -1
            
        logging.info(f"Total matches found for {league} {year}: {len(match_data)}")
        
        for i, link in enumerate(match_data, 1):
            if match_data[link] == '':
                for try_count in range(1, 4):
                    try:
                        logging.info(f"Scraping match {i}/{len(match_data)} (Attempt {try_count})")
                        match_data[link] = self.scrape_match(link)
                        break
                    except Exception as e:
                        logging.error(f"Error scraping match: {str(e)}")
                        if try_count == 3:
                            logging.error(f'Failed to scrape match {i}/{len(match_data)} from {link}')
                        else:
                            self.close()
                            self.__init__()
                            time.sleep(2)
        
        # with open(save_filename, 'w') as f:
            # json.dump(match_data, f, indent=2)
        # logging.info(f"Scraping completed. Data saved to {save_filename}")
        return match_data

    
    ############################################################################
    def scrape_match(self, link):
        self.driver.get(link)
        scripts = list()
        
        for el in self.driver.find_elements(By.TAG_NAME, 'script'):
            scripts.append(el.get_attribute('innerHTML'))
        
        for script in scripts:
            if 'require.config.params["args"]' in script:
                match_data_string = script
        
        match_data_string = match_data_string.split(' = ')[1] \
            .replace('matchId', '"matchId"') \
            .replace('matchCentreData', '"matchCentreData"') \
            .replace('matchCentreEventTypeJson', '"matchCentreEventTypeJson"') \
            .replace('formationIdNameMappings', '"formationIdNameMappings"') \
            .replace(';', '')
        match_data = json.loads(match_data_string)
        
        return match_data
    
    
    ################################################################################
    def tabularize_match_data_events(match_data):
    #-------------------------------------------------------------------------------
        df = pd.DataFrame(columns=['id', 'eventId', 'minute', 'second', 'teamId', 'playerId',
                                   'x', 'y', 'expandedMinute', 'periodValue', 'periodDisplayName',
                                   'typeValue', 'typeDisplayName', 'outcomeTypeValue',
                                   'outcomeTypeDisplayName', 'qualifiers', 'satisfiedEventTypes', 'isTouch'])
        events = match_data['matchCentreData']['events']
        for event in events:
            new_row = pd.Series(dtype=object)
            new_row['id'] = int(event['id'])
            try:
                new_row['eventId'] = event['eventId']
            except KeyError:
                new_row['eventId'] = None
            new_row['minute'] = event['minute']
            try:
                new_row['second'] = event['second']
            except KeyError:
                new_row['second'] = None
            new_row['teamId'] = event['teamId']
            try:
                new_row['playerId'] = event['playerId']
            except KeyError:
                new_row['playerId'] = None
            new_row['x'] = event['x']
            new_row['y'] = event['y']
            new_row['expandedMinute'] = event['expandedMinute']
            new_row['periodValue'] = event['period']['value']
            new_row['periodDisplayName'] = event['period']['displayName']
            new_row['typeValue'] = event['type']['value']
            new_row['typeDisplayName'] = event['type']['displayName']
            new_row['outcomeTypeValue'] = event['outcomeType']['value']
            new_row['outcomeTypeDisplayName'] = event['outcomeType']['displayName']
            qualifiers = event['qualifiers']
            if len(qualifiers) == 0:
                new_row['qualifiers'] = None
            else:
                qualifiers_df = pd.DataFrame(columns=['typeValue', 'typeDisplayName', 'value'])
                for qualifier in qualifiers:
                    new_qualifier_row = pd.Series(dtype=object)
                    new_qualifier_row['typeValue'] = qualifier['type']['value']
                    new_qualifier_row['typeDisplayName'] = qualifier['type']['displayName']
                    try:
                        new_qualifier_row['value'] = qualifier['value']
                    except KeyError:
                        new_qualifier_row['value'] = None
                    qualifiers_df = qualifiers_df.append(new_qualifier_row, ignore_index=True)
                new_row['qualifiers'] = qualifiers_df
            new_row['satisfiedEventTypes'] = event['satisfiedEventsTypes']
            new_row['isTouch'] = event['isTouch']
            df = df.append(new_row, ignore_index=True)
        return df
        