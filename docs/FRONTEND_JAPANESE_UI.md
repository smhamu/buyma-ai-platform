# Frontend 日本語UI方針

ユーザーが操作・参照する画面文言、フォームラベル、accessible name、状態・確認・エラーメッセージは自然な日本語で表示します。日時・金額・割合は原則として `ja-JP` で整形します。

API field、DB値、Enum、error codeは互換性維持のため翻訳しません。Frontendでは共通の `label()` とエラーコード対応表を通して表示時だけ日本語へ変換します。BUYMA、Slack、LINE、Email、URL、API、CSV、JSON-LD、Webhook、Product Code、SKU、VAT、Adminなどの固有名詞・技術用語は必要に応じてそのまま使用します。

新しい画面では本文だけでなく、`aria-label`、ボタン名、フォームラベル、placeholder、title、alt、dialog名も日本語にします。テストは日本語のaccessible nameを参照し、内部値を検証する場合だけ元のEnum値を使用します。
