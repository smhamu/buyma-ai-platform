import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Supplier } from "../../modules/suppliers/types";
import { SupplierRakutenConfigPanel } from "./SupplierRakutenConfigPanel";

const fetchConfig = vi.fn();
const saveConfig = vi.fn();
const deleteConfig = vi.fn();
const previewProducts = vi.fn();
vi.mock("../../modules/suppliers/api", () => ({
  fetchSupplierRakutenConfig: (id:string) => fetchConfig(id),
  saveSupplierRakutenConfig: (id:string, body:unknown) => saveConfig(id, body),
  deleteSupplierRakutenConfig: (id:string) => deleteConfig(id),
  previewSupplierRakutenProducts: (id:string, page:number) => previewProducts(id, page),
}));

const supplier = { id:"supplier-1", name:"Mytheresa JP" } as Supplier;
const pending = {
  configured:true, id:"config-1", supplier_id:supplier.id, advertiser_mid:43171,
  approval_status:"pending", sync_enabled:false, search_keyword:null, language:"en_US",
  max_results:100, max_pages:10, sync_interval_minutes:1440, approved_at:null,
  can_sync:false, blocked_reasons:["advertiser_not_approved"], created_at:"", updated_at:"",
  can_preview:false, preview_blocked_reasons:["advertiser_not_approved"],
};

describe("SupplierRakutenConfigPanel", () => {
  beforeEach(() => { vi.clearAllMocks(); fetchConfig.mockResolvedValue(pending); });

  it("keeps synchronization disabled while approval is pending", async () => {
    render(<SupplierRakutenConfigPanel supplier={supplier} onClose={() => undefined}/>);
    expect(await screen.findByText("広告主の承認待ちです")).toBeInTheDocument();
    expect(screen.getByLabelText("商品同期を有効にする")).toBeDisabled();
  });

  it("saves pending MID and synchronization limits without making a live request", async () => {
    saveConfig.mockResolvedValue(pending);
    render(<SupplierRakutenConfigPanel supplier={supplier} onClose={() => undefined}/>);
    await screen.findByDisplayValue("43171");
    fireEvent.click(screen.getByRole("button", { name:"設定を保存" }));
    await waitFor(() => expect(saveConfig).toHaveBeenCalledWith("supplier-1", expect.objectContaining({ advertiser_mid:43171, approval_status:"pending", sync_enabled:false })));
    expect(await screen.findByText("Rakuten連携設定を保存しました。")).toBeInTheDocument();
  });

  it("shows an approved preview without persisting products", async () => {
    fetchConfig.mockResolvedValue({ ...pending, approval_status:"approved", can_preview:true, preview_blocked_reasons:[] });
    previewProducts.mockResolvedValue({
      supplier_id:"supplier-1", advertiser_mid:43171, page_number:1, total_pages:1,
      total_matches:1, fetched_at:"2026-10-31T00:00:00Z", persisted:false,
      items:[{ advertiser_id:43171, advertiser_name:"Mytheresa", link_id:"1", sku:"SKU-1", name:"Leather shoes", price:"199.95", currency:"EUR", product_url:"https://www.mytheresa.com/product", image_url:null, primary_category:"Shoes", secondary_category:"Women", short_description:null }],
    });
    render(<SupplierRakutenConfigPanel supplier={supplier} onClose={() => undefined}/>);
    fireEvent.click(await screen.findByRole("button", { name:"商品をプレビュー" }));
    expect(await screen.findByText("Leather shoes")).toBeInTheDocument();
    expect(screen.getByText(/DB保存なし/)).toBeInTheDocument();
    expect(previewProducts).toHaveBeenCalledWith("supplier-1", 1);
  });
});
