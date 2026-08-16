import { FormEvent, useEffect, useState } from "react";
import { Badge } from "../components/ui/Badge";
import { fetchRecentDeliveries, fetchSlackSetting, removeSlackSetting, saveSlackSetting } from "../modules/notifications/api";
import type { NotificationDelivery, SlackChannelSetting } from "../modules/notifications/types";

const empty:SlackChannelSetting={channel_type:"slack",enabled:false,configured:false,destination_label:"Slack",subscribed_event_types:[]};

export function NotificationSettingsPage(){
  const [setting,setSetting]=useState(empty);const [deliveries,setDeliveries]=useState<NotificationDelivery[]>([]);
  const [webhook,setWebhook]=useState("");const [changing,setChanging]=useState(false);const [loading,setLoading]=useState(true);const [saving,setSaving]=useState(false);const [error,setError]=useState("");const [notice,setNotice]=useState("");
  useEffect(()=>{void Promise.all([fetchSlackSetting(),fetchRecentDeliveries()]).then(([s,d])=>{setSetting(s);setDeliveries(d.items);}).catch(e=>setError(e instanceof Error?e.message:"Failed to load notification settings.")).finally(()=>setLoading(false));},[]);
  const subscribed=setting.subscribed_event_types.includes("supplier_policy_review_changed");
  const submit=async(e:FormEvent)=>{e.preventDefault();setSaving(true);setError("");setNotice("");try{const saved=await saveSlackSetting({enabled:setting.enabled,webhook_url:webhook||undefined,destination_label:setting.destination_label,subscribed_event_types:subscribed?["supplier_policy_review_changed"]:[]});setSetting(saved);setWebhook("");setChanging(false);setNotice("Slack notification setting saved.");}catch(err){setError(err instanceof Error?err.message:"Failed to save Slack setting.");}finally{setSaving(false);}};
  const remove=async()=>{if(!window.confirm("Remove Slack integration? Pending deliveries will be cancelled."))return;setSaving(true);try{setSetting(await removeSlackSetting());setWebhook("");setChanging(false);setNotice("Slack integration removed.");setError("");}catch(err){setError(err instanceof Error?err.message:"Failed to remove Slack integration.");}finally{setSaving(false);}};
  if(loading)return <div className="page-status">Loading notification settings...</div>;
  return <section className="page-section"><div className="page-section__header"><div><h1>Notification Settings</h1><p>Manage user-specific operational notification destinations.</p></div></div>
    {error&&<div className="form-error-banner" role="alert">{error}</div>}{notice&&<div className="panel" role="status">{notice}</div>}
    <form className="panel notification-settings" aria-label="Slack notification settings" onSubmit={e=>void submit(e)}><div className="notification-settings__header"><div><h2>Slack Notifications</h2><Badge tone={setting.configured?"success":"warning"}>{setting.configured?"Configured":"Not configured"}</Badge></div></div>
      <label className="checkbox-field"><input type="checkbox" checked={setting.enabled} onChange={e=>setSetting({...setting,enabled:e.target.checked})}/>Enabled</label>
      <label className="form-field">Destination label<input className="form-field__input" required maxLength={100} value={setting.destination_label} onChange={e=>setSetting({...setting,destination_label:e.target.value})}/></label>
      <fieldset className="brand-picker"><legend>Events</legend><label className="checkbox-field"><input type="checkbox" checked={subscribed} onChange={e=>setSetting({...setting,subscribed_event_types:e.target.checked?["supplier_policy_review_changed"]:[]})}/>Supplier Policy Review Changes</label></fieldset>
      {(!setting.configured||changing)&&<label className="form-field">Slack webhook URL<input className="form-field__input" type="url" required={!setting.configured} value={webhook} onChange={e=>setWebhook(e.target.value)} autoComplete="off" placeholder="https://hooks.slack.com/services/..."/></label>}
      {setting.configured&&!changing&&<p><strong>Webhook:</strong> Configured</p>}
      <p className="form-help">Your Slack webhook URL is stored securely and is never displayed after saving.</p>
      <div className="row-actions"><button className="primary-button" disabled={saving}>{saving?"Saving...":"Save Settings"}</button>{setting.configured&&<button type="button" className="secondary-button" onClick={()=>setChanging(x=>!x)}>Change Webhook</button>}{setting.configured&&<button type="button" className="danger-button" onClick={()=>void remove()} disabled={saving}>Remove Slack Integration</button>}</div>
    </form>
    <section className="panel" aria-label="Recent deliveries"><h2>Recent Deliveries</h2>{deliveries.length?<div className="table-wrapper"><table className="data-table"><thead><tr><th>Status</th><th>Event</th><th>Channel</th><th>Created</th></tr></thead><tbody>{deliveries.map(x=><tr key={x.id}><td>{x.status}</td><td>{x.event_type.replace(/_/g," ")}</td><td>{x.channel_type}</td><td>{new Date(x.created_at).toLocaleString()}</td></tr>)}</tbody></table></div>:<p>No deliveries yet.</p>}</section>
  </section>;
}
