import threading
import time
import random
import os
import sys
import logging
import subprocess
import tempfile
from queue import Queue
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from colorama import Fore, Style, init

init(autoreset=True)
os.system("cls" if os.name == "nt" else "clear")

WRITE_LOCK = threading.Lock()

def setup_logging():
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/automation.log'),
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def cleanup_chrome_processes():
    try:
        subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                      capture_output=True, timeout=2, check=False)
        subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], 
                      capture_output=True, timeout=2, check=False)
    except:
        pass

def check_chrome_installation():
    username = os.getenv('USERNAME', 'admin')
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        rf"C:\Users\{username}\AppData\Local\Google\Chrome\Application\chrome.exe",
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            return path
    
    print(f"{Fore.RED}[-] Chrome not found! Install Google Chrome first.")
    sys.exit(1)

def rizzler_config():
    check_chrome_installation()
    
    while True:
        try:
            thread_count = int(input(f"{Fore.YELLOW}Enter threads (1-8 recommended): "))
            if 1 <= thread_count <= 15:
                break
            else:
                print(f"{Fore.RED}Please enter 1-15")
        except ValueError:
            print(f"{Fore.RED}Enter a valid number")
    
    os.system("cls" if os.name == "nt" else "clear")
    return thread_count

def rizzler_files():
    files = {
        "tokens": "tokens.txt",
        "success": "success.txt", 
        "failed": "failed.txt",
        "invalid": "invalid.txt",
        "proxies": "proxies.txt"
    }
    
    for file in files.values():
        if not os.path.exists(file):
            open(file, 'a').close()
    
    fake_address = {
        "line1": "123 MG Road",
        "city": "Mumbai",
        "state": "Maharashtra", 
        "postalCode": "400001"
    }
    
    return files["tokens"], files["success"], files["failed"], files["invalid"], files["proxies"], fake_address

def rizzler_tokens(tokens_file):
    tokens = []
    try:
        with open(tokens_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                raw_line = line
                if ":" in line:
                    parts = line.split(":")
                    last_segment = ""
                    for segment in reversed(parts):
                        cleaned = segment.strip().strip('"').strip("'")
                        if cleaned:
                            last_segment = cleaned
                            break
                    token = last_segment if last_segment else line
                else:
                    token = line
                
                if token:
                    tokens.append((raw_line, token))
    except FileNotFoundError:
        print(f"{Fore.RED}[-] {tokens_file} not found!")
        return []
    except Exception as e:
        print(f"{Fore.RED}[-] Error reading tokens: {e}")
        return []
    
    return tokens

def rizzler_proxies(proxies_file):
    proxies = []
    try:
        with open(proxies_file, "r") as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                if "@" in line:
                    proxies.append(line)
                elif ":" in line:
                    parts = line.split(":")
                    if len(parts) == 2:
                        proxies.append(line)
                    elif len(parts) == 4:
                        username, password, host, port = parts
                        proxies.append(f"{username}:{password}@{host}:{port}")
                else:
                    proxies.append(line)
    except FileNotFoundError:
        pass
    except Exception as e:
        pass
    
    return proxies

def rizzler_save(raw_line, success=True):
    with WRITE_LOCK:
        try:
            filename = "success.txt" if success else "failed.txt"
            with open(filename, "a") as f:
                f.write(raw_line + "\n")
        except:
            pass

def get_speed_chrome_options(thread_id, proxy=None):
    options = Options()
    
    profile_dir = os.path.join(tempfile.gettempdir(), f"chrome_profiles", f"Profile{thread_id}")
    os.makedirs(profile_dir, exist_ok=True)
    
    options.add_argument("--no-sandbox")
    options.add_argument("--headless=new")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-prompt-on-repost")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-web-resources")
    options.add_argument("--disable-component-extensions-with-background-pages")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript-harmony-shipping")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--aggressive-cache-discard")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-component-update")
    options.add_argument("--disable-ntp-popular-sites")
    options.add_argument("--disable-ntp-most-likely-f_sites")
    options.add_argument("--disable-quick-launch-shortcuts-fetching")
    
    options.add_argument("--max_old_space_size=2048")
    options.add_argument("--memory-pressure-off")
    options.add_argument("--max-threads=1")
    
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-default-apps")
    
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1366,768")
    
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--disable-extensions-http-throttling")
    options.add_argument("--disable-fetching-hints-at-navigation-start")
    options.add_argument("--disable-background-media-suspend")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-breakpad")
    options.add_argument("--disable-domain-reliability")
    options.add_argument("--disable-features=AudioServiceOutOfProcess")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--disable-features=Translate")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--disable-prefetch")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--disable-threaded-animation")
    options.add_argument("--disable-threaded-scrolling")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-webgl")
    options.add_argument("--disable-webgl2")
    options.add_argument("--enable-fast-unload")
    options.add_argument("--enable-tcp-fast-open")
    options.add_argument("--force-high-contrast")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-certificate-errors-spki-list")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--no-proxy-server")
    options.add_argument("--process-per-tab")
    
    options.add_argument(f"--user-data-dir={profile_dir}")
    
    if proxy:
        proxy_server = proxy.split("@")[1] if "@" in proxy else proxy
        options.add_argument(f'--proxy-server={proxy_server}')
    
    return options

