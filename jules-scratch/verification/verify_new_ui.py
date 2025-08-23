from playwright.sync_api import sync_playwright, Page, expect

def run_verification(page: Page):
    """
    This script verifies the new collapsible sidebar and tabbed UI.
    """
    # 1. Navigate to the app
    page.goto("http://localhost:3030/")

    # 2. Check that the sidebar is visible
    sidebar = page.locator("aside.sidebar")
    expect(sidebar).to_be_visible(timeout=15000)

    # 3. Click the first task in the sidebar
    first_task_selector = "div.p-3.ml-6.rounded-lg.cursor-pointer"
    first_task = page.locator(first_task_selector).first
    expect(first_task).to_be_visible(timeout=20000)
    first_task.click()

    # 4. Verify that the "Prompt Editor" tab is active
    editor_tab = page.locator(".tab-button", has_text="Prompt Editor")
    expect(editor_tab).to_have_class("tab-button active")

    # 5. Click the "Result Viewer" tab and verify it becomes active
    result_tab = page.locator(".tab-button", has_text="Result Viewer")
    result_tab.click()
    expect(result_tab).to_have_class("tab-button active")
    expect(editor_tab).not_to_have_class("tab-button active")

    # 6. Click the collapse sidebar button
    collapse_button = page.get_by_title("Collapse sidebar")
    collapse_button.click()

    # 7. Verify the sidebar is no longer visible (or has 'collapsed' class)
    expect(sidebar).to_have_class("sidebar collapsed")

    # 8. Take a screenshot
    page.screenshot(path="jules-scratch/verification/verification.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        run_verification(page)
        browser.close()
