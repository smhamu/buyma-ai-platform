import { expect, test } from "@playwright/test";

test("user configures and removes a private Slack notification channel",async({page})=>{
  test.skip(!process.env.E2E_ADMIN_EMAIL||!process.env.E2E_ADMIN_PASSWORD,"E2E admin credentials are required.");
  await page.goto("/login");await page.getByLabel("Email").fill(process.env.E2E_ADMIN_EMAIL!);await page.getByLabel("Password").fill(process.env.E2E_ADMIN_PASSWORD!);await page.getByRole("button",{name:"Login"}).click();
  await page.getByRole("link",{name:"Notification Settings",exact:true}).click();await expect(page).toHaveURL(/\/notification-settings$/);
  const form=page.getByRole("form",{name:"Slack notification settings"});
  test.skip((await form.getByText("Configured",{exact:true}).count())>0,"Dedicated E2E user already has a Slack integration; preserving it.");
  await form.getByLabel("Destination label").fill(`E2E Slack ${Date.now()}`);await form.getByLabel("Enabled").check();await form.getByLabel("Supplier Policy Review Changes").check();
  const fake="https://hooks.slack.com/services/e2e/test/not-a-real-secret";await form.getByLabel("Slack webhook URL").fill(fake);
  const [saved]=await Promise.all([page.waitForResponse(r=>r.url().includes("/notification-channels/slack")&&r.request().method()==="PUT"),form.getByRole("button",{name:"Save Settings"}).click()]);expect(saved.ok()).toBeTruthy();
  await expect(form.getByText("Configured",{exact:true})).toBeVisible();await expect(page.getByText(fake)).toHaveCount(0);
  page.once("dialog",dialog=>dialog.accept());const [removed]=await Promise.all([page.waitForResponse(r=>r.url().includes("/notification-channels/slack")&&r.request().method()==="DELETE"),form.getByRole("button",{name:"Remove Slack Integration"}).click()]);expect(removed.ok()).toBeTruthy();await expect(form.getByText("Not configured",{exact:true})).toBeVisible();
});
