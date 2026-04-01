# Meta & Instagram Setup Guide 📸

This guide provides a step-by-step walkthrough for configuring the **Instagram Graph API** used by ArxivIntel to automate social publishing. Follow these 5 phases to obtain your IDs and Access Tokens.

---

## Phase 1: Social Identity 👤

Before using the API, you must have a **Facebook Page** and an **Instagram Business** account.

1.  **Create a Facebook Page**: Go to [facebook.com/pages/create](https://www.facebook.com/pages/create) and create a Page for your bot/brand.
2.  **Switch Instagram to Business**:
    -   Open your Instagram profile on a mobile device.
    -   Go to **Settings and Privacy** -> **Account Type and Tools**.
    -   Select **Switch to Professional Account** and choose **Business**.

---

## Phase 2: Linking Accounts 🔗

Linking ensures that your Facebook Page has the authority to publish to your Instagram account.

1.  Go to your **Facebook Page**.
2.  Select **Settings** -> **Linked Accounts**.
3.  Select **Instagram** and click **Connect Account**.
4.  Follow the prompts to log in and confirm the link.

---

## Phase 3: Meta App Registration 🛠️

1.  Go to the [Meta for Developers Dashboard](https://developers.facebook.com/apps/).
2.  Click **Create App** and select **Other** -> **Business**.
3.  Add **Instagram Graph API** to your app from the dashboard.
4.  In **Settings** -> **Basic**, copy your `META_APP_ID` and `META_APP_SECRET`.

---

## Phase 4: Long-lived Access Token 🔑

Short-lived tokens from the Explorer expire in 1 hour. You need a **Long-lived (60-day)** token.

### 1. Get Short-lived Token
-   Go to the [Graph API Explorer](https://developers.facebook.com/tools/explorer/).
-   Select your **App** and add these permissions:
    -   `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`.
-   Click **Generate Access Token** and copy it.

### 2. Exchange for Long-lived Token
Run this command in your terminal (replacing the placeholders):

```bash
curl -X GET "https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token&client_id={APP_ID}&client_secret={APP_SECRET}&fb_exchange_token={SHORT_TOKEN}"
```

The response will contain your `INSTAGRAM_ACCESS_TOKEN`. Save this!

---

## Phase 5: Finding your IDs 🔍

Use your new Long-lived Access Token to find your internal IDs.

### 1. Find your Page ID
Query the `me/accounts` endpoint in the [Explorer](https://developers.facebook.com/tools/explorer/):
-   **GET** `/me/accounts`
-   Look for the `id` of the Facebook Page you created in Phase 1.

### 2. Find your Instagram Business ID
Using that `PAGE_ID`, query:
-   **GET** `/{PAGE_ID}?fields=instagram_business_account`
-   The `instagram_business_account.id` is your `INSTAGRAM_BUSINESS_ACCOUNT_ID`.

---

## Summary of .env Variables

| Variable | Source |
| --- | --- |
| `META_APP_ID` | Meta App Dashboard (Settings > Basic) |
| `META_APP_SECRET` | Meta App Dashboard (Settings > Basic) |
| `INSTAGRAM_ACCESS_TOKEN` | Result of Phase 4 exchange |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Result of Phase 5 query |
| `INSTAGRAM_USERNAME` | Your @handle |
