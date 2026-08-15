import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import { Pagination } from "../ui/Pagination";
import { label } from "../../modules/product-research/format";
import { createPolicyEvidence, fetchLatestPolicyEvidence, fetchPolicyEvidence } from "../../modules/suppliers/api";
import type { EvidenceResult, EvidenceType, PolicyEvidenceSummary, Supplier, SupplierPolicyEvidenceInput, SupplierPolicyEvidencePage } from "../../modules/suppliers/types";

const evidenceTypes: EvidenceType[] = ["terms","robots","vat","shipping","official_api","buyma","ingestion","resale_restriction","other"];
const evidenceResultsByType: Record<EvidenceType,EvidenceResult[]> = {
  terms:["allowed","restricted","prohibited","unknown"], robots:["allowed","restricted","disallowed","unknown"],
  vat:["included","excluded_for_export","not_refunded","unknown"], shipping:["supported","unsupported","confirmed","unconfirmed","unknown"],
  official_api:["supported","unsupported","confirmed","unconfirmed","unknown"], buyma:["unchecked","allowed","caution","prohibited","unknown"],
  ingestion:["manual","url_manual","csv","official_api","structured_data","html_parser","disabled","supported","unsupported","unknown"],
  resale_restriction:["allowed","restricted","prohibited","confirmed","unconfirmed","unknown"],
  other:["allowed","restricted","prohibited","disallowed","supported","unsupported","confirmed","unconfirmed","unknown"],
};

const initialInput = (): SupplierPolicyEvidenceInput => ({
  evidence_type:"terms", result:"unknown", source_url:null, source_title:null,
  source_excerpt:null, evidence_notes:"", checked_at:new Date().toISOString(),
});

export function SupplierPolicyEvidencePanel({supplier,onClose}:{supplier:Supplier;onClose:()=>void}) {
  const [history,setHistory]=useState<SupplierPolicyEvidencePage|null>(null);
  const [summary,setSummary]=useState<PolicyEvidenceSummary|null>(null);
  const [page,setPage]=useState(1);
  const [pageSize,setPageSize]=useState(20);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");
  const [form,setForm]=useState(initialInput);
  const [saving,setSaving]=useState(false);
  const load=useCallback(async()=>{
    setLoading(true);
    try {
      const [nextHistory,nextSummary]=await Promise.all([fetchPolicyEvidence(supplier.id,page,pageSize),fetchLatestPolicyEvidence(supplier.id)]);
      setHistory(nextHistory);setSummary(nextSummary);setError("");
    } catch(e) {setError(e instanceof Error?e.message:"Failed to load policy evidence.");}
    finally {setLoading(false);}
  },[page,pageSize,supplier.id]);
  useEffect(()=>{void load();},[load]);
  const field=<K extends keyof SupplierPolicyEvidenceInput>(key:K,value:SupplierPolicyEvidenceInput[K])=>setForm((current)=>({...current,[key]:value}));
  const submit=async(e:FormEvent)=>{
    e.preventDefault();setSaving(true);setError("");
    try {await createPolicyEvidence(supplier.id,form);setForm(initialInput());setPage(1);await load();}
    catch(x){setError(x instanceof Error?x.message:"Failed to add evidence.");}
    finally{setSaving(false);}
  };
  return <div className="modal-backdrop"><section className="modal-panel research-form" aria-label="Policy Evidence">
    <div className="modal-panel__header"><div><h2>Policy Evidence</h2><p>{supplier.name}</p></div><button className="secondary-button" onClick={onClose}>Close</button></div>
    <p className="subtle">Evidence records why a policy was researched. Adding evidence does not automatically change the supplier policy.</p>
    {error&&<div className="form-error-banner">{error}</div>}
    <section aria-label="Latest policy evidence"><h3>Latest Evidence</h3>
      {loading&&!summary?<div className="page-status">Loading policy evidence...</div>:summary&&<div className="stats-grid">
        {Object.entries(summary).map(([type,item])=><article className="stat-card" key={type}>
          <strong>{label(type)}</strong><div>Current Policy: {label(String(item.current))}</div><div>Latest Evidence: {item.latest_evidence?label(item.latest_evidence):"No evidence"}</div>
          {item.checked_at&&<div>Checked: {new Date(item.checked_at).toLocaleDateString()} ({item.age_days} days ago)</div>}
          <div>{item.consistent===true?"Up to date":item.consistent===false?"Review required":"No evidence"}</div>
          {item.is_stale===true&&<div>Review recommended</div>}
        </article>)}
      </div>}
    </section>
    <form aria-label="Add policy evidence" onSubmit={(e)=>void submit(e)}><h3>Add Evidence</h3>
      <div className="form-grid">
        <label className="form-field">Evidence Type<select className="form-field__input" value={form.evidence_type} onChange={(e)=>{const type=e.target.value as EvidenceType;setForm(current=>({...current,evidence_type:type,result:evidenceResultsByType[type][0]}));}}>{evidenceTypes.map(x=><option key={x} value={x}>{label(x)}</option>)}</select></label>
        <label className="form-field">Result<select className="form-field__input" value={form.result} onChange={(e)=>field("result",e.target.value as EvidenceResult)}>{evidenceResultsByType[form.evidence_type].map(x=><option key={x} value={x}>{label(x)}</option>)}</select></label>
        <label className="form-field">Source URL<input className="form-field__input" type="url" maxLength={2048} value={form.source_url??""} onChange={(e)=>field("source_url",e.target.value||null)}/></label>
        <label className="form-field">Checked At<input className="form-field__input" type="datetime-local" value={form.checked_at.slice(0,16)} onChange={(e)=>field("checked_at",new Date(e.target.value).toISOString())} required/></label>
      </div>
      <label className="form-field">Notes<textarea className="form-field__input" maxLength={4000} value={form.evidence_notes} onChange={(e)=>field("evidence_notes",e.target.value)} required/></label>
      <div className="subtle">Checked By: current authenticated user</div>
      <button className="primary-button" disabled={saving}>{saving?"Adding...":"Add Evidence"}</button>
    </form>
    <section aria-label="Evidence history"><h3>Evidence History</h3>
      {!loading&&!history?.items.length?<div className="panel panel--empty">No policy evidence recorded.</div>:history&&<><div className="table-wrapper"><table className="data-table"><thead><tr><th>Type</th><th>Result</th><th>Source</th><th>Checked At</th><th>Checked By</th><th>Notes</th></tr></thead><tbody>{history.items.map(item=><tr key={item.id}><td>{label(item.evidence_type)}</td><td>{label(item.result)}</td><td>{item.source_url?<a href={item.source_url} target="_blank" rel="noopener noreferrer">Source</a>:"-"}</td><td>{new Date(item.checked_at).toLocaleString()}</td><td>{item.checked_by_username}</td><td>{item.evidence_notes}</td></tr>)}</tbody></table></div><Pagination page={history} onPage={setPage} onPageSize={(size)=>{setPageSize(size);setPage(1);}}/></>}
    </section>
  </section></div>;
}
