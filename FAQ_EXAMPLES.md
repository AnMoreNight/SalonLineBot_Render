# FAQ Examples Based on KB Data

This document shows example FAQs that the salon LINE bot can handle based on the KB data structure.

## 📍 Address & Location FAQs

### Basic Address Questions
- **Q: 住所はどこですか？** → **A: 住所は「東京都渋谷区神宮前4-3-10 グリーン表参道ビル2F」です。**
- **Q: お店の場所を教えて** → **A: 住所は「東京都渋谷区神宮前4-3-10 グリーン表参道ビル2F」です。**
- **Q: 所在地は？** → **A: 住所は「東京都渋谷区神宮前4-3-10 グリーン表参道ビル2F」です。**

### Access Information
- **Q: 最寄り駅はどこ？** → **A: 最寄りは「表参道駅A1出口 徒歩3分（青山通り沿い｜伊藤病院向かい）」です。**
- **Q: 駅からの道順は？** → **A: 表参道駅A1出口→地上に出て右（外苑前方面）へ直進約200m→左手のカフェが目印→そのビル2F**
- **Q: アクセス方法を教えて** → **A: 最寄りは「表参道駅A1出口 徒歩3分（青山通り沿い｜伊藤病院向かい）」です。**

### Parking Information
- **Q: 駐車場はありますか？** → **A: 駐車場は「提携なし／近隣コインP（表参道ヒルズP・NPC外苑前P）あり」です。**
- **Q: 車で行けますか？** → **A: 駐車場は「提携なし／近隣コインP（表参道ヒルズP・NPC外苑前P）あり」です。**

## 📱 SNS & Contact FAQs

### SNS Accounts
- **Q: SNSアカウントはありますか？** → **A: 公式LINE（@salonai_omotesando）／Instagram（@salonai_omotesando）です。**
- **Q: Instagramは？** → **A: 公式LINE（@salonai_omotesando）／Instagram（@salonai_omotesando）です。**
- **Q: 公式アカウントを教えて** → **A: 公式LINE（@salonai_omotesando）／Instagram（@salonai_omotesando）です。**

### Contact Information
- **Q: 電話番号を教えて** → **A: お電話は「03-1234-5678」までお願いいたします。**
- **Q: 連絡先は？** → **A: お電話は「03-1234-5678」までお願いいたします。**

## 🕒 Business Hours & Workday FAQs

### Regular Business Hours
- **Q: 営業時間を教えて** → **A: 営業時間は「平日 10:00–19:00（最終受付18:30）」です。**
- **Q: 平日の営業時間は？** → **A: 営業時間は「平日 10:00–19:00（最終受付18:30）」です。**
- **Q: 土日の営業時間は？** → **A: 営業時間は「土日祝 10:00–18:00（最終受付17:30）」です。**

### Holiday Information
- **Q: 定休日はいつですか？** → **A: 定休日は「毎週火曜・第2水曜（臨時は公式LINEで告知）」です。**
- **Q: 休みの日は？** → **A: 定休日は「毎週火曜・第2水曜（臨時は公式LINEで告知）」です。**
- **Q: 今日は営業していますか？** → **A: 定休日は「毎週火曜・第2水曜（臨時は公式LINEで告知）」です。**

### Busy Times
- **Q: 混みやすい時間帯は？** → **A: 土日祝の11:00–15:00が混みやすい。平日午前は比較的取りやすい**
- **Q: 空いている時間は？** → **A: 土日祝の11:00–15:00が混みやすい。平日午前は比較的取りやすい**

## 💳 Payment & Booking FAQs

### Payment Methods
- **Q: 支払い方法は？** → **A: 支払い方法は「現金／クレジット（VISA・Mastercard・AMEX・JCB）／交通系IC／iD／QUICPay／PayPay」です。**
- **Q: キャッシュレスは使えますか？** → **A: 支払い方法は「現金／クレジット（VISA・Mastercard・AMEX・JCB）／交通系IC／iD／QUICPay／PayPay」です。**

### Booking Information
- **Q: 予約方法を教えて** → **A: 公式LINEから希望日時・メニューを選択→空き枠を提示→確定**
- **Q: どうやって予約するの？** → **A: 公式LINEから希望日時・メニューを選択→空き枠を提示→確定**
- **Q: 当日予約は可能？** → **A: 空きがあれば可（LINEでリアルタイム表示）**

### Cancellation Policy
- **Q: キャンセルはできますか？** → **A: キャンセル規定は「来店の2時間前まで無料／以降は100％（無断は次回受付制限あり）」です。**
- **Q: キャンセル料は？** → **A: キャンセル規定は「来店の2時間前まで無料／以降は100％（無断は次回受付制限あり）」です。**

## 👥 Accessibility & Special Needs FAQs

### Children & Family
- **Q: 子連れで行けますか？** → **A: 可（ベビーカーOK／簡易キッズチェアあり）**
- **Q: 子どもと一緒に行けますか？** → **A: 可（ベビーカーOK／簡易キッズチェアあり）**

### Accessibility
- **Q: バリアフリーですか？** → **A: 店内段差なし、エレベーターあり。車椅子は事前連絡で動線を案内**
- **Q: 車椅子で行けますか？** → **A: 店内段差なし、エレベーターあり。車椅子は事前連絡で動線を案内**

### Pet Policy
- **Q: ペット同伴は可能ですか？** → **A: 衛生上、原則不可（補助犬は可）**

## 🚫 Examples of Queries That Should Return "分かりません"

### Medical/Safety Questions
- **Q: アレルギーがあるのですが大丈夫ですか？** → **A: 安全のため、パッチテスト・薬剤調整を提案。無理はしない方針。詳細はスタッフにお繋ぎします。**
- **Q: 妊娠中でもカラー可能ですか？** → **A: 安全のため、体調と医師の指示を優先。無理はせず当日も遠慮なくご相談を。詳細はスタッフにお繋ぎします。**

### Out-of-Scope Questions
- **Q: 明日の天気は？** → **A: 申し訳ございませんが、その質問については分かりません。スタッフにお繋ぎします。**
- **Q: 近くの競合店より安くできますか？** → **A: 申し訳ございませんが、その質問については分かりません。スタッフにお繋ぎします。**
- **Q: 店長の自宅住所を教えて** → **A: 申し訳ございませんが、その質問については分かりません。スタッフにお繋ぎします。**

## 🔧 Technical Implementation Notes

### KB Key Mapping
The system maps Japanese queries to English KB keys:
- **住所** → `ADDRESS`
- **営業時間** → `BUSINESS_HOURS_WEEKDAY`, `BUSINESS_HOURS_WEEKEND`
- **SNS** → `SNS`
- **支払い** → `PAYMENTS`
- **予約** → `BOOKING_METHOD`
- **キャンセル** → `CANCEL_POLICY`

### Response Generation
- **Natural Japanese responses** based on KB data
- **Contextual formatting** (e.g., "店名は「...」です")
- **Safety redirects** for medical/sensitive queries
- **"分かりません"** for out-of-scope questions

### Categories
- **基本情報**: SALON_NAME, ADDRESS, PHONE
- **営業時間**: BUSINESS_HOURS_WEEKDAY, BUSINESS_HOURS_WEEKEND, HOLIDAY
- **アクセス**: ACCESS_STATION, PARKING, ACCESS_DETAIL
- **支払い**: PAYMENTS
- **予約**: BOOKING_METHOD, CANCEL_POLICY
- **安全**: ALLERGY_CARE, PREGNANCY_CARE
