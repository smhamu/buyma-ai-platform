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
    await page.getByLabel("Email").fill(credentials.email);
    await page.getByLabel("Password").fill(credentials.password);
    await page.getByRole("button", { name: "Login" }).click();
    await expect(page).toHaveURL(/\/knowledge-bases$/);
    const brandsLink = page.getByRole("link", { name: "Brands" });
    await expect(brandsLink).toBeVisible();
    await brandsLink.click();
    await expect(page).toHaveURL(/\/brands$/);
    await page.getByRole("button", { name: "Add Brand" }).click();
    const brandForm = page.getByRole("form", { name: "Brand form" });
    await brandForm.getByLabel("Brand code").fill(brandCode);
    await brandForm.getByLabel("Brand name").fill(brandName);
    await brandForm.getByLabel("Luxury tier").selectOption("luxury");
    await brandForm.getByLabel("Purchase policy").selectOption("normal");
    await expect(brandForm.getByLabel("Brand code")).toHaveValue(brandCode);
    await expect(brandForm.getByLabel("Brand name")).toHaveValue(brandName);
    await expect(brandForm.getByLabel("Luxury tier")).toHaveValue("luxury");
    await expect(brandForm.getByLabel("Purchase policy")).toHaveValue("normal");
    await expect(brandForm.locator(".form-error-banner")).toHaveCount(0);
    expect(
      await brandForm.evaluate((form: HTMLFormElement) => form.checkValidity()),
    ).toBeTruthy();
    const saveBrandButton = brandForm.getByRole("button", { name: "Save Brand" });
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
    await expect(brandRow).toContainText("Luxury");
    await expect(brandRow.getByRole("button", { name: "Edit" })).toBeVisible();
    await page.getByRole("link", { name: "Suppliers" }).click();
    await page.getByRole("button", { name: "Add Supplier" }).click();
    const supplierForm = page.getByRole("heading", { name: "Add Supplier" }).locator("xpath=ancestor::form");
    await supplierForm.getByLabel("Name").fill(supplierName);
    await supplierForm.getByLabel("Website URL").fill("https://example.com/e2e-supplier");
    await supplierForm.getByLabel("Country").selectOption("FR");
    await supplierForm.getByLabel("Type").selectOption("authorized_retailer");
    await supplierForm.getByLabel("Currency").selectOption("EUR");
    await supplierForm.getByLabel("VAT policy").selectOption("excluded_for_export");
    await supplierForm.getByLabel("VAT rate").fill("0.20");
    await supplierForm.getByLabel("BUYMA status").selectOption("allowed");
    await supplierForm.getByLabel(brandName).check();
    await supplierForm.getByLabel("Ships to Japan").check();
    await supplierForm.getByRole("button", { name: "Save Supplier" }).click();
    const supplierRow = page.getByRole("row").filter({ hasText: supplierName });
    await expect(supplierRow).toContainText("FR");
    await expect(supplierRow).toContainText(brandName);
    await expect(supplierRow).toContainText("Allowed");
    const createdSupplier = await findSupplier(api, token, supplierName);
    expect(createdSupplier).toBeTruthy();
    expect(createdSupplier?.brands.some(brand => brand.id === ids.brandId)).toBe(
      true,
    );
    ids.supplierId = createdSupplier?.id;
    expect(ids.supplierId).toBeTruthy();

    await page
      .getByRole("link", { name: "Research Candidates", exact: true })
      .click();
    await page.getByRole("button", { name: "Add Candidate" }).click();
    const candidateForm = page.getByRole("heading", { name: "Add Research Candidate" }).locator("xpath=ancestor::form");
    await candidateForm.getByLabel("Brand").selectOption(ids.brandId!);
    expect(ids.supplierId).toBeTruthy();
    const supplierSelect = candidateForm.getByRole("combobox", {
      name: "Supplier",
      exact: true,
    });
    await expect(supplierSelect).toBeVisible();
    const supplierOption = supplierSelect.locator(
      `option[value="${ids.supplierId}"]`,
    );
    await expect(supplierOption).toHaveCount(1);
    await supplierSelect.selectOption(ids.supplierId!);
    await candidateForm.getByLabel("Product URL").fill("https://example.com/e2e-product");
    await candidateForm.getByLabel("Product name").fill(productName);
    await candidateForm
      .getByRole("spinbutton", { name: "Supplier price", exact: true })
      .fill("1200");
    const vatPolicySelect = candidateForm.getByRole("combobox", {
      name: "VAT policy",
      exact: true,
    });
    await expect(vatPolicySelect).toBeVisible();
    await expect(vatPolicySelect.locator('option[value="unknown"]')).toHaveCount(
      1,
    );
    await vatPolicySelect.selectOption("unknown");
    await expect(candidateForm.getByText(/VAT deduction is not assumed/)).toBeVisible();
    await expect(
      vatPolicySelect.locator('option[value="excluded_for_export"]'),
    ).toHaveCount(1);
    await vatPolicySelect.selectOption("excluded_for_export");
    const vatRateInput = candidateForm.getByRole("spinbutton", {
      name: "VAT rate (e.g. 0.20)",
      exact: true,
    });
    await expect(vatRateInput).toBeVisible();
    await vatRateInput.fill("0.20");
    await candidateForm
      .getByRole("spinbutton", { name: "Exchange rate", exact: true })
      .fill("165");
    await candidateForm
      .getByRole("spinbutton", {
        name: "Japan shipping cost",
        exact: true,
      })
      .fill("5000");
    await candidateForm
      .getByRole("spinbutton", {
        name: "Estimated import cost",
        exact: true,
      })
      .fill("10000");
    await candidateForm
      .getByRole("spinbutton", {
        name: "Estimated other cost",
        exact: true,
      })
      .fill("3000");
    await candidateForm
      .getByRole("spinbutton", { name: "BUYMA price", exact: true })
      .fill("300000");
    await candidateForm
      .getByRole("spinbutton", { name: "BUYMA fee rate", exact: true })
      .fill("0.077");
    await candidateForm.getByLabel("Availability").selectOption("in_stock");
    await candidateForm
      .getByRole("combobox", { name: "Purchase restriction", exact: true })
      .selectOption("normal");
    const [calculateResponse] = await Promise.all([
      page.waitForResponse(
        response =>
          response.url().includes("/product-research-candidates/calculate") &&
          response.request().method() === "POST",
      ),
      candidateForm
        .getByRole("button", { name: "Calculate Profit" })
        .click(),
    ]);
    expect(calculateResponse.ok()).toBeTruthy();
    const preview = candidateForm.getByRole("region", { name: "Profit preview" });
    await expect(preview).toBeVisible();
    await expect(preview).toContainText("Effective supplier price");
    await expect(preview).toContainText("Supplier cost");
    await expect(preview).toContainText("BUYMA fee");
    await expect(preview).toContainText("Total cost");
    await expect(preview).toContainText("Profit");
    await candidateForm.getByRole("button", { name: "Save Candidate" }).click();

    await expect(page).toHaveURL(/\/product-research\/[^/]+$/);
    ids.candidateId = page.url().split("/").pop();
    await expect(page.getByRole("heading", { name: productName })).toBeVisible();
    for (const heading of ["Overview", "Purchase Cost", "BUYMA", "Profit", "Research"]) await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
    await expect(page.getByText(brandName, { exact: true }).first()).toBeVisible();
    await expect(page.getByText(supplierName, { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Edit Candidate" }).click();
    const editForm = page.getByRole("heading", { name: "Edit Research Candidate" }).locator("xpath=ancestor::form");
    await editForm.getByLabel("Research status").selectOption("ready_for_listing");
    await editForm.getByRole("button", { name: "Save Changes" }).click();
    await expect(page.getByText("Ready For Listing", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Edit Candidate" }).click();
    const restrictedForm = page.getByRole("heading", { name: "Edit Research Candidate" }).locator("xpath=ancestor::form");
    await restrictedForm
      .getByRole("combobox", { name: "Purchase restriction", exact: true })
      .selectOption("client_advisor_only");
    await restrictedForm.getByRole("button", { name: "Save Changes" }).click();
    await expect(restrictedForm.getByText("This product requires purchase through a client advisor and cannot be marked ready for listing.")).toBeVisible();
    await restrictedForm
      .getByRole("combobox", { name: "Purchase restriction", exact: true })
      .selectOption("normal");
    await restrictedForm.getByRole("button", { name: "Save Changes" }).click();
    await expect(page.getByText("Ready For Listing", { exact: true })).toBeVisible();

    await updateSupplierStatus(api, token, ids.supplierId!, "prohibited");
    await page.getByRole("button", { name: "Edit Candidate" }).click();
    const blockedForm = page.getByRole("heading", { name: "Edit Research Candidate" }).locator("xpath=ancestor::form");
    await blockedForm.getByRole("button", { name: "Save Changes" }).click();
    await expect(blockedForm.getByText("This supplier is prohibited for BUYMA purchasing.")).toBeVisible();
    await blockedForm.getByRole("button", { name: "Close" }).click();

    await page
      .getByRole("link", { name: "Research Candidates", exact: true })
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
    await candidateRow.getByRole("button", { name: "Delete" }).click();
    await expect(page.getByRole("row").filter({ hasText: productName })).toHaveCount(0);
  } finally {
    if (token) await cleanupResearchData(api, token, ids);
    await api.dispose();
  }
});
