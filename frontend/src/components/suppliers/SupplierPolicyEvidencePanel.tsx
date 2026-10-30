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
    } catch(e) {setError(e instanceof Error?e.message:"ポリシー根拠を読み込めませんでした。" );}
    finally {setLoading(false);}
  },[page,pageSize,supplier.id]);
  useEffect(()=>{void load();},[load]);
  const field=<K extends keyof SupplierPolicyEvidenceInput>(key:K,value:SupplierPolicyEvidenceInput[K])=>setForm((current)=>({...current,[key]:value}));
  const submit=async(e:FormEvent)=>{
    e.preventDefault();setSaving(true);setError("");
    try {await createPolicyEvidence(supplier.id,form);setForm(initialInput());setPage(1);await load();}
    catch(x){setError(x instanceof Error?x.message:"根拠を追加できませんでした。" );}
    finally{setSaving(false);}
  };
  return <div className="modal-backdrop"><section className="modal-panel research-form" aria-label="ポリシー根拠">
    <div className="modal-panel__header"><div><h2>ポリシー根拠</h2><p>{supplier.name}</p></div><button className="secondary-button" onClick={onClose}>閉じる</button></div>
    <p className="subtle">ポリシーを調査した根拠を記録します。根拠を追加しても仕入先ポリシーは自動変更されません。</p>
    {error&&<div className="form-error-banner">{error}</div>}
    <section aria-label="最新のポリシー根拠"><h3>最新の根拠</h3>
      {loading&&!summary?<div className="page-status">ポリシー根拠を読み込み中...</div>:summary&&<div className="stats-grid">
        {Object.entries(summary).map(([type,item])=><article className="stat-card" key={type}>
          <strong>{label(type)}</strong><div>現在のポリシー: {label(String(item.current))}</div><div>最新の根拠: {item.latest_evidence?label(item.latest_evidence):"根拠未登録"}</div>
          {item.checked_at&&<div>確認日: {new Date(item.checked_at).toLocaleDateString("ja-JP")}（{item.age_days}日前）</div>}
          <div>{item.consistent===true?"最新":item.consistent===false?"要確認":"根拠未登録"}</div>
          {item.is_stale===true&&<div>再確認を推奨</div>}
        </article>)}
      </div>}
    </section>
    <form aria-label="ポリシー根拠を追加" onSubmit={(e)=>void submit(e)}><h3>根拠を追加</h3>
      <div className="form-grid">
        <label className="form-field">根拠種別<select className="form-field__input" value={form.evidence_type} onChange={(e)=>{const type=e.target.value as EvidenceType;setForm(current=>({...current,evidence_type:type,result:evidenceResultsByType[type][0]}));}}>{evidenceTypes.map(x=><option key={x} value={x}>{label(x)}</option>)}</select></label>
        <label className="form-field">結果<select className="form-field__input" value={form.result} onChange={(e)=>field("result",e.target.value as EvidenceResult)}>{evidenceResultsByType[form.evidence_type].map(x=><option key={x} value={x}>{label(x)}</option>)}</select></label>
        <label className="form-field">出典URL<input className="form-field__input" type="url" maxLength={2048} value={form.source_url??""} onChange={(e)=>field("source_url",e.target.value||null)}/></label>
        <label className="form-field">確認日時<input className="form-field__input" type="datetime-local" value={form.checked_at.slice(0,16)} onChange={(e)=>field("checked_at",new Date(e.target.value).toISOString())} required/></label>
      </div>
      <label className="form-field">メモ<textarea className="form-field__input" maxLength={4000} value={form.evidence_notes} onChange={(e)=>field("evidence_notes",e.target.value)} required/></label>
      <div className="subtle">確認者: 現在ログイン中のユーザー</div>
      <button className="primary-button" disabled={saving}>{saving?"追加中...":"根拠を追加"}</button>
    </form>
    <section aria-label="根拠履歴"><h3>根拠履歴</h3>
      {!loading&&!history?.items.length?<div className="panel panel--empty">ポリシー根拠は登録されていません。</div>:history&&<><div className="table-wrapper"><table className="data-table"><thead><tr><th>種別</th><th>結果</th><th>出典</th><th>確認日時</th><th>確認者</th><th>メモ</th></tr></thead><tbody>{history.items.map(item=><tr key={item.id}><td>{label(item.evidence_type)}</td><td>{label(item.result)}</td><td>{item.source_url?<a href={item.source_url} target="_blank" rel="noopener noreferrer">出典</a>:"-"}</td><td>{new Date(item.checked_at).toLocaleString("ja-JP")}</td><td>{item.checked_by_username}</td><td>{item.evidence_notes}</td></tr>)}</tbody></table></div><Pagination page={history} onPage={setPage} onPageSize={(size)=>{setPageSize(size);setPage(1);}}/></>}
    </section>
  </section></div>;
}
