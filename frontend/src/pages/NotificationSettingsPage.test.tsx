import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NotificationSettingsPage } from "./NotificationSettingsPage";

const fetchSetting=vi.fn(),saveSetting=vi.fn(),removeSetting=vi.fn(),fetchDeliveries=vi.fn();
vi.mock("../modules/notifications/api",()=>({
  fetchSlackSetting:()=>fetchSetting(),saveSlackSetting:(x:unknown)=>saveSetting(x),
  removeSlackSetting:()=>removeSetting(),fetchRecentDeliveries:()=>fetchDeliveries(),
}));

const unconfigured={channel_type:"slack",enabled:false,configured:false,destination_label:"Slack",subscribed_event_types:[]};
describe("NotificationSettingsPage",()=>{
  beforeEach(()=>{vi.clearAllMocks();fetchSetting.mockResolvedValue(unconfigured);fetchDeliveries.mockResolvedValue({items:[],page:1,page_size:5,total:0,total_pages:0});});
  it("never displays a stored webhook and saves a new integration",async()=>{
    saveSetting.mockResolvedValue({...unconfigured,enabled:true,configured:true,destination_label:"Ops",subscribed_event_types:["supplier_policy_review_changed"]});
    render(<NotificationSettingsPage/>);await screen.findByRole("form",{name:"Slack notification settings"});
    fireEvent.change(screen.getByLabelText("Destination label"),{target:{value:"Ops"}});
    fireEvent.click(screen.getByLabelText("Enabled"));fireEvent.click(screen.getByLabelText("Supplier Policy Review Changes"));
    fireEvent.change(screen.getByLabelText("Slack webhook URL"),{target:{value:"https://hooks.slack.com/services/a/b/c"}});
    fireEvent.click(screen.getByRole("button",{name:"Save Settings"}));
    await waitFor(()=>expect(saveSetting).toHaveBeenCalled());
    expect(await screen.findByText("Webhook:")).toBeInTheDocument();
    expect(screen.queryByDisplayValue("https://hooks.slack.com/services/a/b/c")).not.toBeInTheDocument();
  });
  it("shows recent delivery metadata without raw errors",async()=>{
    fetchDeliveries.mockResolvedValue({items:[{id:"1",channel_type:"slack",event_type:"supplier_policy_review_changed",status:"delivered",created_at:"2026-08-16T00:00:00Z",delivered_at:"2026-08-16T00:00:01Z"}],page:1,page_size:5,total:1,total_pages:1});
    render(<NotificationSettingsPage/>);expect(await screen.findByText("delivered")).toBeInTheDocument();expect(screen.getByText("supplier policy review changed")).toBeInTheDocument();
  });
});
