# Amazon.in Price Tracker

This is a robust tracker that:
- Watches Amazon.in product pages.
- **Checks Prices & Stock Status**: Uses Selenium (headless Chrome) to reliably scrape data without getting blocked.
- **Notifications**: Sends Email alerts when Price <= Threshold AND Product is In Stock.

## Quick start

1. **Setup Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Products**:
   Use the helper script to easily add or remove products:
   ```bash
   python3 add_products.py
   ```
   Follow the interactive prompts to add the product name, URL, and threshold price.
   
   Alternatively, you can manually edit `products.json`.

3. **Configure Notifications**:
   Copy the example environment file and fill in your details:
   ```bash
   cp .env.example .env
   # Edit .env with your SMTP credentials
   ```

4. **Run**:
   ```bash
   python3 tracker.py
   ```

## Tools

- `tracker.py`: Main script. Runs in a loop (default 30 min interval).
- `add_products.py`: Interactive script to add or remove products.
- `products.json`: List of products to track.
- `.env`: Environment variables for email configuration.

## Requirements
- Google Chrome installed.
- `chromedriver` (usually handled automatically by Selenium).

## Notification Setup Guide

### Email (Gmail Example)
1. Go to your Google Account > Security.
2. Enable **2-Step Verification**.
3. Search for **App Passwords**.
4. Create a new App Password (custom name: "Price Tracker").
5. Add the generated password to your `.env` file along with your email:
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   TO_EMAIL=recipient@example.com
   ```

