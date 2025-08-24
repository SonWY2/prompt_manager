import re
from playwright.sync_api import sync_playwright, Page, expect

def verify_llm_provider_form(page: Page):
    """
    This script verifies the new LLM Provider UI.
    1. Navigates to the app.
    2. Clicks the 'LLM Provider' link in the header.
    3. Clicks the 'Add New Endpoint' button.
    4. Verifies the 'Context Size' field is visible in the form.
    5. Takes a screenshot.
    """
    # 1. Navigate to the app
    page.goto("http://localhost:3030/")

    # 2. Click the 'LLM Provider' link
    llm_provider_link = page.get_by_text("LLM Provider")
    expect(llm_provider_link).to_be_visible()
    llm_provider_link.click()

    # 3. Wait for settings page and click 'Add New Endpoint'
    # Use a robust selector to find the button
    add_new_button = page.get_by_role("button", name=re.compile("새 엔드포인트 추가|Add New Endpoint", re.IGNORECASE))

    # Wait for the button to be visible before clicking
    expect(add_new_button).to_be_visible(timeout=10000)
    add_new_button.click()

    # 4. Verify the 'Context Size' field is visible
    # The label for the context size input
    context_size_label = page.get_by_label(re.compile("Context Size", re.IGNORECASE))
    expect(context_size_label).to_be_visible()

    # Also check for the placeholder text as an extra verification
    context_size_input = page.get_by_placeholder(re.compile("예: 4096, 8192", re.IGNORECASE))
    expect(context_size_input).to_be_visible()

    # 5. Take a screenshot
    page.screenshot(path="jules-scratch/verification/verification.png")

# Boilerplate to run the verification
if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_llm_provider_form(page)
            print("Verification script ran successfully.")
        except Exception as e:
            print(f"Verification script failed: {e}")
        finally:
            browser.close()