def fast_click(driver, element):
    try:
        driver.execute_script("arguments[0].click();", element)
        return True
    except:
        try:
            ActionChains(driver).click(element).perform()
            return True
        except:
            return False

def speed_wait(driver, xpath, timeout=8):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        return element
    except:
        return None

def fast_login_check(driver, max_time=15):
    start = time.time()
    
    while time.time() - start < max_time:
        try:
            url = driver.current_url
            
            if any(x in url for x in ["channels/@me", "/app"]):
                try:
                    driver.find_element(By.XPATH, "//button[@aria-label='User Settings']")
                    return True
                except:
                    pass
        except:
            pass
        
        time.sleep(0.1)
    
    return False

def fast_fill_stripe_field(driver, field_name, value, max_retries=2, retry_interval=0.05):
    for attempt in range(max_retries):
        try:
            driver.switch_to.default_content()
            
            WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
            
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    field = driver.find_element(By.NAME, field_name)
                    
                    current_value = field.get_attribute('value') or ""
                    expected_clean = value.replace(" ", "").replace("/", "").replace("-", "")
                    actual_clean = current_value.replace(" ", "").replace("/", "").replace("-", "")
                    
                    if expected_clean == actual_clean:
                        driver.switch_to.default_content()
                        return True
                    
                    field.clear()
                    time.sleep(0.01)
                    field.send_keys(value)
                    
                    driver.execute_script("""
                        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                        arguments[0].blur();
                    """, field)
                    
                    time.sleep(0.02)
                    
                    new_value = field.get_attribute('value') or ""
                    new_clean = new_value.replace(" ", "").replace("/", "").replace("-", "")
                    
                    if expected_clean == new_clean:
                        driver.switch_to.default_content()
                        return True
                    
                except Exception:
                    driver.switch_to.default_content()
                    continue
            
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
                
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
    
    driver.switch_to.default_content()
    return False

def fast_card_filling(driver):
    time.sleep(0.1)
    
    card_details = [
        ("cardnumber", "5487933005613404"),
        ("exp-date", "10/27"),
        ("cvc", "068")
    ]
    
    success_count = 0
    
    for field_name, value in card_details:
        if fast_fill_stripe_field(driver, field_name, value, max_retries=2, retry_interval=0.05):
            success_count += 1
        time.sleep(0.01)
    
    return success_count >= 2

