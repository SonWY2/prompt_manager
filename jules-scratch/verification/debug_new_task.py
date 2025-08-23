from playwright.sync_api import sync_playwright

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto("http://localhost:3030/")
            page.get_by_role("button", name="New Task").click()
            page.screenshot(path="jules-scratch/verification/after_new_task_click.png")
            print("Screenshot taken after clicking 'New Task'.")

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            browser.close()

if __name__ == "__main__":
    run_verification()
