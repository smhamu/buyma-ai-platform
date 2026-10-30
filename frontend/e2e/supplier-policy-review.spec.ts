import { expect, test } from "@playwright/test";
import { createApiContext, loginByApi, uniqueValue, type E2ECredentials } from "./utils/e2e-api";
import { cleanupResearchData, findSupplier, type ResearchIds } from "./utils/research-api";

test("supplier policy review moves through all review states", async ({ page }) => {
  test.skip(!process.env.E2E_ADMIN_EMAIL || !process.env.E2E_ADMIN_PASSWORD, "E2E admin credentials are required.");
  const credentials: E2ECredentials = { email: process.env.E2E_ADMIN_EMAIL!, password: process.env.E2E_ADMIN_PASSWORD!, username: "e2e-admin" };
  const api = await createApiContext(); const ids: ResearchIds = {}; let token = ""; let originalSettings: Record<string, unknown> | null = null;
  const supplierName = uniqueValue("e2e-policy-review");
  try {
    token = (await loginByApi(api, credentials)).access_token;
    const headers = { Authorization: `Bearer ${token}` };
    const settingsResponse = await api.get("/supplier-policy-review/settings", { headers }); expect(settingsResponse.ok()).toBeTruthy();
    originalSettings = (await settingsResponse.json()).data;
    const settingsBody = { ...originalSettings, required_evidence_types: ["terms"], terms_max_age_days: 3650 }; delete settingsBody.id; delete settingsBody.user_id;
    expect((await api.put("/supplier-policy-review/settings", { headers, data: settingsBody })).ok()).toBeTruthy();

    await page.goto("/login"); await page.getByLabel("メールアドレス").fill(credentials.email); await page.getByLabel("パスワード").fill(credentials.password); await page.getByRole("button", { name: "ログイン" }).click();
    await page.getByRole("link", { name: "仕入先", exact: true }).click(); await page.getByRole("button", { name: "仕入先を追加" }).click();
    const createForm = page.getByRole("heading", { name: "仕入先を追加" }).locator("xpath=ancestor::form");
    await createForm.getByLabel("名称").fill(supplierName); await createForm.getByLabel("WebサイトURL").fill("https://e2e-policy-review.invalid"); await createForm.getByLabel("利用規約ステータス").selectOption("unknown");
    const [created] = await Promise.all([page.waitForResponse(r => r.url().includes("/suppliers") && r.request().method() === "POST"), createForm.getByRole("button", { name: "仕入先を保存" }).click()]); expect(created.ok()).toBeTruthy();
    const supplier = await findSupplier(api, token, supplierName); expect(supplier).toBeTruthy(); ids.supplierId = supplier!.id;

    await page.getByRole("link", { name: "ポリシーレビュー", exact: true }).click();
    const reviewRow = page.getByRole("row").filter({ hasText: supplierName }); await expect(reviewRow).toContainText("根拠未登録"); await reviewRow.getByRole("button", { name: "レビュー" }).click(); await page.getByRole("link", { name: "根拠履歴を開く" }).click();
    const evidencePanel = page.getByRole("region", { name: "ポリシー根拠" }); const evidenceForm = evidencePanel.getByRole("form", { name: "ポリシー根拠を追加" });
    await evidenceForm.getByLabel("根拠種別").selectOption("terms"); await evidenceForm.getByLabel("結果").selectOption("restricted"); await evidenceForm.getByLabel("確認日時").fill(new Date(Date.now() - 200 * 86400000).toISOString().slice(0, 16)); await evidenceForm.getByLabel("メモ").fill("E2E historical terms review.");
    const [evidenceResponse] = await Promise.all([page.waitForResponse(r => r.url().includes(`/suppliers/${ids.supplierId}/policy-evidence`) && r.request().method() === "POST"), evidenceForm.getByRole("button", { name: "根拠を追加" }).click()]); expect(evidenceResponse.ok()).toBeTruthy();
    await evidencePanel.getByRole("button", { name: "閉じる" }).click(); await page.getByRole("link", { name: "ポリシーレビュー", exact: true }).click();
    const inconsistentRow = page.getByRole("row").filter({ hasText: supplierName }); await expect(inconsistentRow).toContainText("不整合"); await inconsistentRow.getByRole("button", { name: "レビュー" }).click();
    await expect(page.getByRole("region", { name: "最近のレビュー変更履歴" })).toContainText("根拠未登録 → 不整合"); await page.getByRole("region", { name: "仕入先レビュー詳細" }).getByRole("button", { name: "閉じる" }).click();

    await page.getByRole("link", { name: "仕入先", exact: true }).click(); await page.goto("/suppliers?page_size=100"); const supplierRow = page.getByRole("row").filter({ hasText: supplierName }); await supplierRow.getByRole("button", { name: "編集" }).click();
    const editForm = page.getByRole("heading", { name: "仕入先を編集" }).locator("xpath=ancestor::form"); await editForm.getByLabel("利用規約ステータス").selectOption("restricted");
    const [updated] = await Promise.all([page.waitForResponse(r => r.url().includes(`/suppliers/${ids.supplierId}`) && r.request().method() === "PUT"), editForm.getByRole("button", { name: "仕入先を保存" }).click()]); expect(updated.ok()).toBeTruthy();
    await page.getByRole("link", { name: "ポリシーレビュー", exact: true }).click(); const recoveredRow = page.getByRole("row").filter({ hasText: supplierName }); await expect(recoveredRow).toContainText("最新"); await recoveredRow.getByRole("button", { name: "レビュー" }).click();
    await expect(page.getByRole("region", { name: "最近のレビュー変更履歴" })).toContainText("不整合 → 最新"); await page.getByRole("region", { name: "仕入先レビュー詳細" }).getByRole("button", { name: "閉じる" }).click();
    const reviewSettings = page.getByRole("region", { name: "レビュー設定" }); await reviewSettings.getByRole("spinbutton", { name: "利用規約の有効期間（日）" }).fill("90");
    const [settingsUpdated] = await Promise.all([page.waitForResponse(r => r.url().includes("/supplier-policy-review/settings") && r.request().method() === "PUT"), reviewSettings.getByRole("button", { name: "レビュー設定を保存" }).click()]); expect(settingsUpdated.ok()).toBeTruthy(); await expect(page.getByRole("row").filter({ hasText: supplierName })).toContainText("再確認期限超過");
  } finally {
    if (token && originalSettings) { const body = { ...originalSettings }; delete body.id; delete body.user_id; await api.put("/supplier-policy-review/settings", { headers: { Authorization: `Bearer ${token}` }, data: body }); }
    if (token) await cleanupResearchData(api, token, ids); await api.dispose();
  }
});
