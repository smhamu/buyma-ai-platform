import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ApiClientError } from "../../lib/api";
import { fetchBrands } from "../../modules/brands/api";
import { fetchProductCategories, resolvePurchasePolicy } from "../../modules/product-categories/api";
import { updateCandidate } from "../../modules/product-research/api";
import type { Candidate } from "../../modules/product-research/types";
import { fetchSuppliers } from "../../modules/suppliers/api";
import { CandidateForm } from "./CandidateForm";

vi.mock("../../modules/brands/api", () => ({ fetchBrands: vi.fn() }));
vi.mock("../../modules/suppliers/api", () => ({ fetchSuppliers: vi.fn() }));
vi.mock("../../modules/product-categories/api", () => ({ fetchProductCategories: vi.fn(), resolvePurchasePolicy: vi.fn() }));
vi.mock("../../modules/product-research/api", () => ({ calculateCandidate: vi.fn(), createCandidate: vi.fn(), updateCandidate: vi.fn() }));

const candidate = {
  id:"c",owner_user_id:"u",supplier_id:"s",brand_id:"b",category_id:null,
  supplier_product_url:"https://shop.invalid/item",supplier_product_code:null,product_name:"Bag",category:null,
  supplier_price:"100",supplier_currency:"EUR",vat_policy:"unknown",vat_rate:null,export_price:null,
  japan_shipping_cost:"0",exchange_rate:"160",supplier_cost_jpy:"16000",estimated_import_cost:"0",
  estimated_other_cost:"0",total_cost:"16000",buyma_price:"30000",buyma_fee_rate:"0.077",buyma_fee:"2310",
  profit_amount:"11690",profit_rate:"0.389667",availability_status:"in_stock",purchase_restriction:"normal",
  research_status:"ready_for_listing",checked_at:null,online_purchase_available:true,is_active:true,created_at:"",updated_at:"",
} satisfies Candidate;

describe("CandidateForm purchase restriction", () => {
  it("offers product restrictions and shows a user-facing restricted-product error", async () => {
    vi.mocked(fetchBrands).mockResolvedValue({items:[],page:1,page_size:100,total:0,total_pages:0});
    vi.mocked(fetchSuppliers).mockResolvedValue({items:[],page:1,page_size:100,total:0,total_pages:0});
    vi.mocked(fetchProductCategories).mockResolvedValue([]);
    vi.mocked(resolvePurchasePolicy).mockResolvedValue({policy:"normal",research_enabled:true,source:"brand_default"});
    vi.mocked(updateCandidate).mockRejectedValue(new ApiClientError(409,"PRODUCT_PURCHASE_RESTRICTED","This product requires purchase through a client advisor and cannot be marked ready for listing."));
    render(<MemoryRouter><CandidateForm candidate={candidate} onClose={vi.fn()} /></MemoryRouter>);

    const restriction = screen.getByRole("combobox", {name:"Purchase restriction"});
    expect(restriction).toHaveValue("normal");
    expect(restriction).toContainHTML("client_advisor_only");
    fireEvent.change(restriction, {target:{value:"client_advisor_only"}});
    fireEvent.click(screen.getByRole("button", {name:"Save Changes"}));

    await waitFor(() => expect(screen.getByText(/requires purchase through a client advisor/)).toBeVisible());
  });
});
