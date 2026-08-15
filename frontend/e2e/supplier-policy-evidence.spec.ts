import { expect, test } from "@playwright/test";

import { createApiContext, loginByApi, uniqueValue, type E2ECredentials } from "./utils/e2e-api";
import { cleanupResearchData, findSupplier, type ResearchIds } from "./utils/research-api";

test("supplier policy evidence remains separate from the current policy", async ({page})=>{
  test.skip(!process.env.E2E_ADMIN_EMAIL||!process.env.E2E_ADMIN_PASSWORD,"E2E admin credentials are required.");
  const credentials:E2ECredentials={email:process.env.E2E_ADMIN_EMAIL!,password:process.env.E2E_ADMIN_PASSWORD!,username:"e2e-admin"};
  const api=await createApiContext();
  const ids:ResearchIds={};
  const supplierName=uniqueValue("e2e-policy-evidence");
  let token="";
  try {
    token=(await loginByApi(api,credentials)).access_token;
    await page.goto("/login");
    await page.getByLabel("Email").fill(credentials.email);
    await page.getByLabel("Password").fill(credentials.password);
    await page.getByRole("button",{name:"Login"}).click();
    await page.getByRole("link",{name:"Suppliers",exact:true}).click();
    await page.getByRole("button",{name:"Add Supplier"}).click();
    const form=page.getByRole("heading",{name:"Add Supplier"}).locator("xpath=ancestor::form");
    await form.getByLabel("Name").fill(supplierName);
    await form.getByLabel("Website URL").fill("https://e2e-policy-shop.invalid");
    await form.getByLabel("Terms status").selectOption("unknown");
    const [createSupplierResponse]=await Promise.all([
      page.waitForResponse(response=>
        response.url().includes("/suppliers")&&
        response.request().method()==="POST",
      ),
      form.getByRole("button",{name:"Save Supplier"}).click(),
    ]);
    expect(createSupplierResponse.ok()).toBeTruthy();
    const supplier=await findSupplier(api,token,supplierName);
    expect(supplier).toBeTruthy();ids.supplierId=supplier!.id;
    await page.goto("/suppliers?page_size=100");
    const row=page.getByRole("row").filter({hasText:supplierName});
    await expect(row).toBeVisible();
    await row.getByRole("button",{name:"Policy Evidence"}).click();
    const panel=page.getByRole("region",{name:"Policy Evidence"});
    const termsSummary=panel
      .getByRole("region",{name:"Latest policy evidence"})
      .getByRole("article")
      .filter({hasText:/^Terms/});
    await expect(termsSummary).toHaveCount(1);
    await expect(termsSummary.getByText("Current Policy: Unknown")).toBeVisible();
    const evidenceForm=panel.getByRole("form",{name:"Add policy evidence"});
    await evidenceForm.getByLabel("Evidence Type").selectOption("terms");
    await evidenceForm.getByLabel("Result").selectOption("restricted");
    await evidenceForm.getByLabel("Source URL").fill("https://evidence.invalid/terms-v1");
    await evidenceForm.getByLabel("Notes").fill("Initial terms review.");
    const [createResponse]=await Promise.all([
      page.waitForResponse(r=>r.url().includes(`/suppliers/${ids.supplierId}/policy-evidence`)&&r.request().method()==="POST"),
      evidenceForm.getByRole("button",{name:"Add Evidence"}).click(),
    ]);
    expect(createResponse.ok()).toBeTruthy();
    await expect(termsSummary.getByText("Latest Evidence: Restricted")).toBeVisible();
    await expect(termsSummary.getByText("Review required")).toBeVisible();
    await expect(termsSummary.getByText("Current Policy: Unknown")).toBeVisible();
    await panel.getByRole("button",{name:"Close"}).click();

    await row.getByRole("button",{name:"Edit"}).click();
    const edit=page.getByRole("heading",{name:"Edit Supplier"}).locator("xpath=ancestor::form");
    await edit.getByLabel("Terms status").selectOption("restricted");
    const [updateSupplierResponse]=await Promise.all([
      page.waitForResponse(response=>
        response.url().includes(`/suppliers/${ids.supplierId}`)&&
        response.request().method()==="PUT",
      ),
      edit.getByRole("button",{name:"Save Supplier"}).click(),
    ]);
    expect(updateSupplierResponse.ok()).toBeTruthy();
    await row.getByRole("button",{name:"Policy Evidence"}).click();
    const updatedPanel=page.getByRole("region",{name:"Policy Evidence"});
    const updatedTermsSummary=updatedPanel
      .getByRole("region",{name:"Latest policy evidence"})
      .getByRole("article")
      .filter({hasText:/^Terms/});
    await expect(updatedTermsSummary).toHaveCount(1);
    await expect(updatedTermsSummary.getByText("Current Policy: Restricted")).toBeVisible();
    await expect(updatedTermsSummary.getByText("Up to date")).toBeVisible();
    const secondForm=updatedPanel.getByRole("form",{name:"Add policy evidence"});
    await secondForm.getByLabel("Evidence Type").selectOption("terms");
    await secondForm.getByLabel("Result").selectOption("restricted");
    await secondForm.getByLabel("Source URL").fill("https://evidence.invalid/terms-v2");
    await secondForm.getByLabel("Notes").fill("Follow-up terms review.");
    await secondForm.getByRole("button",{name:"Add Evidence"}).click();
    await expect(updatedPanel.getByText("Initial terms review.")).toBeVisible();
    await expect(updatedPanel.getByText("Follow-up terms review.")).toBeVisible();
  } finally {
    if(token) await cleanupResearchData(api,token,ids);
    await api.dispose();
  }
});
