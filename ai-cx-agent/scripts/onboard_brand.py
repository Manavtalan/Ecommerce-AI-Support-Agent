#!/usr/bin/env python3
"""
Brand Onboarding Wizard
Interactive CLI for adding new brands to the platform
"""

import os
import sys
import yaml
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.brands.registry import get_brand_registry


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(step_num, text):
    """Print step header"""
    print(f"\n{'─' * 70}")
    print(f"STEP {step_num}: {text}")
    print(f"{'─' * 70}\n")


def get_input(prompt, default=None, required=True):
    """Get user input with optional default"""
    if default:
        prompt = f"{prompt} [{default}]"
    
    while True:
        value = input(f"{prompt}: ").strip()
        
        if not value and default:
            return default
        
        if not value and required:
            print("⚠️  This field is required. Please enter a value.")
            continue
        
        return value


def select_from_list(prompt, options):
    """Let user select from a list of options"""
    print(f"\n{prompt}")
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    
    while True:
        try:
            choice = int(input("\nSelect option (number): "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            print(f"⚠️  Please enter a number between 1 and {len(options)}")
        except ValueError:
            print("⚠️  Please enter a valid number")


def confirm(prompt):
    """Get yes/no confirmation"""
    while True:
        response = input(f"{prompt} (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False
        print("⚠️  Please enter 'y' or 'n'")


def onboard_brand():
    """Main onboarding flow"""
    
    print_header("🚀 BRAND ONBOARDING WIZARD")
    print("Welcome! Let's add a new brand to the platform.")
    print("This will take about 5-10 minutes.\n")
    
    if not confirm("Ready to start?"):
        print("Onboarding cancelled.")
        return
    
    brand_config = {}
    
    # ========================================
    # STEP 1: BASIC INFORMATION
    # ========================================
    print_step(1, "Basic Information")
    
    brand_config['brand_id'] = get_input(
        "Brand ID (lowercase, no spaces, e.g., 'acmecorp')",
        required=True
    ).lower().replace(' ', '')
    
    # Check if brand already exists
    registry = get_brand_registry()
    if registry.validate_brand_id(brand_config['brand_id']):
        print(f"\n❌ Brand '{brand_config['brand_id']}' already exists!")
        if not confirm("Overwrite existing brand?"):
            print("Onboarding cancelled.")
            return
    
    brand_config['name'] = get_input("Brand name (display name)", required=True)
    
    brand_config['industry'] = select_from_list(
        "Select industry:",
        ["fashion", "technology", "food_health", "beauty", "home_decor", "general"]
    )
    
    brand_config['domain'] = get_input(
        "Brand domain (e.g., 'example.com')",
        default=f"{brand_config['brand_id']}.com"
    )
    
    brand_config['active'] = True
    
    print(f"\n✅ Basic info captured for {brand_config['name']}")
    
    # ========================================
    # STEP 2: VOICE CONFIGURATION
    # ========================================
    print_step(2, "Voice & Personality Configuration")
    
    brand_config['voice'] = {}
    
    # Tone
    tone_options = {
        "friendly_professional": "Friendly yet professional (recommended for most brands)",
        "professional_technical": "Formal and technical (B2B, tech products)",
        "warm_health_focused": "Warm and caring (health, wellness, food)",
        "casual": "Very casual and conversational (youth brands)",
        "formal": "Highly formal (luxury, legal, finance)"
    }
    
    print("\nSelect brand tone:")
    for i, (key, desc) in enumerate(tone_options.items(), 1):
        print(f"  {i}. {key}: {desc}")
    
    tone_choice = int(get_input("Select tone (number)", default="1"))
    brand_config['voice']['tone'] = list(tone_options.keys())[tone_choice - 1]
    
    # Formality
    brand_config['voice']['formality'] = select_from_list(
        "Select formality level:",
        ["casual", "casual_warm", "neutral", "formal"]
    )
    
    # Emoji usage
    brand_config['voice']['emoji_usage'] = select_from_list(
        "Emoji usage preference:",
        ["none", "minimal", "moderate", "frequent"]
    )
    
    # Signature phrases
    print("\nEnter 3-5 signature phrases your brand likes to use:")
    print("(Press Enter on empty line to finish)")
    
    signature_phrases = []
    for i in range(1, 6):
        phrase = input(f"  Phrase {i}: ").strip()
        if not phrase:
            break
        signature_phrases.append(phrase)
    
    brand_config['voice']['signature_phrases'] = signature_phrases or [
        "We're here to help",
        "Let us know if you need anything"
    ]
    
    # Forbidden phrases
    print("\nEnter phrases to AVOID (optional):")
    print("(Press Enter on empty line to finish)")
    
    forbidden_phrases = []
    for i in range(1, 6):
        phrase = input(f"  Avoid {i}: ").strip()
        if not phrase:
            break
        forbidden_phrases.append(phrase)
    
    brand_config['voice']['forbidden_phrases'] = forbidden_phrases
    
    # Emoji preferences (if using emojis)
    if brand_config['voice']['emoji_usage'] not in ['none', 'minimal']:
        print("\nEmoji preferences (optional, press Enter to skip):")
        brand_config['voice']['emoji_preferences'] = {
            'greeting': get_input("Greeting emoji", default="👋", required=False),
            'positive': get_input("Positive emoji", default="✨", required=False),
            'help': get_input("Help emoji", default="💡", required=False),
        }
    else:
        brand_config['voice']['emoji_preferences'] = {}
    
    print(f"\n✅ Voice configuration complete")
    
    # ========================================
    # STEP 3: POLICY CONFIGURATION
    # ========================================
    print_step(3, "Policy Configuration")
    
    brand_config['policies'] = {}
    
    brand_config['policies']['return_window_days'] = int(get_input(
        "Return window (days)",
        default="30"
    ))
    
    brand_config['policies']['free_shipping_threshold'] = int(get_input(
        "Free shipping threshold (₹)",
        default="999"
    ))
    
    brand_config['policies']['cod_available'] = confirm(
        "Cash on Delivery (COD) available?"
    )
    
    brand_config['policies']['international_shipping'] = confirm(
        "International shipping available?"
    )
    
    print(f"\n✅ Policy configuration complete")
    
    # ========================================
    # STEP 4: INTEGRATION SETUP
    # ========================================
    print_step(4, "Integration Setup")
    
    brand_config['integrations'] = {}
    
    # Shopify
    print("\n--- Shopify Integration ---")
    if confirm("Connect Shopify store?"):
        brand_config['integrations']['shopify'] = {
            'enabled': True,
            'store_url': get_input("Shopify store URL (e.g., 'store.myshopify.com')")
        }
    else:
        brand_config['integrations']['shopify'] = {'enabled': False}
    
    # WhatsApp
    print("\n--- WhatsApp Business API ---")
    if confirm("Connect WhatsApp Business?"):
        brand_config['integrations']['whatsapp'] = {
            'enabled': True,
            'business_number': get_input("WhatsApp business number")
        }
    else:
        brand_config['integrations']['whatsapp'] = {'enabled': False}
    
    # Email
    print("\n--- Email Support ---")
    if confirm("Enable email support?"):
        brand_config['integrations']['email'] = {
            'enabled': True,
            'smtp_host': get_input("SMTP host (optional)", required=False)
        }
    else:
        brand_config['integrations']['email'] = {'enabled': False}
    
    print(f"\n✅ Integration setup complete")
    
    # ========================================
    # STEP 5: BUSINESS INFORMATION
    # ========================================
    print_step(5, "Business Information")
    
    brand_config['business_hours'] = {
        'timezone': get_input("Timezone", default="Asia/Kolkata"),
        'support_hours': get_input("Support hours", default="9 AM - 6 PM"),
        'days': get_input("Support days", default="Monday - Saturday")
    }
    
    brand_config['metadata'] = {
        'created_at': '2026-02-01',
        'primary_contact': get_input("Primary contact email"),
        'target_audience': get_input("Target audience", required=False)
    }
    
    print(f"\n✅ Business information complete")
    
    # ========================================
    # STEP 6: REVIEW & SAVE
    # ========================================
    print_step(6, "Review & Save")
    
    print("\n📋 BRAND CONFIGURATION SUMMARY:")
    print(f"  Brand: {brand_config['name']} ({brand_config['brand_id']})")
    print(f"  Industry: {brand_config['industry']}")
    print(f"  Voice: {brand_config['voice']['tone']}, {brand_config['voice']['emoji_usage']} emojis")
    print(f"  Return Window: {brand_config['policies']['return_window_days']} days")
    print(f"  Free Shipping: ₹{brand_config['policies']['free_shipping_threshold']}")
    print(f"  Shopify: {'✅ Connected' if brand_config['integrations']['shopify']['enabled'] else '❌ Not connected'}")
    print(f"  WhatsApp: {'✅ Connected' if brand_config['integrations']['whatsapp']['enabled'] else '❌ Not connected'}")
    
    if not confirm("\nSave this configuration?"):
        print("Onboarding cancelled.")
        return
    
    # Create brand directory
    brand_dir = Path(f"test_data/brands/{brand_config['brand_id']}")
    brand_dir.mkdir(parents=True, exist_ok=True)
    
    # Create policies directory
    policies_dir = brand_dir / "policies"
    policies_dir.mkdir(exist_ok=True)
    
    # Save configuration
    config_file = brand_dir / "brand_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(brand_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"\n✅ Brand configuration saved to: {config_file}")
    
    # ========================================
    # STEP 7: NEXT STEPS
    # ========================================
    print_step(7, "Next Steps")
    
    print(f"""
✅ Brand '{brand_config['name']}' successfully onboarded!

📁 Created:
  • {config_file}
  • {policies_dir}/

📋 TODO:
  1. Upload policy documents to: {policies_dir}/
     - return_policy.md
     - shipping_policy.md
     - refund_policy.md
     - cancellation_policy.md
  
  2. Run policy embedding:
     python scripts/embed_policies.py {brand_config['brand_id']}
  
  3. Test the brand:
     python scripts/test_brand.py {brand_config['brand_id']}
  
  4. Start using:
     from core.orchestrator import ConversationOrchestrator
     agent = ConversationOrchestrator(brand_id='{brand_config['brand_id']}')

🎉 You're all set!
""")


if __name__ == "__main__":
    try:
        onboard_brand()
    except KeyboardInterrupt:
        print("\n\n⚠️  Onboarding cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
