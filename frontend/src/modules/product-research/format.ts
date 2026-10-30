export function money(value: string | null | undefined, currency = "JPY") {
  if (value == null) return "-";
  const number = Number(value);
  return Number.isFinite(number) ? new Intl.NumberFormat("ja-JP", { style: "currency", currency, maximumFractionDigits: currency === "JPY" ? 0 : 2 }).format(number) : value;
}
export function percent(value: string | null | undefined) {
  if (value == null) return "-";
  const number = Number(value);
  return Number.isFinite(number) ? new Intl.NumberFormat("ja-JP", { style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(number) : value;
}
const LABELS: Record<string, string> = {
  unknown: "未確認", normal: "通常", limited: "制限あり", restricted: "制限あり", category_limited: "カテゴリ別制限", boutique_only: "店舗限定", research_only: "調査のみ",
  pre_order: "予約商品", preorder: "予約商品", personalized: "パーソナライズ商品", made_to_order: "受注生産", client_advisor_only: "担当者への問い合わせ限定",
  pending: "処理待ち", processing: "処理中", ready: "準備完了", failed: "失敗", cancelled: "キャンセル", expanded: "配信展開済み", delivered: "配信済み",
  active: "有効", inactive: "無効", enabled: "有効", disabled: "無効", configured: "設定済み", not_configured: "未設定",
  review_due: "再確認期限超過", up_to_date: "最新", no_evidence: "根拠未登録", inconsistent: "不整合", needs_review: "要確認", review_required: "確認が必要",
  discovered: "発見済み", reviewing: "確認中", approved: "承認済み", profitable: "利益あり", unprofitable: "利益なし", rejected: "却下", ready_for_listing: "出品準備完了",
  in_stock: "在庫あり", out_of_stock: "在庫なし", fetched: "取得済み", normalized: "正規化済み", matched: "照合済み", candidate_created: "候補作成済み", file: "ファイル", manual: "手動", url_manual: "手動URL", csv: "CSV", csv_import: "CSV取込",
  structured_data: "構造化データ", html_parser: "HTML解析", official_api: "公式API", included: "VAT込み", excluded_for_export: "輸出時VAT除外", not_refunded: "VAT返金なし",
  unchecked: "未確認", allowed: "許可", caution: "注意", prohibited: "禁止", disallowed: "不許可", terms: "利用規約", robots: "robots.txt", shipping: "配送", vat: "VAT", buyma: "BUYMA", api: "API",
  ingestion: "取込", resale_restriction: "再販売制限", unsupported: "非対応", success: "成功", duplicate: "重複", manual_review: "手動確認", consistent: "整合", stale: "期限超過", fresh: "最新",
  initial_evaluation: "初回評価", supplier_policy_review_changed: "仕入先ポリシーレビューの変更", authorized_retailer: "正規取扱店", department_store: "百貨店", boutique: "ブティック", marketplace: "マーケットプレイス", other: "その他", ultra_luxury: "最高級", luxury: "ラグジュアリー", premium: "プレミアム",
};
export const label = (value: string) => LABELS[value] ?? value.split("_").join(" ");
export const formatDate = (value: string) => new Intl.DateTimeFormat("ja-JP").format(new Date(value));
export const formatDateTime = (value: string) => new Intl.DateTimeFormat("ja-JP", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
