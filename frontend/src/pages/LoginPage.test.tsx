import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { LoginPage } from "./LoginPage";

const loginMock = vi.fn();

vi.mock("../modules/auth/AuthContext", () => ({
  useAuth: () => ({
    status: "unauthenticated",
    user: null,
    login: loginMock,
    logout: vi.fn(),
  }),
}));

describe("LoginPage", () => {
  it("validates fields before submit", async () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Login" }));

    expect(
      screen.getByText("メールアドレスを入力してください。"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("パスワードを入力してください。"),
    ).toBeInTheDocument();
  });

  it("submits and redirects after successful login", async () => {
    loginMock.mockResolvedValueOnce(undefined);

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/knowledge-bases" element={<div>kb list</div>} />
        </Routes>
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "user@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "password" },
    });
    fireEvent.submit(screen.getByRole("button", { name: "Login" }).closest("form")!);

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith({
        email: "user@example.com",
        password: "password",
      });
    });
  });
});
