import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { IntegrationSettingsPage } from "./IntegrationSettingsPage";

const fetchSetting = vi.fn();
const saveToken = vi.fn();
const removeToken = vi.fn();

vi.mock("../modules/integration-settings/api", () => ({
  fetchRakutenSetting: () => fetchSetting(),
  saveRakutenToken: (body: unknown) => saveToken(body),
  removeRakutenToken: () => removeToken(),
}));

describe("IntegrationSettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchSetting.mockResolvedValue({ provider: "rakuten_product_search", configured: false });
  });

  it("stores a token and never renders it after saving", async () => {
    saveToken.mockResolvedValue({ provider: "rakuten_product_search", configured: true });
    render(<IntegrationSettingsPage />);
    await screen.findByRole("form", { name: "Rakuten API設定" });

    const secret = "private-rakuten-token";
    fireEvent.change(screen.getByLabelText("APIトークン"), { target: { value: secret } });
    fireEvent.click(screen.getByRole("button", { name: "トークンを保存" }));

    await waitFor(() => expect(saveToken).toHaveBeenCalledWith({ token: secret }));
    expect(await screen.findByText("Rakuten APIトークンを保存しました。")).toBeInTheDocument();
    expect(screen.queryByDisplayValue(secret)).not.toBeInTheDocument();
    expect(screen.getByText("設定済み", { selector: ".badge" })).toBeInTheDocument();
  });

  it("does not request or display a stored token", async () => {
    fetchSetting.mockResolvedValue({ provider: "rakuten_product_search", configured: true });
    render(<IntegrationSettingsPage />);
    await screen.findByRole("form", { name: "Rakuten API設定" });
    expect(screen.queryByLabelText("APIトークン")).not.toBeInTheDocument();
    expect(screen.getByText("トークンを変更")).toBeInTheDocument();
  });
});
