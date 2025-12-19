#!/usr/bin/env python3

import time, json, os, re, sys, traceback
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import smtplib
from email.mime.text import MIMEText

def send_email(smtp_server, smtp_port, smtp_user, smtp_password, to_email, subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    try:
        s = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        s.starttls()
        s.login(smtp_user, smtp_password)
        s.sendmail(smtp_user, [to_email], msg.as_string())
        s.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ---- Amazon price & stock parsing ----

def get_headless_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36")
    # You might need to specify path if chromedriver is not in PATH
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def parse_price_and_stock(driver, url):
    """
    Returns (price_float, in_stock_bool)
    price_float is None if not found.
    in_stock_bool is True if stock detected or strictly not "unavailable".
    """
    try:
        driver.get(url)
        # Give it a moment to render JS
        time.sleep(3) 
        
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # 1. Parse Price
        selectors = [
            ".a-price .a-offscreen",
            "#priceblock_dealprice",
            "#priceblock_ourprice",
            "#priceblock_saleprice",
            ".a-color-price"
        ]
        price_text = None
        for sel in selectors:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                price_text = el.get_text(strip=True)
                break
        
        # Fallback regex
        if not price_text:
            text = soup.get_text()
            # Look for ₹ followed by numbers
            m = re.search(r"₹\s?[\d,]+(?:\.\d+)?", text)
            if m:
                price_text = m.group(0)

        price = None
        if price_text:
            cleaned = re.sub(r"[^\d.]", "", price_text)
            try:
                price = float(cleaned)
            except:
                price = None
        
        # 2. Parse Stock
        # "Currently unavailable" is a strong signal for NO stock.
        # "In stock" or "Only X left" is YES.
        
        text_lower = soup.get_text().lower()
        if "currently unavailable" in text_lower:
            in_stock = False
        else:
            # Default to True if we found a price, unless specific out-of-stock markers appear
            # Some pages show price but "Temporary out of stock"
            if "temporarily out of stock" in text_lower:
                in_stock = False
            else:
                in_stock = True
                
        return price, in_stock

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None, False

# ---- Optional Selenium checkout helper ----


# ---- Main loop ----
def run_tracker(single_run=False):
    products_path = "products.json"

    print(f"Reading products from {products_path}")
    if not os.path.exists(products_path):
        print(f"Products file not found: {products_path}")
        return

    with open(products_path, "r", encoding="utf-8") as f:
        prod_cfg = json.load(f)

    # Determine notification config from Environment Variables
    # No more file-based email config.
    notify_cfg = {
        "email": {
            "smtp_server": os.environ.get("SMTP_SERVER"),
            "smtp_port": int(os.environ.get("SMTP_PORT", 587)),
            "smtp_user": os.environ.get("SMTP_USER"),
            "smtp_password": os.environ.get("SMTP_PASSWORD"),
            "to_email": os.environ.get("TO_EMAIL") or os.environ.get("SMTP_USER")
        },
        "notification_method": "email"
    }

    interval = prod_cfg.get("check_interval_seconds", 1800)
    seen_hits = {}  # url -> last_price 

    print("Starting tracker (Selenium Mode). Press Ctrl+C to stop.")
    
    driver = None

    try:
        while True:
            # Reload products dynamically?
            if not single_run:
                try:
                    with open(products_path, "r", encoding="utf-8") as f:
                        prod_cfg = json.load(f)
                except Exception as e:
                    print(f"Error reloading config: {e}")
            
            products = prod_cfg.get("products", [])
            if not products:
                 print(f"[{datetime.now():%H:%M:%S}] No products found config.")
            # Always email for now or check os.environ?
            # Let's keep it simple fixed to email since we are hardcoding notify_cfg above
            method = notify_cfg.get("notification_method", "email")
            
            if not driver:
                try:
                    driver = get_headless_driver()
                except Exception as e:
                    print("Failed to start Selenium driver:", e)
                    time.sleep(60)
                    continue

            for p in products:
                name = p.get("name", "Unknown")
                url = p.get("url")
                thr = p.get("threshold_inr")
                
                if not url or thr is None:
                    continue

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{now}] Checking {name}...")

                price, in_stock = parse_price_and_stock(driver, url)
                
                if price is None:
                    print(f"  -> Price not found.")
                    continue
                
                status_str = "In Stock" if in_stock else "Out of Stock"
                print(f"  -> ₹{price:.2f} ({status_str}) [Threshold: ₹{thr}]")

                key = url
                
                # Logic: Notify if Price <= Threshold AND In Stock
                if in_stock and price <= float(thr):
                    # Check if already notified
                    last_price = seen_hits.get(key)
                    
                    # If we haven't seen this low price, OR it went even lower
                    if last_price is None or price < last_price:
                        msg = f"PRICE ALERT: {name}\nPrice: ₹{price:.2f}\nThreshold: ₹{thr}\nStatus: {status_str}\n{url}"
                        
                        sent = False
                        if method == "email":
                            ec = notify_cfg.get("email", {})
                            sent = send_email(
                                ec.get("smtp_server"),
                                ec.get("smtp_port"),
                                ec.get("smtp_user"),
                                ec.get("smtp_password"),
                                ec.get("to_email"),
                                f"Price Alert: {name}",
                                msg
                            )
                        
                        if sent:
                            print(f"  -> Notification SENT.")
                            seen_hits[key] = price
                        else:
                            print(f"  -> Notification FAILED.")
                    else:
                        print(f"  -> Already notified at ₹{last_price}.")
                else:
                    if key in seen_hits and price > seen_hits[key]:
                        del seen_hits[key]
                        print("  -> Price rose, resetting alert.")

            # Sleep
            if single_run:
                print("Single run complete. Exiting.")
                break
            
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--single-run", action="store_true", help="Run once and exit (for cron jobs)")
    args = parser.parse_args()
    
    run_tracker(single_run=args.single_run)