def fast_worker(thread_id, token_queue, proxies, fake_address):
    stats = {"success": 0, "failed": 0}
    
    time.sleep(thread_id * 0.05)
    
    while not token_queue.empty():
        driver = None
        start_time = time.time()
        
        try:
            raw_line, token = token_queue.get_nowait()
        except:
            break
        
        try:
            proxy = random.choice(proxies) if proxies else None
            options = get_speed_chrome_options(thread_id, proxy)
            
            service = Service()
            service.log_path = os.devnull
            if os.name == "nt":
                service.creation_flags = subprocess.CREATE_NO_WINDOW
            
            try:
                driver = webdriver.Chrome(service=service, options=options)
                driver.set_page_load_timeout(15)
                driver.implicitly_wait(1.0)
            except:
                time.sleep(0.1)
                driver = webdriver.Chrome(service=service, options=options) 
                driver.set_page_load_timeout(15)
                driver.implicitly_wait(1.0)
            
            driver.get("https://discord.com/login")
            time.sleep(0.1)
            
            login_script = f"""
            let token = "{token}";
            setInterval(() => {{
                document.body.appendChild(document.createElement('iframe')).contentWindow.localStorage.token = `"${{token}}"`;
            }}, 10);
            setTimeout(() => location.reload(), 200);
            """
            driver.execute_script(login_script)
            time.sleep(0.2)
            
            if not fast_login_check(driver, max_time=10):
                rizzler_save(raw_line, success=False)
                stats["failed"] += 1
                elapsed = time.time() - start_time
                print(f"{Fore.RED}[+] Trial Triggering Failed - {Fore.CYAN}{token[:10]}**** {Fore.RED}({elapsed:.1f}s)")
                continue
            
            time.sleep(0.03)
            
            settings = None
            for attempt in range(3):
                settings = speed_wait(driver, "//button[@aria-label='User Settings'] | //div[@aria-label='User Settings'] | //*[contains(@class, 'userSettings')]", timeout=5)
                if settings:
                    break
                time.sleep(0.2)
            
            if not settings:
                raise Exception("Settings not found")
            fast_click(driver, settings)
            time.sleep(0.03)
            
            nitro_selectors = [
                "//div[contains(text(), 'Nitro')] | //*[@aria-label='Nitro'] | //div[@role='tab'][contains(text(), 'Nitro')]",
                "//div[contains(@class, 'premiumTab') or contains(@class, 'nitro')]",
                "//div[@role='tab' and contains(., 'Nitro')]",
                "//div[contains(@class, 'tabBarItem') and contains(., 'Nitro')]"
            ]
            
            nitro = None
            for attempt in range(3):
                for selector in nitro_selectors:
                    nitro = speed_wait(driver, selector, timeout=3)
                    if nitro:
                        break
                if nitro:
                    break
                time.sleep(0.2)
            
            if not nitro:
                raise Exception("Nitro tab not found")
            fast_click(driver, nitro)
            time.sleep(0.03)
            
            subscribe_selectors = [
                "//button[.//span[text()='Subscribe']]",
                "//button[contains(text(), 'Subscribe')]",
                "//button[@aria-label='Subscribe to Nitro']",
                "//button[contains(@class, 'subscribe') or contains(@class, 'premiumCTA')]",
                "//button[contains(@class, 'button') and contains(., 'Subscribe')]"
            ]
            
            subscribe = None
            for attempt in range(3):
                for selector in subscribe_selectors:
                    subscribe = speed_wait(driver, selector, timeout=5)
                    if subscribe:
                        break
                if subscribe:
                    break
                time.sleep(0.2)
                    
            if not subscribe:
                raise Exception("Subscribe not found")
            fast_click(driver, subscribe)
            time.sleep(0.03)
            
            plan_selectors = [
                "//div[contains(@class, 'tier2MarketingCard')]",
                "//div[contains(@class, 'card_ac86f6')]", 
                "//*[contains(@class, 'tier2')]",
                "//div[contains(@class, 'premiumTier') and contains(., 'Boost')]",
                "//div[@role='button' and contains(@class, 'card')]"
            ]
            
            plan = None
            for attempt in range(3):
                for selector in plan_selectors:
                    plan = speed_wait(driver, selector, timeout=3)
                    if plan:
                        break
                if plan:
                    break
                time.sleep(0.2)
            
            if not plan:
                raise Exception("Plan not found")
            fast_click(driver, plan)
            time.sleep(0.02)
            
            monthly = None
            for attempt in range(3):
                monthly = speed_wait(driver, "//div[contains(@class,'planOptionInterval') and text()='Monthly']", timeout=3)
                if monthly:
                    break
                time.sleep(0.2)
            
            if monthly:
                fast_click(driver, monthly)
                time.sleep(0.02)
            
            select_selectors = [
                "//span[text()='Select']/ancestor::button",
                "//button[contains(text(), 'Select')]",
                "//button[contains(@class, 'select') or contains(@class, 'button') and contains(., 'Select')]",
                "//button[@type='button' and contains(., 'Select')]"
            ]
            
            select = None
            for attempt in range(3):
                for selector in select_selectors:
                    select = speed_wait(driver, selector, timeout=5)
                    if select:
                        break
                if select:
                    break
                time.sleep(0.2)
            
            if not select:
                raise Exception("Select not found")
            fast_click(driver, select)
            time.sleep(0.03)
            
            card_selectors = [
                "//span[text()='Card']/ancestor::button",
                "//button[contains(text(), 'Card')]",
                "//button[contains(@class, 'payment') and contains(., 'Card')]"
            ]
            
            card = None
            for attempt in range(3):
                for selector in card_selectors:
                    card = speed_wait(driver, selector, timeout=5)
                    if card:
                        break
                if card:
                    break
                time.sleep(0.2)
            
            if not card:
                raise Exception("Card not found")
            fast_click(driver, card)
            
            cc_success = fast_card_filling(driver)
            if not cc_success:
                raise Exception("Card filling failed")
            
            for attempt in range(2):
                try:
                    name_field = driver.find_element(By.NAME, "name")
                    name_field.clear()
                    time.sleep(0.03)
                    name_field.send_keys("utkie")
                    if name_field.get_attribute('value').lower().strip() == "utkie":
                        break
                except:
                    if attempt < 1:
                        time.sleep(0.05)
            
            time.sleep(0.05)
            
            next_btn_selectors = [
                "//button[.//span[text()='Next']]",
                "//button[contains(@class, 'button') and contains(., 'Next') and not(contains(@class, 'lookBlank'))]",
                "//button[@type='submit' and contains(., 'Next')]",
                "//button[contains(., 'Next') and not(contains(., 'theme')) and not(contains(., 'Theme'))]",
                "//button[contains(@class, 'next') or contains(@class, 'continue')]"
            ]
            
            next_btn = None
            for attempt in range(3):
                for selector in next_btn_selectors:
                    next_btn = speed_wait(driver, selector, timeout=5)
                    if next_btn:
                        break
                if next_btn:
                    break
                time.sleep(0.2)
                    
            if not next_btn:
                raise Exception("Next button not found")
            fast_click(driver, next_btn)
            time.sleep(0.3)
            
            address_fields = {
                "line1": fake_address["line1"],
                "city": fake_address["city"],
                "state": fake_address["state"],
                "postalCode": fake_address["postalCode"]
            }
            
            for field_name, value in address_fields.items():
                try:
                    field = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.NAME, field_name))
                    )
                    field.clear()
                    time.sleep(0.03)
                    field.send_keys(value)
                    time.sleep(0.03)
                except Exception as e:
                    pass
            
            time.sleep(0.1)
            
            final_next_selectors = [
                "//button[.//span[text()='Next']]",
                "//button[contains(@class, 'button') and contains(., 'Next') and not(contains(@class, 'lookBlank'))]",
                "//button[@type='submit' and (contains(., 'Next') or contains(., 'Confirm')) and not(contains(., 'Apply Theme'))]",
                "//button[contains(., 'Next') and not(contains(., 'theme')) and not(contains(., 'Theme')) and not(contains(., 'Apply'))]",
                "//button[contains(@class, 'submit') or contains(@class, 'confirm')]"
            ]
            
            final_next = None
            for attempt in range(3):
                for selector in final_next_selectors:
                    final_next = speed_wait(driver, selector, timeout=5)
                    if final_next:
                        try:
                            button_text = final_next.text.lower()
                            if "apply theme" not in button_text and "theme" not in button_text:
                                break
                            else:
                                final_next = None
                        except:
                            break
                if final_next:
                    break
                time.sleep(0.2)
            
            if final_next:
                fast_click(driver, final_next)
            
            time.sleep(1)
            
            rizzler_save(raw_line, success=True)
            stats["success"] += 1
            elapsed = time.time() - start_time
            print(f"{Fore.GREEN}[+] Trial Triggered: {Fore.CYAN}{token[:10]}**** {Fore.GREEN}({elapsed:.1f}s)")
        
        except Exception as e:
            rizzler_save(raw_line, success=False)
            stats["failed"] += 1
            elapsed = time.time() - start_time
            error_msg = str(e)[:30] + "..." if len(str(e)) > 30 else str(e)
            print(f"{Fore.RED}[+] Trial Triggering Failed - {Fore.CYAN}{token[:10]}**** {Fore.RED}({elapsed:.1f}s) - {error_msg}")
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
            time.sleep(0.05)

