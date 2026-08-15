import { apiClient } from "../../lib/api";
import type { Candidate, CandidateInput, CandidatePage, CandidateQuery, PricePreview } from "./types";
const qs=(q:Record<string,unknown>)=>{const p=new URLSearchParams();Object.entries(q).forEach(([k,v])=>{if(v!==undefined&&v!=="")p.set(k,String(v));});return p.toString();};
export const fetchCandidates=(q:CandidateQuery={})=>apiClient.get<CandidatePage>(`/product-research-candidates?${qs(q)}`);
export const fetchCandidate=(id:string)=>apiClient.get<Candidate>(`/product-research-candidates/${id}`);
export const calculateCandidate=(body:CandidateInput)=>apiClient.post<PricePreview,CandidateInput>("/product-research-candidates/calculate",body);
export const createCandidate=(body:CandidateInput)=>apiClient.post<Candidate,CandidateInput>("/product-research-candidates",body);
export const updateCandidate=(id:string,body:Partial<CandidateInput>)=>apiClient.put<Candidate,Partial<CandidateInput>>(`/product-research-candidates/${id}`,body);
export const deleteCandidate=(id:string)=>apiClient.delete<{deleted:boolean}>(`/product-research-candidates/${id}`);
