
def extract_price(soup):
    import re
    
    # Strategy 1: Standard CSS Selectors (Desktop & Mobile)
    selectors = [
        ".a-price .a-offscreen",
        "#priceblock_dealprice",
        "#priceblock_ourprice",
        "#priceblock_saleprice",
        ".a-color-price",
        "#corePrice_feature_div .a-offscreen",
        "#corePriceDisplay_mobile_feature_div .a-offscreen",
        "span.a-price span.a-offscreen" # Generic backup
    ]
    
    for sel in selectors:
        if el := soup.select_one(sel):
            text = el.get_text(strip=True)
            if re.search(r"\d", text): # Ensure it has numbers
                print(f"DEBUG: Found price via Selector '{sel}': {text}")
                return text

    # Strategy 2: Search for specific data structures (Metadata)
    # Often Amazon puts price in hidden inputs or data attributes
    try:
        # Example: <input type="hidden" id="twister-plus-price-data-price" value="109900.0" ...>
        # Or similar hidden price inputs
        hidden_price = soup.select_one("#twister-plus-price-data-price")
        if hidden_price and hidden_price.get("value"):
             val = hidden_price.get("value")
             print(f"DEBUG: Found price via Hidden Input: {val}")
             return val
    except: 
        pass

    # Strategy 3: Regex on Layout Text (Fallback)
    # Look for currency symbol followed by numbers, but try to be specific to price context if possible.
    # We search the whole text, but maybe prioritising the 'center' column or similar would be better.
    # For now, simple regex fallback as requested.
    text_content = soup.get_text()
    # Matches ₹ 1,09,900.00 or ₹109900 etc.
    match = re.search(r"[₹Rs\.]\s?[\d,]+(?:\.\d+)?", text_content)
    if match:
        print(f"DEBUG: Found price via Regex: {match.group(0)}")
        return match.group(0)
        
    return None
