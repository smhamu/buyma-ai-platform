import { expect,test } from "@playwright/test";
import { createApiContext,loginByApi,uniqueValue,type E2ECredentials } from "./utils/e2e-api";
import { cleanupResearchData,findSupplier,type ResearchIds } from "./utils/research-api";

test("supplier policy review moves through no evidence, inconsistent, up to date and review due",async({page})=>{
  test.skip(!process.env.E2E_ADMIN_EMAIL||!process.env.E2E_ADMIN_PASSWORD,"E2E admin credentials are required.");
  const credentials:E2ECredentials={email:process.env.E2E_ADMIN_EMAIL!,password:process.env.E2E_ADMIN_PASSWORD!,username:"e2e-admin"};
  const api=await createApiContext();const ids:ResearchIds={};let token="";let originalSettings:Record<string,unknown>|null=null;
  const supplierName=uniqueValue("e2e-policy-review");
  try{
    token=(await loginByApi(api,credentials)).access_token;const headers={Authorization:`Bearer ${token}`};
    const settingsResponse=await api.get("/supplier-policy-review/settings",{headers});expect(settingsResponse.ok()).toBeTruthy();originalSettings=(await settingsResponse.json()).data;
    const settingsBody={...originalSettings,required_evidence_types:["terms"],terms_max_age_days:3650};delete settingsBody.id;delete settingsBody.user_id;
    expect((await api.put("/supplier-policy-review/settings",{headers,data:settingsBody})).ok()).toBeTruthy();
    await page.goto("/login");await page.getByLabel("Email").fill(credentials.email);await page.getByLabel("Password").fill(credentials.password);await page.getByRole("button",{name:"Login"}).click();
    await page.getByRole("link",{name:"Suppliers",exact:true}).click();await page.getByRole("button",{name:"Add Supplier"}).click();
    const createForm=page.getByRole("heading",{name:"Add Supplier"}).locator("xpath=ancestor::form");await createForm.getByLabel("Name").fill(supplierName);await createForm.getByLabel("Website URL").fill("https://e2e-policy-review.invalid");await createForm.getByLabel("Terms status").selectOption("unknown");
    const [created]=await Promise.all([page.waitForResponse(r=>r.url().includes("/suppliers")&&r.request().method()==="POST"),createForm.getByRole("button",{name:"Save Supplier"}).click()]);expect(created.ok()).toBeTruthy();
    const supplier=await findSupplier(api,token,supplierName);expect(supplier).toBeTruthy();ids.supplierId=supplier!.id;
    await page.getByRole("link",{name:"Policy Review",exact:true}).click();const reviewRow=page.getByRole("row").filter({hasText:supplierName});await expect(reviewRow).toContainText("No Evidence");await reviewRow.getByRole("button",{name:"Review"}).click();await page.getByRole("link",{name:"Open Evidence History"}).click();
    const evidencePanel=page.getByRole("region",{name:"Policy Evidence"});const evidenceForm=evidencePanel.getByRole("form",{name:"Add policy evidence"});await evidenceForm.getByLabel("Evidence Type").selectOption("terms");await evidenceForm.getByLabel("Result").selectOption("restricted");await evidenceForm.getByLabel("Checked At").fill(new Date(Date.now()-200*86400000).toISOString().slice(0,16));await evidenceForm.getByLabel("Notes").fill("E2E historical terms review.");
    const [evidenceResponse]=await Promise.all([page.waitForResponse(r=>r.url().includes(`/suppliers/${ids.supplierId}/policy-evidence`)&&r.request().method()==="POST"),evidenceForm.getByRole("button",{name:"Add Evidence"}).click()]);expect(evidenceResponse.ok()).toBeTruthy();
    await evidencePanel.getByRole("button",{name:"Close"}).click();await page.getByRole("link",{name:"Policy Review",exact:true}).click();const inconsistentRow=page.getByRole("row").filter({hasText:supplierName});await expect(inconsistentRow).toContainText("Inconsistent");await inconsistentRow.getByRole("button",{name:"Review"}).click();const inconsistentChanges=page.getByRole("region",{name:"Recent Review Changes"});await expect(inconsistentChanges).toContainText("No Evidence → Inconsistent");await page.getByRole("region",{name:"Supplier review detail"}).getByRole("button",{name:"Close"}).click();
    await page.getByRole("link",{name:"Suppliers",exact:true}).click();await page.goto("/suppliers?page_size=100");const supplierRow=page.getByRole("row").filter({hasText:supplierName});await supplierRow.getByRole("button",{name:"Edit"}).click();const editForm=page.getByRole("heading",{name:"Edit Supplier"}).locator("xpath=ancestor::form");await editForm.getByLabel("Terms status").selectOption("restricted");const [updated]=await Promise.all([page.waitForResponse(r=>r.url().includes(`/suppliers/${ids.supplierId}`)&&r.request().method()==="PUT"),editForm.getByRole("button",{name:"Save Supplier"}).click()]);expect(updated.ok()).toBeTruthy();
    await page.getByRole("link",{name:"Policy Review",exact:true}).click();const recoveredRow=page.getByRole("row").filter({hasText:supplierName});await expect(recoveredRow).toContainText("Up To Date");await recoveredRow.getByRole("button",{name:"Review"}).click();const recoveryChanges=page.getByRole("region",{name:"Recent Review Changes"});await expect(recoveryChanges).toContainText("Inconsistent → Up To Date");await page.getByRole("region",{name:"Supplier review detail"}).getByRole("button",{name:"Close"}).click();
    const reviewSettings=page.getByRole("region",{name:"Review settings"});await reviewSettings.getByRole("spinbutton",{name:"Terms max age (days)"}).fill("90");const [settingsUpdated]=await Promise.all([page.waitForResponse(r=>r.url().includes("/supplier-policy-review/settings")&&r.request().method()==="PUT"),reviewSettings.getByRole("button",{name:"Save Review Settings"}).click()]);expect(settingsUpdated.ok()).toBeTruthy();await expect(page.getByRole("row").filter({hasText:supplierName})).toContainText("Review Due");
  }finally{
    if(token&&originalSettings){const body={...originalSettings};delete body.id;delete body.user_id;await api.put("/supplier-policy-review/settings",{headers:{Authorization:`Bearer ${token}`},data:body});}
    if(token)await cleanupResearchData(api,token,ids);await api.dispose();
  }
});
