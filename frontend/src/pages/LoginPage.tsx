import { FormEvent, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ApiClientError } from "../lib/api";
import { useAuth } from "../modules/auth/AuthContext";

export function LoginPage() {
  const {login}=useAuth();const navigate=useNavigate();const location=useLocation();
  const[email,setEmail]=useState("");const[password,setPassword]=useState("");const[errors,setErrors]=useState<{email?:string;password?:string}>({});const[apiError,setApiError]=useState<string|null>(null);const[isSubmitting,setIsSubmitting]=useState(false);
  const redirectTo=useMemo(()=>{const state=location.state as {from?:{pathname?:string}}|null;return state?.from?.pathname||"/knowledge-bases";},[location.state]);
  const validate=()=>{const next:{email?:string;password?:string}={};if(!email.trim())next.email="メールアドレスを入力してください。";if(!password.trim())next.password="パスワードを入力してください。";setErrors(next);return Object.keys(next).length===0;};
  const submit=async(event:FormEvent<HTMLFormElement>)=>{event.preventDefault();setApiError(null);if(!validate())return;setIsSubmitting(true);try{await login({email:email.trim(),password});navigate(redirectTo,{replace:true});}catch(error){setApiError(error instanceof ApiClientError?error.message:"ログインに失敗しました。");}finally{setIsSubmitting(false);}};
  return <div className="auth-page"><div className="auth-card"><h1 className="auth-card__title">BUYMA AI Platform</h1><p className="auth-card__description">管理画面へログインしてください。</p><form className="auth-form" onSubmit={e=>void submit(e)}><label className="form-field"><span className="form-field__label">メールアドレス</span><input className="form-field__input" type="email" name="email" autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} aria-invalid={Boolean(errors.email)}/>{errors.email&&<span className="form-field__error">{errors.email}</span>}</label><label className="form-field"><span className="form-field__label">パスワード</span><input className="form-field__input" type="password" name="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} aria-invalid={Boolean(errors.password)}/>{errors.password&&<span className="form-field__error">{errors.password}</span>}</label>{apiError&&<div className="form-error-banner">{apiError}</div>}<button className="primary-button" type="submit" disabled={isSubmitting}>{isSubmitting?"ログイン中...":"ログイン"}</button></form></div></div>;
}
