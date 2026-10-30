import { expect, test } from "@playwright/test";

test("user configures and removes a private Slack notification channel", async ({ page }) => {
  test.skip(!process.env.E2E_ADMIN_EMAIL || !process.env.E2E_ADMIN_PASSWORD, "E2E admin credentials are required.");
  await page.goto("/login");
  await page.getByLabel("メールアドレス").fill(process.env.E2E_ADMIN_EMAIL!);
  await page.getByLabel("パスワード").fill(process.env.E2E_ADMIN_PASSWORD!);
  await page.getByRole("button", { name: "ログイン" }).click();
  await page.getByRole("link", { name: "通知設定", exact: true }).click();
  await expect(page).toHaveURL(/\/notification-settings$/);
  const form = page.getByRole("form", { name: "Slack通知設定" });
  await form.getByLabel("通知先名").fill(`E2E Slack ${Date.now()}`);
  await form.getByLabel("有効").check();
  await form.getByLabel("仕入先ポリシーレビューの変更").check();
  const fake = "https://hooks.slack.com/services/e2e/test/not-a-real-secret";
  const webhookInput = form.getByRole("textbox", {
    name: "Slack Webhook URL",
    exact: true,
  });
  if (!(await webhookInput.isVisible())) {
    await form.getByRole("button", { name: "Webhookを変更", exact: true }).click();
  }
  await expect(webhookInput).toBeVisible();
  await webhookInput.fill(fake);
  const [saved] = await Promise.all([page.waitForResponse(r => r.url().includes("/notification-channels/slack") && r.request().method() === "PUT"), form.getByRole("button", { name: "設定を保存" }).click()]);
  expect(saved.ok()).toBeTruthy();
  await expect(form.getByText("設定済み", { exact: true })).toBeVisible();
  await expect(page.getByText(fake)).toHaveCount(0);
  page.once("dialog", dialog => dialog.accept());
  const [removed] = await Promise.all([page.waitForResponse(r => r.url().includes("/notification-channels/slack") && r.request().method() === "DELETE"), form.getByRole("button", { name: "Slack連携を解除" }).click()]);
  expect(removed.ok()).toBeTruthy();
  await expect(form.getByText("未設定", { exact: true })).toBeVisible();
});
