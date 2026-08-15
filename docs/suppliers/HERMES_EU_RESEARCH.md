# Hermès EU Official Online Supplier Research

調査日: 2026-08-15

## 結論

France、Germany、Italy、Spainはいずれも、現時点では `url_manual` を採用する。公開商品ページに価格、商品コード、在庫、variant情報およびJSON-LDが含まれることは確認できるが、Hermèsから自動取得についての明示的な許可や公開Product APIは確認できなかった。利用規約にはサイトコンテンツの複製、公開、配布、派生利用を制限する記載があるため、`automated_fetch_enabled=false` を維持する。

robots.txtは法的・契約上の許可ではなく、今回の判断材料の一つとしてのみ扱う。

## 国別比較

| 国 | Official URL | 通貨 | 日本直送 | VAT | 商品HTML | JSON-LD Product | 推奨Source Type |
|---|---|---|---|---|---|---|---|
| France | `https://www.hermes.com/fr/fr/` | EUR | なし | 税込、EU外転送でもVAT返金なし | 代表商品で200 | 代表商品で確認 | `url_manual` |
| Germany | `https://www.hermes.com/de/de/` | EUR | なし | 税込、EU外転送でもVAT返金なし | 代表商品で200 | 代表商品で確認 | `url_manual` |
| Italy | `https://www.hermes.com/it/it/` | EUR | なし | 税込、VAT返金なし | 検索結果で商品・価格を確認。直接調査はアクセス拒否 | 未確定 | `url_manual` |
| Spain | `https://www.hermes.com/es/es/` | EUR | なし | 税込、EU外転送でもVAT返金なし | 公式商品ページと価格を確認。直接調査はアクセス拒否 | 未確定 | `url_manual` |

配送対象は欧州の指定国に限定され、日本は含まれない。転送業者宛の配送も販売条件で認められていないため、`ships_to_japan=false` とする。

## 取得可能フィールド

代表商品 `V38290` のFrance/Germany公開HTMLで、次の存在を確認した。値の継続的な安定性は未保証である。

| フィールド | 状況 |
|---|---|
| Product name | HTML/構造化データから確認可能 |
| SKU / product code | URL末尾および構造化データ内で確認可能 |
| Price | 確認可能 |
| Currency | EURを確認可能 |
| Availability | 構造化された在庫表現を確認可能 |
| Canonical URL | locale別canonicalを確認 |
| Color / size / variant | 商品により存在。代表HTMLにvariant関連データあり |

France/Germanyは同じ商品コードでもlocale別canonical URLを返す。Italy/Spainについて同じ内部構造を推測で確定せず、手動ブラウザでの追加確認を残課題とする。

## JSON-LD調査

- France: `application/ld+json`および`@type: Product`を確認。
- Germany: `application/ld+json`および`@type: Product`を確認。
- Italy: 今回の直接GETは拒否されたため未確定。
- Spain: 今回の直接GETは拒否されたため未確定。検索エンジンが公式商品ページの商品名と価格を取得できることだけ確認。

JSON-LDが技術的に取得可能であっても、自動利用の許可を意味しない。そのため `structured_data` は設定しない。

## Official / Public API調査

公式サイト、販売条件、利用条件および公開検索結果から、一般向けの商品カタログ・価格・在庫APIは確認できなかった。内部ネットワークAPIがブラウザから見える場合でも、それをofficial/public APIとは扱わない。

`official_api_available=false` とする。

## robots.txt調査

`https://www.hermes.com/robots.txt` を2026-08-15に1回確認した。

- `User-agent: *`
- 管理、checkout、customer、search、内部catalog routeなど多数をDisallow。
- 公開locale商品URLの `/fr/fr/product/...`、`/de/de/product/...` 等を直接禁止する規則は確認されなかった。
- `/catalog/product/view/` はDisallowされており、内部routeへアクセスしてはならない。

Supplierの `robots_status` は公開商品URLという限定スコープでは `allowed` とする。ただし自動取得許可ではなく、robots変更時には再確認する。

