import { expect, test } from "@playwright/test";

import {
  createApiContext,
  loginByApi,
  uniqueValue,
  type E2ECredentials,
} from "./utils/e2e-api";
import {
  cleanupIngestion,
  createIngestionBrand,
  createIngestionSupplier,
  findSources,
  getCandidate,
  getSource,
  type IngestionIds,
} from "./utils/research-ingestion-api";

test.describe.configure({ mode: "serial" });

test("admin ingests EU supplier research sources without external fetching", async ({
  page,
}) => {
  test.skip(
    !process.env.E2E_ADMIN_EMAIL || !process.env.E2E_ADMIN_PASSWORD,
    "E2E admin credentials are required.",
  );
  const credentials: E2ECredentials = {
    email: process.env.E2E_ADMIN_EMAIL!,
    password: process.env.E2E_ADMIN_PASSWORD!,
    username: "e2e-admin",
  };
  const api = await createApiContext();
  const ids: IngestionIds = { sourceIds: [] };
  const suffix = uniqueValue("ingestion").replace(/-/g, "_");
  const brandCode = `e2e_ingestion_${suffix}`.toLowerCase();
  const brandName = `E2E Ingestion Brand ${suffix}`;
  const supplierName = `E2E Ingestion Supplier ${suffix}`;
  const productName = `E2E Ingestion Product ${suffix}`;
  const domain = "example-e2e-shop.invalid";
  const manualUrl = `https://${domain}/products/item-001-${suffix}`;
  const csvUrl = `https://${domain}/products/item-002-${suffix}`;
  let token = "";
  try {
    token = (await loginByApi(api, credentials)).access_token;
    ids.brandId = (
      await createIngestionBrand(api, token, brandCode, brandName)
    ).id;
    const supplier = await createIngestionSupplier(
      api,
      token,
      ids.brandId,
      supplierName,
      `https://${domain}`,
    );
    ids.supplierId = supplier.id;
    expect(supplier).toMatchObject({
      country_code: "FR",
      default_currency: "EUR",
      ships_to_japan: true,
      ingestion_source_type: "url_manual",
      automated_fetch_enabled: false,
      terms_status: "allowed",
      robots_status: "allowed",
    });

    await page.goto("/login");
    await page.getByLabel("メールアドレス").fill(credentials.email);
    await page.getByLabel("パスワード").fill(credentials.password);
    await page.getByRole("button", { name: "ログイン" }).click();
    await expect(page).toHaveURL(/\/knowledge-bases$/);
    const ingestionLink = page.getByRole("link", {
      name: "リサーチ取込",
      exact: true,
    });
    await expect(ingestionLink).toBeVisible();
    await ingestionLink.click();
    await expect(page).toHaveURL(/\/research-ingestion$/);

    await page.getByRole("button", { name: "URLを追加" }).click();
    const urlForm = page.getByRole("form", { name: "URL登録フォーム" });
    const supplierSelect = urlForm.getByRole("combobox", {
      name: "仕入先",
      exact: true,
    });
    await supplierSelect.selectOption(ids.supplierId);
    await expect(
      urlForm.getByText(/手動URL.*自動取得: 無効/),
    ).toBeVisible();
    await urlForm.getByRole("textbox", { name: "商品URL" }).fill(manualUrl);
    const [manualResponse] = await Promise.all([
      page.waitForResponse(
        (r) =>
          r.url().includes("/research-ingestion/url") &&
          r.request().method() === "POST",
      ),
      urlForm.getByRole("button", { name: "URLを登録" }).click(),
    ]);
    expect(manualResponse.ok()).toBeTruthy();
    const manualRow = page
      .getByRole("row")
      .filter({ hasText: supplierName })
      .filter({ hasText: "url_manual" });
    await expect(manualRow).toBeVisible();
    await expect(manualRow).toContainText("pending");
    await expect(
      manualRow.getByRole("link", { name: "url_manual" }),
    ).toHaveAttribute("href", manualUrl);
    const manualSources = await findSources(api, token, "item-001");
    expect(manualSources).toHaveLength(1);
    ids.sourceIds.push(manualSources[0].id);
    const manualDetail = await getSource(api, token, manualSources[0].id);
    expect(manualDetail.processing_status).toBe("pending");
    expect(manualDetail.source_type).toBe("url_manual");
    expect(manualDetail.supplier_id).toBe(ids.supplierId);

    await page.getByRole("button", { name: "CSV取込" }).click();
    const csvForm = page.getByRole("form", { name: "CSV取込フォーム" });
    const csv = [
      "supplier,brand,product_url,product_name,supplier_product_code,supplier_price,currency,availability,buyma_price",
      `${supplierName},${brandName},${csvUrl},${productName},SKU-${suffix},1200,EUR,in_stock,300000`,
      `${supplierName},${brandName},https://${domain}/products/invalid-${suffix},Invalid Product,INVALID-${suffix},not-a-price,EUR,in_stock,`,
      `${supplierName},${brandName},${csvUrl},Duplicate Product,SKU-${suffix},1200,EUR,in_stock,300000`,
    ].join("\n");
    await csvForm.getByLabel("CSVファイル").setInputFiles({
      name: `e2e-ingestion-${suffix}.csv`,
      mimeType: "text/csv",
      buffer: Buffer.from(csv, "utf-8"),
    });
    const [csvResponse] = await Promise.all([
      page.waitForResponse(
        (r) =>
          r.url().includes("/research-ingestion/csv") &&
          r.request().method() === "POST",
      ),
      csvForm.getByRole("button", { name: "CSVを取り込む" }).click(),
    ]);
    const csvStatus = csvResponse.status();
    const csvBody = await csvResponse.text();
    expect(
      csvResponse.ok(),
      `CSV import failed with HTTP ${csvStatus}: ${csvBody}`,
    ).toBeTruthy();
    await expect(
      csvForm.getByText(/成功 1件.*失敗 1件.*重複 1件/),
    ).toBeVisible();
    await expect(csvForm.getByText(/行\s+2: 成功/)).toBeVisible();
    await expect(csvForm.getByText(/行\s+3: 失敗/)).toBeVisible();
    await expect(csvForm.getByText(/行\s+4: 重複/)).toBeVisible();
    await csvForm.getByRole("button", { name: "閉じる" }).click();

    const matchedSources = await findSources(api, token, productName);
    expect(matchedSources).toHaveLength(1);
    const matchedSource = matchedSources[0];
    ids.sourceIds.push(matchedSource.id);
    expect(matchedSource.processing_status).toBe("matched");
    const sourceRow = page.getByRole("row").filter({ hasText: productName });
    await expect(sourceRow).toContainText("matched");
    await sourceRow.getByRole("button", { name: "候補を作成" }).click();
    const conversionForm = page.getByRole("form", {
      name: "商品リサーチ候補変換フォーム",
    });
    await conversionForm
      .getByRole("spinbutton", { name: "為替レート", exact: true })
      .fill("165");
    await conversionForm
      .getByRole("spinbutton", { name: "BUYMA販売価格", exact: true })
      .fill("300000");
    const [conversionResponse] = await Promise.all([
      page.waitForResponse(
        (r) =>
          r
            .url()
            .includes(
              `/research-ingestion/${matchedSource.id}/create-candidate`,
            ) && r.request().method() === "POST",
      ),
      conversionForm.getByRole("button", { name: "候補を作成" }).click(),
    ]);
    expect(conversionResponse.ok()).toBeTruthy();

    const converted = await getSource(api, token, matchedSource.id);
    expect(converted.candidate_id).toBeTruthy();
    ids.candidateId = converted.candidate_id!;
    expect(converted.brand_id).toBe(ids.brandId);
    const candidate = await getCandidate(api, token, ids.candidateId);
    expect(candidate.source_product_id).toBe(matchedSource.id);
    expect(candidate.brand_id).toBe(ids.brandId);
    expect(candidate.supplier_id).toBe(ids.supplierId);
    const convertedRow = page.getByRole("row").filter({ hasText: productName });
    const candidateLink = convertedRow.getByRole("link", {
      name: "候補を開く",
    });
    await expect(candidateLink).toBeVisible();
    await candidateLink.click();
    await expect(page).toHaveURL(
      new RegExp(`/product-research/${ids.candidateId}$`),
    );
    await expect(
      page.getByRole("heading", { name: productName }),
    ).toBeVisible();
    const overview = page.locator("section.panel").filter({
      has: page.getByRole("heading", { name: "概要", exact: true }),
    });
    await expect(overview.getByText(brandName, { exact: true })).toBeVisible();
    await expect(
      overview.getByText(supplierName, { exact: true }),
    ).toBeVisible();

    await page
      .getByRole("link", { name: "リサーチ取込", exact: true })
      .click();
    const protectedRow = page.getByRole("row").filter({ hasText: productName });
    page.once("dialog", (dialog) => dialog.accept());
    const [deleteResponse] = await Promise.all([
      page.waitForResponse(
        (r) =>
          r.url().includes(`/research-ingestion/${matchedSource.id}`) &&
          r.request().method() === "DELETE",
      ),
      protectedRow.getByRole("button", { name: "削除" }).click(),
    ]);
    expect(deleteResponse.status()).toBe(409);
    await expect(
      page.getByText("候補へ変換済みの取込ソースは削除できません。", {
        exact: true,
      }),
    ).toBeVisible();
  } finally {
    if (token) await cleanupIngestion(api, token, ids);
    await api.dispose();
  }
});
