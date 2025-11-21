---
description: How to deploy the Thiruvalla Map to GitHub Pages
---

This workflow guides you through deploying your static HTML/JS map to GitHub Pages so it can be accessed by anyone via a public URL.

## Prerequisites
- A GitHub account.
- `git` installed on your computer.

## Steps

1.  **Initialize Git Repository** (if not already done)
    Open your terminal in the project folder (`/Users/devandev/Desktop/Thiruvalla`) and run:
    ```bash
    git init
    ```

2.  **Commit Your Files**
    Add all your project files to git:
    ```bash
    git add .
    git commit -m "Initial commit of Thiruvalla Map"
    ```

3.  **Create a Repository on GitHub**
    - Go to [github.com/new](https://github.com/new).
    - Name your repository (e.g., `thiruvalla-map`).
    - Make it **Public**.
    - Do **not** check "Initialize with README" (since you have local files).
    - Click **Create repository**.

4.  **Push to GitHub**
    Copy the commands shown on the GitHub page under "…or push an existing repository from the command line". They will look like this (replace `YOUR_USERNAME` with your actual GitHub username):
    ```bash
    git remote add origin https://github.com/YOUR_USERNAME/thiruvalla-map.git
    git branch -M main
    git push -u origin main
    ```

5.  **Enable GitHub Pages**
    - Go to your repository **Settings** tab on GitHub.
    - Click on **Pages** in the left sidebar.
    - Under **Build and deployment** > **Source**, select **Deploy from a branch**.
    - Under **Branch**, select `main` and `/ (root)`.
    - Click **Save**.

6.  **Access Your Site**
    - Wait a minute or two.
    - Refresh the Pages settings page.
    - You will see a link at the top: `Your site is live at https://YOUR_USERNAME.github.io/thiruvalla-map/`
    - Share this link with everyone!
