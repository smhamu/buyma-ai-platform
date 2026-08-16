import { fireEvent,render,screen,waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe,expect,it,vi } from "vitest";
import { fetchReviewQueue,fetchReviewSettings,fetchReviewTransitions } from "../modules/supplier-policy-review/api";
import { SupplierPolicyReviewPage } from "./SupplierPolicyReviewPage";

vi.mock("../modules/supplier-policy-review/api",()=>({fetchReviewQueue:vi.fn(),fetchReviewSettings:vi.fn(),fetchReviewTransitions:vi.fn(),updateReviewSettings:vi.fn()}));
const type=(review_status:"up_to_date"|"review_due"|"inconsistent"|"no_evidence")=>({current:"unknown",latest_evidence:null,checked_at:null,age_days:null,max_age_days:180,consistent:null,is_stale:null,review_status});
describe("SupplierPolicyReviewPage",()=>{
  it("renders summary, queue status, detail actions and settings",async()=>{
    vi.mocked(fetchReviewSettings).mockResolvedValue({user_id:"u",terms_max_age_days:180,robots_max_age_days:180,vat_max_age_days:180,shipping_max_age_days:180,official_api_max_age_days:365,buyma_max_age_days:90,required_evidence_types:["terms"]});
    vi.mocked(fetchReviewTransitions).mockResolvedValue({items:[],page:1,page_size:20,total:0,total_pages:0});
    vi.mocked(fetchReviewQueue).mockResolvedValue({items:[{supplier_id:"s",supplier_name:"EU Shop",country_code:"FR",supplier_type:"boutique",brand_names:["Test Brand"],updated_at:new Date().toISOString(),overall_status:"no_evidence",priority:"high",issue_types:["terms"],oldest_evidence_at:null,types:{terms:type("no_evidence"),robots:type("up_to_date"),vat:type("up_to_date"),shipping:type("up_to_date"),official_api:type("up_to_date"),buyma:type("up_to_date")}}],page:1,page_size:20,total:1,total_pages:1,summary:{inconsistent:0,review_due:0,no_evidence:1,up_to_date:0}});
    render(<MemoryRouter><SupplierPolicyReviewPage/></MemoryRouter>);
    await waitFor(()=>expect(screen.getByText("EU Shop")).toBeVisible());
    expect(screen.getByRole("region",{name:"Review summary"})).toHaveTextContent("No Evidence");
    expect(screen.getByRole("region",{name:"Review settings"})).toBeVisible();
    expect(screen.getByRole("link",{name:"Edit Supplier Policy"})).toHaveAttribute("href","/suppliers?focus=s");
    fireEvent.click(screen.getByRole("button",{name:"Review"}));
    expect(await screen.findByRole("region",{name:"Recent Review Changes"})).toHaveTextContent("No review changes recorded.");
  });

  it("renders the empty state",async()=>{
    vi.mocked(fetchReviewSettings).mockResolvedValue({user_id:"u",terms_max_age_days:180,robots_max_age_days:180,vat_max_age_days:180,shipping_max_age_days:180,official_api_max_age_days:365,buyma_max_age_days:90,required_evidence_types:["terms"]});
    vi.mocked(fetchReviewQueue).mockResolvedValue({items:[],page:1,page_size:20,total:0,total_pages:0,summary:{inconsistent:0,review_due:0,no_evidence:0,up_to_date:0}});
    render(<MemoryRouter><SupplierPolicyReviewPage/></MemoryRouter>);
    expect(await screen.findByText("No supplier policy reviews found.")).toBeVisible();
  });
});
