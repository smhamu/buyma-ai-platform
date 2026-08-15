import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { BrandsPage } from "./BrandsPage";

vi.mock("../modules/auth/AuthContext",()=>({useAuth:()=>({user:{role:"admin"}})}));
vi.mock("../modules/brands/api",()=>({fetchBrands:vi.fn().mockResolvedValue({items:[{id:"b1",brand_code:"chanel",brand_name:"CHANEL",luxury_tier:"ultra_luxury",official_site_url:null,online_purchase_policy:"research_only",purchase_restriction_notes:null,is_research_enabled:true,is_active:true,created_at:"2026-01-01",updated_at:"2026-01-01"}],page:1,page_size:20,total:1,total_pages:1}),createBrand:vi.fn(),updateBrand:vi.fn(),deleteBrand:vi.fn()}));
vi.mock("../modules/product-categories/api",()=>({fetchProductCategories:vi.fn().mockResolvedValue([{id:"c1",category_code:"fragrance",category_name:"Fragrance",is_active:true}]),fetchCategoryPolicies:vi.fn().mockResolvedValue([{id:"p1",brand_id:"b1",category_id:"c1",category:{id:"c1",category_code:"fragrance",category_name:"Fragrance",is_active:true},online_purchase_policy:"normal",research_enabled:true,policy_notes:"Official online boutique",checked_at:"2026-08-15T00:00:00Z",created_at:"2026-08-15",updated_at:"2026-08-15"}]),createCategoryPolicy:vi.fn(),updateCategoryPolicy:vi.fn(),deleteCategoryPolicy:vi.fn()}));

describe("Brand Category Policies",()=>{it("shows fallback and overrides with admin actions",async()=>{render(<MemoryRouter><BrandsPage/></MemoryRouter>);await userEvent.click(await screen.findByRole("button",{name:"Category Policies"}));await waitFor(()=>expect(screen.getByText("Default brand policy: Research Only")).toBeInTheDocument());expect(screen.getByText("Fragrance")).toBeInTheDocument();expect(screen.getByText("Official online boutique")).toBeInTheDocument();expect(screen.getByRole("button",{name:"Add Policy"})).toBeInTheDocument();});});