def fast_threads(thread_count, tokens, proxies, fake_address):
    token_queue = Queue()
    for token in tokens:
        token_queue.put(token)
    
    threads = []
    
    for i in range(min(thread_count, len(tokens))):
        t = threading.Thread(
            target=fast_worker,
            args=(i+1, token_queue, proxies, fake_address),
            daemon=True
        )
        t.start()
        threads.append(t)
        time.sleep(0.1)
    
    for t in threads:
        t.join()

def main():
    try:
        cleanup_chrome_processes()
        
        thread_count = rizzler_config()
        tokens_file, success_file, failed_file, invalid_file, proxies_file, fake_address = rizzler_files()
        tokens = rizzler_tokens(tokens_file)
        proxies = rizzler_proxies(proxies_file)
        
        start_time = time.time()
        fast_threads(thread_count, tokens, proxies, fake_address)
        elapsed = time.time() - start_time
        
        try:
            with open(success_file, 'r') as f:
                success_count = sum(1 for line in f if line.strip())
        except:
            success_count = 0
            
        try:
            with open(failed_file, 'r') as f:
                failed_count = sum(1 for line in f if line.strip())
        except:
            failed_count = 0
        
        print(f"{Fore.GREEN}[+] Success: {success_count} tokens")
        print(f"{Fore.RED}[+] Failed: {failed_count} tokens")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Stopped by user")
        cleanup_chrome_processes()
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {e}")
        logger.error(f"Main execution error: {e}")
        cleanup_chrome_processes()
    
    print(f"\n{Fore.CYAN}Made by Your Love : rizzler.py")
    input(f"{Fore.CYAN}Press Enter to exit...")

if __name__ == "__main__":
    main()