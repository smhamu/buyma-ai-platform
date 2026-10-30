import { expect, test } from "@playwright/test";
import { cleanupResearchData, findBrand, findSupplier, updateSupplierStatus, type ResearchIds } from "./utils/research-api";
import { createApiContext, loginByApi, uniqueValue, type E2ECredentials } from "./utils/e2e-api";

test.describe.configure({ mode: "serial" });

test("admin manages an EU luxury research candidate end to end", async ({ page }) => {
  test.skip(!process.env.E2E_ADMIN_EMAIL || !process.env.E2E_ADMIN_PASSWORD, "E2E admin credentials are required for Brand Master mutation.");
  const credentials: E2ECredentials = { email: process.env.E2E_ADMIN_EMAIL!, password: process.env.E2E_ADMIN_PASSWORD!, username: "e2e-admin" };
  const api = await createApiContext();
  const ids: ResearchIds = {};
  const suffix = uniqueValue("luxury").replace(/-/g, "_");
  const brandCode = `e2e_brand_${suffix}`.toLowerCase();
  const brandName = `E2E Luxury Brand ${suffix}`;
  const supplierName = `E2E EU Supplier ${suffix}`;
  const productName = `E2E Luxury Bag ${suffix}`;
  let token = "";

  try {
    token = (await loginByApi(api, credentials)).access_token;
    await page.goto("/login");
    await page.getByLabel("メールアドレス").fill(credentials.email);
    await page.getByLabel("パスワード").fill(credentials.password);
    await page.getByRole("button", { name: "ログイン" }).click();
    await expect(page).toHaveURL(/\/knowledge-bases$/);
    const brandsLink = page.getByRole("link", { name: "ブランド" });
    await expect(brandsLink).toBeVisible();
    await brandsLink.click();
    await expect(page).toHaveURL(/\/brands$/);
    await page.getByRole("button", { name: "ブランドを追加" }).click();
    const brandForm = page.getByRole("form", { name: "ブランドフォーム" });
    await brandForm.getByLabel("ブランドコード").fill(brandCode);
    await brandForm.getByLabel("ブランド名").fill(brandName);
    await brandForm.getByLabel("ラグジュアリーランク").selectOption("luxury");
    await brandForm.getByLabel("購入ポリシー").selectOption("normal");
    await expect(brandForm.getByLabel("ブランドコード")).toHaveValue(brandCode);
    await expect(brandForm.getByLabel("ブランド名")).toHaveValue(brandName);
    await expect(brandForm.getByLabel("ラグジュアリーランク")).toHaveValue("luxury");
    await expect(brandForm.getByLabel("購入ポリシー")).toHaveValue("normal");
    await expect(brandForm.locator(".form-error-banner")).toHaveCount(0);
    expect(
      await brandForm.evaluate((form: HTMLFormElement) => form.checkValidity()),
    ).toBeTruthy();
    const saveBrandButton = brandForm.getByRole("button", { name: "ブランドを保存" });
    await expect(saveBrandButton).toBeVisible();
    await expect(saveBrandButton).toBeEnabled();
    const [createBrandResponse] = await Promise.all([
      page.waitForResponse(
        response =>
          response.url().includes("/brands") &&
          response.request().method() === "POST",
      ),
      saveBrandButton.click(),
    ]);
    expect(createBrandResponse.ok()).toBeTruthy();

    ids.brandId = (await findBrand(api, token, brandCode))?.id;
    expect(ids.brandId).toBeTruthy();
    const brandRow = page.getByRole("row").filter({ hasText: brandName });
    await expect(brandRow).toBeVisible();
    await expect(brandRow).toContainText("ラグジュアリー");
    await expect(brandRow.getByRole("button", { name: "編集" })).toBeVisible();
    await page.getByRole("link", { name: "仕入先" }).click();
    await page.getByRole("button", { name: "仕入先を追加" }).click();
    const supplierForm = page.getByRole("heading", { name: "仕入先を追加" }).locator("xpath=ancestor::form");
    await supplierForm.getByLabel("名称").fill(supplierName);
    await supplierForm.getByLabel("WebサイトURL").fill("https://example.com/e2e-supplier");
    await supplierForm.getByLabel("国").selectOption("FR");
    await supplierForm.getByLabel("種別").selectOption("authorized_retailer");
    await supplierForm
      .getByRole("combobox", { name: "Currency", exact: true })
      .selectOption("EUR");
    await supplierForm.getByLabel("VATポリシー").selectOption("excluded_for_export");
    await supplierForm.getByLabel("VAT率").fill("0.20");
    await supplierForm.getByLabel("BUYMAステータス").selectOption("allowed");
    await supplierForm.getByLabel(brandName).check();
    await supplierForm.getByLabel("日本へ配送可").check();
    await supplierForm.getByRole("button", { name: "仕入先を保存" }).click();
    const supplierRow = page.getByRole("row").filter({ hasText: supplierName });
    await expect(supplierRow).toContainText("FR");
    await expect(supplierRow).toContainText(brandName);
    await expect(supplierRow).toContainText("許可");
    const createdSupplier = await findSupplier(api, token, supplierName);
    expect(createdSupplier).toBeTruthy();
    expect(createdSupplier?.brands.some(brand => brand.id === ids.brandId)).toBe(
      true,
    );
    ids.supplierId = createdSupplier?.id;
    expect(ids.supplierId).toBeTruthy();

    await page
      .getByRole("link", { name: "商品リサーチ候補", exact: true })
      .click();
    await page
      .getByRole("button", { name: "候補を追加", exact: true })
      .click();
    const candidateForm = page.getByRole("heading", { name: "商品リサーチ候補を追加" }).locator("xpath=ancestor::form");
    await candidateForm.getByLabel("ブランド").selectOption(ids.brandId!);
    expect(ids.supplierId).toBeTruthy();
    const supplierSelect = candidateForm.getByRole("combobox", {
      name: "仕入先",
      exact: true,
    });
    await expect(supplierSelect).toBeVisible();
    const supplierOption = supplierSelect.locator(
      `option[value="${ids.supplierId}"]`,
    );
    await expect(supplierOption).toHaveCount(1);
    await supplierSelect.selectOption(ids.supplierId!);
    await candidateForm.getByLabel("商品URL").fill("https://example.com/e2e-product");
    await candidateForm.getByLabel("商品名").fill(productName);
    await candidateForm
      .getByRole("spinbutton", { name: "仕入価格", exact: true })
      .fill("1200");
    const vatPolicySelect = candidateForm.getByRole("combobox", {
      name: "VATポリシー",
      exact: true,
    });
    await expect(vatPolicySelect).toBeVisible();
    await expect(vatPolicySelect.locator('option[value="unknown"]')).toHaveCount(
      1,
    );
    await vatPolicySelect.selectOption("unknown");
    await expect(candidateForm.getByText(/VAT控除は利益計算に適用されません/)).toBeVisible();
    await expect(
      vatPolicySelect.locator('option[value="excluded_for_export"]'),
    ).toHaveCount(1);
    await vatPolicySelect.selectOption("excluded_for_export");
    const vatRateInput = candidateForm.getByRole("spinbutton", {
      name: "VAT率（例: 0.20）",
      exact: true,
    });
    await expect(vatRateInput).toBeVisible();
    await vatRateInput.fill("0.20");
    await candidateForm
      .getByRole("spinbutton", { name: "為替レート", exact: true })
      .fill("165");
    await candidateForm
      .getByRole("spinbutton", {
        name: "日本向け送料",
        exact: true,
      })
      .fill("5000");
    await candidateForm
      .getByRole("spinbutton", {
        name: "輸入費用見込",
        exact: true,
      })
      .fill("10000");
    await candidateForm
      .getByRole("spinbutton", {
        name: "その他費用見込",
        exact: true,
      })
      .fill("3000");
    await candidateForm
      .getByRole("spinbutton", { name: "BUYMA販売価格", exact: true })
      .fill("300000");
    await candidateForm
      .getByRole("spinbutton", { name: "BUYMA手数料率", exact: true })
      .fill("0.077");
    await candidateForm.getByLabel("在庫状況").selectOption("in_stock");
    await candidateForm
      .getByRole("combobox", { name: "購入制限", exact: true })
      .selectOption("normal");
    const [calculateResponse] = await Promise.all([
      page.waitForResponse(
        response =>
          response.url().includes("/product-research-candidates/calculate") &&
          response.request().method() === "POST",
      ),
      candidateForm
        .getByRole("button", { name: "利益を計算" })
        .click(),
    ]);
    expect(calculateResponse.ok()).toBeTruthy();
    const preview = candidateForm.getByRole("region", { name: "利益プレビュー" });
    await expect(preview).toBeVisible();
    await expect(preview).toContainText("実効仕入価格");
    await expect(preview).toContainText("仕入原価");
    await expect(preview).toContainText("BUYMA手数料");
    await expect(preview).toContainText("総費用");
    await expect(preview).toContainText("利益");
    await candidateForm.getByRole("button", { name: "候補を保存" }).click();

    await expect(page).toHaveURL(/\/product-research\/[^/]+$/);
    ids.candidateId = page.url().split("/").pop();
    await expect(page.getByRole("heading", { name: productName })).toBeVisible();
    for (const heading of ["概要", "仕入費用", "BUYMA", "利益", "調査"]) await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
    await expect(page.getByText(brandName, { exact: true }).first()).toBeVisible();
    await expect(page.getByText(supplierName, { exact: true })).toBeVisible();

    await page
      .getByRole("button", { name: "候補を編集", exact: true })
      .click();
    const editForm = page.getByRole("heading", { name: "商品リサーチ候補を編集" }).locator("xpath=ancestor::form");
    await editForm.getByLabel("調査ステータス").selectOption("ready_for_listing");
    await editForm.getByRole("button", { name: "変更を保存" }).click();
    const researchStatusValue = page
      .getByRole("heading", { name: "調査", exact: true })
      .locator("xpath=ancestor::section")
      .locator(".detail-row")
      .filter({ has: page.getByText("ステータス", { exact: true }) })
      .locator(".detail-row__value");
    await expect(researchStatusValue).toHaveText("出品準備完了");

    await page
      .getByRole("button", { name: "候補を編集", exact: true })
      .click();
    const restrictedForm = page.getByRole("heading", { name: "商品リサーチ候補を編集" }).locator("xpath=ancestor::form");
    await restrictedForm
      .getByRole("combobox", { name: "購入制限", exact: true })
      .selectOption("client_advisor_only");
    await restrictedForm.getByRole("button", { name: "変更を保存" }).click();
    await expect(restrictedForm.getByText("この商品は購入制限の対象です。")).toBeVisible();
    await restrictedForm
      .getByRole("combobox", { name: "購入制限", exact: true })
      .selectOption("normal");
    await restrictedForm.getByRole("button", { name: "変更を保存" }).click();
    await expect(researchStatusValue).toHaveText("出品準備完了");

    await updateSupplierStatus(api, token, ids.supplierId!, "prohibited");
    await page
      .getByRole("button", { name: "候補を編集", exact: true })
      .click();
    const blockedForm = page.getByRole("heading", { name: "商品リサーチ候補を編集" }).locator("xpath=ancestor::form");
    await blockedForm.getByRole("button", { name: "変更を保存" }).click();
    await expect(blockedForm.getByText("この仕入先はBUYMAでの買付が禁止されています。")).toBeVisible();
    await blockedForm.getByRole("button", { name: "閉じる" }).click();

    await page
      .getByRole("link", { name: "商品リサーチ候補", exact: true })
      .click();
    const candidateRow = page.getByRole("row").filter({ hasText: productName });
    await expect(candidateRow).toContainText(brandName);
    await expect(candidateRow).toContainText(supplierName);
    await expect(candidateRow.locator(".profit-value")).toHaveText(
      /^\+[¥￥]\s*[\d,]+(?:\.\d{2})?$/,
    );
    await expect(
      candidateRow.getByText(/^\d+(?:\.\d+)?%$/),
    ).toBeVisible();
    page.once("dialog", dialog => dialog.accept());
    await candidateRow.getByRole("button", { name: "削除" }).click();
    await expect(page.getByRole("row").filter({ hasText: productName })).toHaveCount(0);
  } finally {
    if (token) await cleanupResearchData(api, token, ids);
    await api.dispose();
  }
});
