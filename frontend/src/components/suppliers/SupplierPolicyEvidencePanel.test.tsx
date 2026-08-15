import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createPolicyEvidence, fetchLatestPolicyEvidence, fetchPolicyEvidence } from "../../modules/suppliers/api";
import type { Supplier } from "../../modules/suppliers/types";
import { SupplierPolicyEvidencePanel } from "./SupplierPolicyEvidencePanel";

vi.mock("../../modules/suppliers/api",()=>({createPolicyEvidence:vi.fn(),fetchLatestPolicyEvidence:vi.fn(),fetchPolicyEvidence:vi.fn()}));

const supplier={id:"supplier-1",name:"EU Shop",terms_status:"unknown"} as Supplier;
const evidence={id:"evidence-1",supplier_id:supplier.id,owner_user_id:"owner-1",evidence_type:"terms",result:"restricted",source_url:"https://example.invalid/terms",source_title:null,source_excerpt:null,evidence_notes:"Commercial use is restricted.",checked_at:"2026-08-15T00:00:00Z",checked_by_user_id:"user-1",checked_by_username:"reviewer",policy_snapshot:{terms_status:"unknown"},created_at:"2026-08-15T00:00:00Z",updated_at:"2026-08-15T00:00:00Z"} as const;
const history={items:[evidence],page:1,page_size:20,total:1,total_pages:1};
const summary={terms:{current:"unknown",latest_evidence:"restricted",evidence_id:evidence.id,checked_at:evidence.checked_at,age_days:0,is_stale:false,consistent:false},robots:{current:"unknown",latest_evidence:null,evidence_id:null,checked_at:null,age_days:null,is_stale:null,consistent:null},vat:{current:"unknown",latest_evidence:null,evidence_id:null,checked_at:null,age_days:null,is_stale:null,consistent:null},shipping:{current:"unsupported",latest_evidence:null,evidence_id:null,checked_at:null,age_days:null,is_stale:null,consistent:null},official_api:{current:"unsupported",latest_evidence:null,evidence_id:null,checked_at:null,age_days:null,is_stale:null,consistent:null},buyma:{current:"unchecked",latest_evidence:null,evidence_id:null,checked_at:null,age_days:null,is_stale:null,consistent:null}};

describe("SupplierPolicyEvidencePanel",()=>{
  beforeEach(()=>{vi.mocked(fetchPolicyEvidence).mockResolvedValue(history);vi.mocked(fetchLatestPolicyEvidence).mockResolvedValue(summary);});

  it("shows current/latest mismatch, immutable history, and safe source link",async()=>{
    render(<SupplierPolicyEvidencePanel supplier={supplier} onClose={vi.fn()}/>);
    const termsCard=(await screen.findByText("Terms",{selector:"strong"})).closest("article")!;
    expect(within(termsCard).getByText("Current Policy: Unknown")).toBeVisible();
    expect(within(termsCard).getByText("Latest Evidence: Restricted")).toBeVisible();
    expect(within(termsCard).getByText("Review required")).toBeVisible();
    expect(screen.getByText("Commercial use is restricted.")).toBeVisible();
    expect(screen.getByRole("link",{name:"Source"})).toHaveAttribute("rel","noopener noreferrer");
  });

  it("adds evidence while warning that current policy is not changed",async()=>{
    vi.mocked(createPolicyEvidence).mockResolvedValue(evidence);
    render(<SupplierPolicyEvidencePanel supplier={supplier} onClose={vi.fn()}/>);
    expect(await screen.findByText(/does not automatically change/)).toBeVisible();
    fireEvent.change(screen.getByLabelText("Evidence Type"),{target:{value:"terms"}});
    fireEvent.change(screen.getByLabelText("Result"),{target:{value:"restricted"}});
    fireEvent.change(screen.getByLabelText("Source URL"),{target:{value:"https://example.invalid/terms-2"}});
    fireEvent.change(screen.getByLabelText("Notes"),{target:{value:"Replacement evidence."}});
    fireEvent.click(screen.getByRole("button",{name:"Add Evidence"}));
    await waitFor(()=>expect(createPolicyEvidence).toHaveBeenCalled());
    const termsCard=screen.getByText("Terms",{selector:"strong"}).closest("article")!;
    expect(within(termsCard).getByText("Current Policy: Unknown")).toBeVisible();
  });

  it("shows empty and error states",async()=>{
    vi.mocked(fetchPolicyEvidence).mockResolvedValue({...history,items:[],total:0,total_pages:0});
    const {unmount}=render(<SupplierPolicyEvidencePanel supplier={supplier} onClose={vi.fn()}/>);
    expect(await screen.findByText("No policy evidence recorded.")).toBeVisible();unmount();
    vi.mocked(fetchPolicyEvidence).mockRejectedValue(new Error("Evidence unavailable"));
    render(<SupplierPolicyEvidencePanel supplier={supplier} onClose={vi.fn()}/>);
    expect(await screen.findByText("Evidence unavailable")).toBeVisible();
  });
});
