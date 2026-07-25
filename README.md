# Texas News Roundup — DFW Desk

A free, phone-friendly DFW news dashboard. GitHub Actions checks for stories every 30 minutes and GitHub Pages displays them as an installable Android web app.

## Included

- Dallas–Fort Worth breaking news
- Police, fire, traffic, weather, community and sports filters
- One-tap Facebook-ready caption copying
- Android Share button
- Original-source links
- Duplicate removal
- Mark-as-posted tracking on your phone
- Automatic collection every 30 minutes

## Free setup using GitHub

1. Create a free account at GitHub.com.
2. Create a new **public** repository named `texas-news-roundup-dfw`.
3. Upload every file and folder from this package to the repository.
4. Open the repository's **Settings**.
5. Select **Pages**.
6. Under **Build and deployment**, choose:
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/(root)**
7. Save.
8. Open the **Actions** tab.
9. Choose **Update DFW news** and press **Run workflow** once.
10. After the workflow finishes, return to **Settings → Pages** to see your app address.

The address will look similar to:

`https://YOUR-GITHUB-NAME.github.io/texas-news-roundup-dfw/`

## Add it to your Android home screen

1. Open the app address in Chrome.
2. Tap the three-dot Chrome menu.
3. Tap **Add to Home screen** or **Install app**.
4. Name it **DFW News Desk**.

## Using a story

1. Open the original source and verify the facts.
2. Expand **Facebook caption** if you want to edit it.
3. Tap **Copy caption** or **Share**.
4. Post through the Facebook app.
5. Return and tap **Mark posted**.

## Important limits

- Free GitHub scheduled jobs usually run close to the requested time, but they may be delayed during busy periods.
- This starter version links to publishers. It does not copy full articles or download copyrighted images or videos.
- Some sources may change their feeds or block aggregation.
- Review every headline and original article before publishing.
