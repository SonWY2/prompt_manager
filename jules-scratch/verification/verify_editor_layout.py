import time
from playwright.sync_api import sync_playwright, Page, expect

def verify_editor_layout(page: Page):
    """
    This test navigates to the prompt editor with pre-existing data
    and takes a screenshot.
    """
    # 1. Arrange: Go to the application URL.
    page.goto("http://localhost:3030", timeout=60000)

    # 2. Act: Select the pre-existing task and version.
    task_name = "Test Task for Screenshot"

    # Give the page time to load the tasks
    time.sleep(5)

    # DEBUG: Print the page content to see what's rendered
    print("--- PAGE CONTENT ---")
    print(page.content())
    print("--- END PAGE CONTENT ---")

    task_item = page.get_by_text(task_name)
    expect(task_item).to_be_visible(timeout=10000)
    task_item.click()

    # Select the version.
    version_name = "Version 1"
    version_item = page.get_by_text(version_name)
    expect(version_item).to_be_visible()
    version_item.click()

    # 3. Assert: Check if the main prompt editor area is visible
    main_prompt_heading = page.get_by_text("💬 Main Prompt")
    expect(main_prompt_heading).to_be_visible()

    # Give a moment for UI to settle before screenshot
    time.sleep(2)

    # 4. Screenshot: Capture the final result for visual verification.
    page.screenshot(path="jules-scratch/verification/verification.png")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        verify_editor_layout(page)
        browser.close()

if __name__ == "__main__":
    main()
