import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { expect, test } from "@playwright/test";

import {
  createApiContext,
  createKnowledgeBase,
  deleteKnowledgeBase,
  ensureUser,
  loginByApi,
  uniqueValue,
  type E2ECredentials,
} from "./utils/e2e-api";

const fixturesDir = path.join(path.dirname(fileURLToPath(import.meta.url)), "fixtures");
const v1Buffer = readFileSync(path.join(fixturesDir, "buyma-e2e-v1.txt"));
const v2Buffer = readFileSync(path.join(fixturesDir, "buyma-e2e-v2.txt"));

test.describe.configure({ mode: "serial" });

test("Login to restore flow", async ({ page }) => {
  const api = await createApiContext();
  let accessToken: string | null = null;
  let knowledgeBaseId: string | null = null;

  try {
    const credentials: E2ECredentials = await ensureUser(
      api,
      process.env.E2E_ADMIN_EMAIL,
      process.env.E2E_ADMIN_PASSWORD,
      "e2e-admin",
    );
    const token = await loginByApi(api, credentials);
    accessToken = token.access_token;

    const kb = await createKnowledgeBase(api, accessToken, uniqueValue("e2e-kb"));
    knowledgeBaseId = kb.id;

    await page.goto("/login");
    await expect(page).toHaveURL(/\/login$/);

    await page.getByLabel("メールアドレス").fill(credentials.email);
    await page.getByLabel("パスワード").fill(credentials.password);
    await page.getByRole("button", { name: "ログイン" }).click();

    await expect(page).toHaveURL(/\/knowledge-bases$/);
    await expect(page.getByRole("heading", { name: "ナレッジベース" })).toBeVisible();
    const knowledgeBaseCard = page
      .getByRole("heading", { name: kb.name, exact: true })
      .locator("xpath=ancestor::article");
    await expect(knowledgeBaseCard).toBeVisible();

    await knowledgeBaseCard.getByRole("link", { name: "詳細を見る" }).click();
    await expect(page).toHaveURL(new RegExp(`/knowledge-bases/${knowledgeBaseId}$`));
    await expect(page.getByRole("heading", { name: kb.name })).toBeVisible();
    await expect(page.getByRole("heading", { name: "ドキュメント", exact: true })).toBeVisible();
    await expect(page.getByText("最新ドキュメント", { exact: true })).toBeVisible();

    await page.getByRole("link", { name: "ドキュメントを開く" }).click();
    await expect(page).toHaveURL(
      new RegExp(`/knowledge-bases/${knowledgeBaseId}/documents`),
    );
    await expect(
      page.getByRole("heading", { name: "ドキュメント", exact: true }),
    ).toBeVisible();

    await uploadDocument(page, v1Buffer, "buyma-e2e.txt");

    const desktopTable = page.locator(".documents-table-desktop");
    const latestRow = desktopTable.locator("tbody tr").first();

    await expect(latestRow).toContainText("buyma-e2e.txt");
    await expect(latestRow).toContainText(/処理待ち|処理中|準備完了/);
    await expect
      .poll(async () => (await latestRow.textContent()) ?? "", {
        timeout: 60_000,
      })
      .toMatch(/準備完了/);

    await uploadDocument(page, v2Buffer, "buyma-e2e.txt");

    await expect
      .poll(async () => (await latestRow.textContent()) ?? "", {
        timeout: 60_000,
      })
      .toMatch(/v2/);
    await expect(latestRow).toContainText("最新");
    await expect
      .poll(async () => (await latestRow.textContent()) ?? "", {
        timeout: 60_000,
      })
      .toMatch(/準備完了/);

    await latestRow.getByRole("link", { name: "詳細" }).click();

    await expect(page).toHaveURL(
      new RegExp(`/knowledge-bases/${knowledgeBaseId}/documents/`),
    );
    await expect(page.getByRole("heading", { name: /buyma-e2e/i })).toBeVisible();
    const overview = page
      .getByRole("heading", { name: "概要" })
      .locator("xpath=ancestor::div[contains(@class, 'panel')]");
    const overviewValues = overview.locator(".detail-row__value");
    await expect(overviewValues.getByText("buyma-e2e.txt", { exact: true })).toBeVisible();
    await expect(overviewValues.getByText("v2", { exact: true })).toBeVisible();
    await expect(overviewValues.getByText("最新", { exact: true })).toBeVisible();
    await expect(overviewValues.getByText("準備完了", { exact: true })).toBeVisible();

    const v2Card = page.locator(".version-item").filter({ hasText: "v2" }).first();
    const v1Card = page.locator(".version-item").filter({ hasText: "v1" }).first();

    await expect(v2Card).toContainText("最新");
    await expect(v1Card).toBeVisible();
    await expect(v2Card.getByRole("button", { name: "復元" })).toBeDisabled();
    await expect(v1Card.getByRole("button", { name: "差分" })).toBeEnabled();
    await expect(v1Card.getByRole("button", { name: "復元" })).toBeEnabled();

    await v1Card.getByRole("button", { name: "差分" }).click();
    await expect(page.getByRole("heading", { name: "バージョン差分" })).toBeVisible();
    await expect(page.getByText(/現在 v2.*比較対象 v1/)).toBeVisible();
    await expect(page.getByText(/追加\s*\d+/)).toBeVisible();
    await expect(page.getByText(/削除\s*\d+/)).toBeVisible();
    await expect
      .poll(() => page.locator(".diff-line").count(), { timeout: 10_000 })
      .toBeGreaterThan(0);

    await v1Card.getByRole("button", { name: "復元" }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toContainText("バージョン1を復元しますか？");
    await dialog.getByRole("button", { name: "キャンセル" }).click();
    await expect(dialog).toBeHidden();

    await v1Card.getByRole("button", { name: "復元" }).click();
    await expect(dialog).toContainText("バージョン1を復元しますか？");
    await dialog.getByRole("button", { name: "復元" }).click();

    await expect
      .poll(
        async () =>
          ((await page.locator(".version-item").first().textContent()) ?? "").replace(
            /\s+/g,
            " ",
          ),
        { timeout: 60_000 },
      )
      .toMatch(/v3\s*最新/);

    await expect
      .poll(
        async () => {
          await page.reload();
          await expect(
            page.getByRole("heading", { name: "バージョン履歴" }),
          ).toBeVisible();
          return (
            (await page.locator(".version-item").filter({ hasText: "v3" }).first().textContent()) ??
            ""
          ).replace(/\s+/g, " ");
        },
        { timeout: 60_000, intervals: [1_000, 2_000, 5_000] },
      )
      .toMatch(/準備完了/);

    const historyText = (
      await page.locator(".version-list").textContent()
    )?.replace(/\s+/g, " ");
    expect(historyText).toContain("v3");
    expect(historyText).toContain("v2");
    expect(historyText).toContain("v1");
  } finally {
    if (accessToken && knowledgeBaseId) {
      await deleteKnowledgeBase(api, accessToken, knowledgeBaseId);
    }
    await api.dispose();
  }
});

test("Direct access to another user's Knowledge Base shows not found", async ({
  page,
}) => {
  const api = await createApiContext();
  let ownerToken: string | null = null;
  let ownerKbId: string | null = null;

  try {
    const owner = await ensureUser(api, undefined, undefined, "e2e-owner");
    const viewer = await ensureUser(
      api,
      process.env.E2E_USER_EMAIL,
      process.env.E2E_USER_PASSWORD,
      "e2e-viewer",
    );

    ownerToken = (await loginByApi(api, owner)).access_token;
    const ownerKb = await createKnowledgeBase(
      api,
      ownerToken,
      uniqueValue("e2e-private-kb"),
    );
    ownerKbId = ownerKb.id;

    await page.goto("/login");
    await page.getByLabel("メールアドレス").fill(viewer.email);
    await page.getByLabel("パスワード").fill(viewer.password);
    await page.getByRole("button", { name: "ログイン" }).click();
    await expect(page).toHaveURL(/\/knowledge-bases$/);

    await page.goto(`/knowledge-bases/${ownerKbId}`);
    await expect(page.getByText("ナレッジベースが見つかりません")).toBeVisible();
  } finally {
    if (ownerToken && ownerKbId) {
      await deleteKnowledgeBase(api, ownerToken, ownerKbId);
    }
    await api.dispose();
  }
});

async function uploadDocument(
  page: import("@playwright/test").Page,
  buffer: Buffer,
  filename: string,
) {
  await page.getByRole("button", { name: "ドキュメントをアップロード" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await dialog.getByRole("combobox", { name: "埋め込みモデル" }).selectOption({ index: 1 });
  await dialog.locator('input[type="file"]').setInputFiles({
    name: filename,
    mimeType: "text/plain",
    buffer,
  });
  await expect(dialog.getByRole("button", { name: "アップロード", exact: true })).toBeEnabled();
  await dialog.getByRole("button", { name: "アップロード", exact: true }).click();
  await expect(dialog).toBeHidden();
}
