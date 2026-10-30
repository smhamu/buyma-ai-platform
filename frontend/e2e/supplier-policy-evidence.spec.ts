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
    await page.getByLabel("メールアドレス").fill(credentials.email);
    await page.getByLabel("パスワード").fill(credentials.password);
    await page.getByRole("button",{name:"ログイン"}).click();
    await page.getByRole("link",{name:"仕入先",exact:true}).click();
    await page.getByRole("button",{name:"仕入先を追加"}).click();
    const form=page.getByRole("heading",{name:"仕入先を追加"}).locator("xpath=ancestor::form");
    await form.getByLabel("名称").fill(supplierName);
    await form.getByLabel("WebサイトURL").fill("https://e2e-policy-shop.invalid");
    await form.getByLabel("利用規約ステータス").selectOption("unknown");
    const [createSupplierResponse]=await Promise.all([
      page.waitForResponse(response=>
        response.url().includes("/suppliers")&&
        response.request().method()==="POST",
      ),
      form.getByRole("button",{name:"仕入先を保存"}).click(),
    ]);
    expect(createSupplierResponse.ok()).toBeTruthy();
    const supplier=await findSupplier(api,token,supplierName);
    expect(supplier).toBeTruthy();ids.supplierId=supplier!.id;
    await page.goto("/suppliers?page_size=100");
    const row=page.getByRole("row").filter({hasText:supplierName});
    await expect(row).toBeVisible();
    await row.getByRole("button",{name:"ポリシー根拠"}).click();
    const panel=page.getByRole("region",{name:"ポリシー根拠"});
    const termsSummary=panel
      .getByRole("region",{name:"最新のポリシー根拠"})
      .getByRole("article")
      .filter({hasText:/^利用規約/});
    await expect(termsSummary).toHaveCount(1);
    await expect(termsSummary.getByText("現在のポリシー: 未確認")).toBeVisible();
    const evidenceForm=panel.getByRole("form",{name:"ポリシー根拠を追加"});
    await evidenceForm.getByLabel("根拠種別").selectOption("terms");
    await evidenceForm.getByLabel("結果").selectOption("restricted");
    await evidenceForm.getByLabel("出典URL").fill("https://evidence.invalid/terms-v1");
    await evidenceForm.getByLabel("メモ").fill("Initial terms review.");
    const [createResponse]=await Promise.all([
      page.waitForResponse(r=>r.url().includes(`/suppliers/${ids.supplierId}/policy-evidence`)&&r.request().method()==="POST"),
      evidenceForm.getByRole("button",{name:"根拠を追加"}).click(),
    ]);
    expect(createResponse.ok()).toBeTruthy();
    await expect(termsSummary.getByText("最新の根拠: 制限あり")).toBeVisible();
    await expect(termsSummary.getByText("要確認")).toBeVisible();
    await expect(termsSummary.getByText("現在のポリシー: 未確認")).toBeVisible();
    await panel.getByRole("button",{name:"閉じる"}).click();

    await row.getByRole("button",{name:"編集"}).click();
    const edit=page.getByRole("heading",{name:"仕入先を編集"}).locator("xpath=ancestor::form");
    await edit.getByLabel("利用規約ステータス").selectOption("restricted");
    const [updateSupplierResponse]=await Promise.all([
      page.waitForResponse(response=>
        response.url().includes(`/suppliers/${ids.supplierId}`)&&
        response.request().method()==="PUT",
      ),
      edit.getByRole("button",{name:"仕入先を保存"}).click(),
    ]);
    expect(updateSupplierResponse.ok()).toBeTruthy();
    await row.getByRole("button",{name:"ポリシー根拠"}).click();
    const updatedPanel=page.getByRole("region",{name:"ポリシー根拠"});
    const updatedTermsSummary=updatedPanel
      .getByRole("region",{name:"最新のポリシー根拠"})
      .getByRole("article")
      .filter({hasText:/^利用規約/});
    await expect(updatedTermsSummary).toHaveCount(1);
    await expect(updatedTermsSummary.getByText("現在のポリシー: 制限あり")).toBeVisible();
    await expect(updatedTermsSummary.getByText("最新", { exact: true })).toBeVisible();
    const secondForm=updatedPanel.getByRole("form",{name:"ポリシー根拠を追加"});
    await secondForm.getByLabel("根拠種別").selectOption("terms");
    await secondForm.getByLabel("結果").selectOption("restricted");
    await secondForm.getByLabel("出典URL").fill("https://evidence.invalid/terms-v2");
    await secondForm.getByLabel("メモ").fill("Follow-up terms review.");
    await secondForm.getByRole("button",{name:"根拠を追加"}).click();
    await expect(updatedPanel.getByText("Initial terms review.")).toBeVisible();
    await expect(updatedPanel.getByText("Follow-up terms review.")).toBeVisible();
  } finally {
    if(token) await cleanupResearchData(api,token,ids);
    await api.dispose();
  }
});
