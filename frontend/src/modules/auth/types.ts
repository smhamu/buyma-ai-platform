export type LoginRequest = {
  email: string;
  password: string;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type RefreshTokenResponse = {
  access_token: string;
  token_type: string;
};

export type RefreshTokenRequest = {
  refresh_token: string;
};

export type CurrentUser = {
  id: string;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
};