## Terms / Site Usage Policy

France、Germany、Italy、Spainの利用条件は、サイト要素がHermèsグループ等の知的財産であり、明示された例外を除き、全部または一部の複製、公開、送信、変更、販売、配布、派生物作成等を制限している。自動化された商用商品収集を明示的に許可する条項は確認できなかった。

したがって `terms_status=restricted` とする。自動取得を検討する場合は、Hermèsからの書面による許可または正式な契約/API提供を確認する必要がある。

## VATと価格

4か国の販売条件は、商品価格をEUR・税込としている。Germany/Spainでは、購入後にEU外へ転送してもサイト購入に適用されたVATを返金しない旨が明記され、ItalyでもVATを返金しない旨が記載されている。Franceも同じEU販売条件体系で税込・VAT非返金として扱う。

Supplier Policyは次のとおりとする。

- `default_currency=EUR`
- `vat_policy=not_refunded`
- `vat_rate=null`（商品価格からの自動控除に使わない）
- `ships_to_japan=false`

## 推奨Supplier Policy

4 Supplierすべてに次を設定する。

```text
supplier_type=authorized_retailer
default_currency=EUR
ships_to_japan=false
vat_policy=not_refunded
buyma_allowed_status=unchecked
research_status=reviewing
ingestion_source_type=url_manual
automated_fetch_enabled=false
terms_status=restricted
robots_status=allowed
official_api_available=false
parser_key=null
request_interval_seconds=null
```

正規公式サイトであることと、BUYMA買付先として利用可能であることは別判断である。BUYMA側の最新ルール確認前は `buyma_allowed_status=unchecked` を維持する。

## Seed

`backend/scripts/seed_hermes_eu_suppliers.py` はownerとなるactive Adminを対話入力で選び、Hermès Brandに4 Supplierを関連付ける。

```bash
cd backend
python scripts/seed_luxury_brands.py
python scripts/seed_hermes_eu_suppliers.py
```

同一owner・同一Supplier名が存在する場合は作成せず、既存レコードを更新・上書きしない。

## 自動取得可否

現時点では不可。次のいずれかが得られるまで `automated_fetch_enabled=false` を変更しない。

1. Hermèsからの書面による自動取得許可。
2. 利用条件を伴う公式Public APIまたはPartner API契約。
3. 法務・コンプライアンス確認と、最新Terms/robots双方の再確認。

## 残課題

- Italy/Spain商品ページのJSON-LDを通常ブラウザで手動確認する。
- Hermèsへ商品データ利用およびAPI提供可否を問い合わせる。
- BUYMAの最新買付先ルールを確認する。
- Terms/robotsの定期的な再確認日を運用に組み込む。
- 国・カテゴリ・商品ごとの配送制限を手動確認する。
- VAT、輸出販売、転送業者禁止について税務・運用判断を行う。

## 参照した公式ページ

- [Hermès France 利用条件](https://www.hermes.com/fr/fr/legal/6405-conditions-generales-dutilisation/)
- [Hermès Germany 販売条件](https://www.hermes.com/de/de/legal/allgemeine-geschaftsbedingungen-de/)
- [Hermès Germany 利用条件](https://www.hermes.com/de/de/legal/6569-allgemeine-nutzungsbedingungen-der-webseite/)
- [Hermès Italy 販売条件](https://www.hermes.com/it/it/legal/6598-condizioni-generali-di-vendita/)
- [Hermès Italy 利用条件](https://www.hermes.com/it/it/legal/6599-condizioni-generali-di-utilizzo/)
- [Hermès Spain 販売条件](https://www.hermes.com/es/es/legal/6575-condiciones-generales-de-venta/)
- [Hermès Spain 利用条件](https://www.hermes.com/es/es/legal/6580-terminos-y-condiciones-generales-de-uso-del-sitio-hermescom/)
- [Hermès Spain 代表商品ページ](https://www.hermes.com/es/es/product/eau-d-hermes-eau-de-toilette-V38290/)
- [Hermès robots.txt](https://www.hermes.com/robots.txt)
