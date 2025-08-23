from playwright.sync_api import sync_playwright, expect

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 1. Navigate to the application
            page.goto("http://localhost:3030/")

            # 2. Create a new task
            page.get_by_role("button", name="New Task").click()
            page.get_by_placeholder("Enter a task name...").fill("Test Task")
            page.get_by_role("button", name="Create").click()

            # Wait for the new task to appear and be selected
            expect(page.get_by_text("Test Task").first).to_be_visible()
            page.get_by_text("Test Task").first.click()

            # 3. Create a new version with a description and system prompt
            page.get_by_placeholder("Describe the purpose and usage of this prompt...").fill("Test Description")
            page.get_by_placeholder("Define AI role and instructions...").fill("Test System Prompt")
            page.get_by_placeholder("Enter prompt... (Use {{variable_name}} for variables)").fill("Test Prompt Content")

            # 4. Save the new version
            page.get_by_role("button", name="💾 Save").click()
            page.wait_for_timeout(1000) # Wait for UI to update

            page.screenshot(path="jules-scratch/verification/before_final_verification.png")

            # 5. Verify the content was saved
            expect(page.get_by_text("This is a test description.")).to_be_visible()
            expect(page.get_by_text("You are a helpful test assistant.")).to_be_visible()
            expect(page.get_by_text("This is the test prompt content.")).to_be_visible()

            # 6. Update the content
            page.locator('textarea[placeholder="Describe the purpose and usage of this prompt..."]').fill("This is an updated test description.")
            page.locator('textarea[placeholder="Define AI role and instructions..."]').fill("You are an updated helpful test assistant.")
            page.locator('textarea[placeholder="Enter prompt... (Use {{variable_name}} for variables)"]').fill("This is the updated test prompt content.")

            # 7. Save the updated version
            page.get_by_role("button", name="💾 Save").click()

            # 8. Verify the updated content was saved
            expect(page.get_by_text("This is an updated test description.")).to_be_visible()
            expect(page.get_by_text("You are an updated helpful test assistant.")).to_be_visible()
            expect(page.get_by_text("This is the updated test prompt content.")).to_be_visible()

            # 7. Take a screenshot
            page.screenshot(path="jules-scratch/verification/verification.png")

            print("Verification script ran successfully.")

        except Exception as e:
            print(f"An error occurred: {e}")
            page.screenshot(path="jules-scratch/verification/error.png")

        finally:
            browser.close()

if __name__ == "__main__":
    run_verification()
