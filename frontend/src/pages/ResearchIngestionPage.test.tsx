import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { fetchBrands } from "../modules/brands/api";
import { fetchResearchSources, importResearchCsv, registerResearchUrl } from "../modules/research-ingestion/api";
import { fetchSuppliers } from "../modules/suppliers/api";
import type { Supplier } from "../modules/suppliers/types";
import { ResearchIngestionPage } from "./ResearchIngestionPage";

vi.mock("../modules/brands/api",()=>({fetchBrands:vi.fn()}));
vi.mock("../modules/suppliers/api",()=>({fetchSuppliers:vi.fn()}));
vi.mock("../modules/research-ingestion/api",()=>({fetchResearchSources:vi.fn(),registerResearchUrl:vi.fn(),importResearchCsv:vi.fn(),createCandidateFromSource:vi.fn(),deleteResearchSource:vi.fn()}));

const page={items:[],page:1,page_size:20,total:0,total_pages:0};
const supplier={id:"supplier-1",name:"EU Shop",website_url:"https://shop.example",ingestion_source_type:"manual",automated_fetch_enabled:false} as Supplier;

describe("ResearchIngestionPage",()=>{
  beforeEach(()=>{vi.mocked(fetchBrands).mockResolvedValue({items:[],page:1,page_size:100,total:0,total_pages:0});vi.mocked(fetchSuppliers).mockResolvedValue({items:[supplier],page:1,page_size:100,total:1,total_pages:1});vi.mocked(fetchResearchSources).mockResolvedValue(page);});

  it("renders the empty state",async()=>{render(<MemoryRouter><ResearchIngestionPage/></MemoryRouter>);expect(await screen.findByText("No source products found.")).toBeVisible();});

  it("shows loading errors",async()=>{vi.mocked(fetchResearchSources).mockRejectedValue(new Error("Source API unavailable"));render(<MemoryRouter><ResearchIngestionPage/></MemoryRouter>);expect(await screen.findByText("Source API unavailable")).toBeVisible();});

  it("registers a URL without implying an automatic fetch",async()=>{vi.mocked(registerResearchUrl).mockResolvedValue({id:"source-1"} as never);render(<MemoryRouter><ResearchIngestionPage/></MemoryRouter>);fireEvent.click(await screen.findByRole("button",{name:"Add URL"}));fireEvent.change(screen.getByRole("combobox",{name:"Supplier"}),{target:{value:supplier.id}});expect(screen.getByText(/Automated fetching disabled/)).toBeVisible();fireEvent.change(screen.getByRole("textbox",{name:"Product URL"}),{target:{value:"https://shop.example/item/1"}});fireEvent.click(screen.getByRole("button",{name:"Register URL"}));await waitFor(()=>expect(registerResearchUrl).toHaveBeenCalledWith(supplier.id,"https://shop.example/item/1"));});

  it("shows row-level CSV results",async()=>{vi.mocked(importResearchCsv).mockResolvedValue({success_count:1,failed_count:1,duplicate_count:1,rows:[{row:2,status:"success",source_id:"s",message:null},{row:3,status:"failed",source_id:null,message:"Invalid row."},{row:4,status:"duplicate",source_id:null,message:"Already registered."}]});render(<MemoryRouter><ResearchIngestionPage/></MemoryRouter>);fireEvent.click(await screen.findByRole("button",{name:"CSV Import"}));const file=new File(["supplier,brand"],"products.csv",{type:"text/csv"});fireEvent.change(screen.getByLabelText("CSV file"),{target:{files:[file]}});fireEvent.submit(screen.getByRole("form",{name:"CSV import form"}));expect(await screen.findByText(/1 success.*1 failed.*1 duplicate/)).toBeVisible();expect(screen.getByText(/Row 3: failed/)).toBeVisible();});
});
