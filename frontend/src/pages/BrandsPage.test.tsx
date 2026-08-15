import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fetchBrands } from "../modules/brands/api";
import { BrandsPage } from "./BrandsPage";

let role = "user";
vi.mock("../modules/auth/AuthContext",()=>({useAuth:()=>({user:{role}})}));
vi.mock("../modules/brands/api",()=>({fetchBrands:vi.fn(),createBrand:vi.fn(),updateBrand:vi.fn(),deleteBrand:vi.fn()}));
describe("BrandsPage",()=>{beforeEach(()=>{role="user";vi.mocked(fetchBrands).mockResolvedValue({items:[],page:1,page_size:20,total:0,total_pages:0});});it("shows empty state and hides admin actions",async()=>{render(<MemoryRouter><BrandsPage/></MemoryRouter>);expect(await screen.findByText("No brands found.")).toBeInTheDocument();expect(screen.queryByText("Add Brand")).not.toBeInTheDocument();});it("shows badges and admin actions",async()=>{role="admin";vi.mocked(fetchBrands).mockResolvedValue({items:[{id:"b1",brand_code:"chanel",brand_name:"CHANEL",luxury_tier:"ultra_luxury",official_site_url:null,online_purchase_policy:"research_only",purchase_restriction_notes:null,is_research_enabled:true,is_active:true,created_at:"2026-01-01",updated_at:"2026-01-01"}],page:1,page_size:20,total:1,total_pages:1});render(<MemoryRouter><BrandsPage/></MemoryRouter>);await waitFor(()=>expect(screen.getByText("CHANEL")).toBeInTheDocument());expect(screen.getAllByText("Research Only").length).toBeGreaterThan(0);expect(screen.getByText("Add Brand")).toBeInTheDocument();expect(screen.getByText("Edit")).toBeInTheDocument();});});
