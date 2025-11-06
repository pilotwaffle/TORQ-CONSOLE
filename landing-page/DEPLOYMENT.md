# TORQ-CONSOLE Landing Page Deployment Guide

This guide provides detailed instructions for deploying the TORQ-CONSOLE Phase 5 landing page to various hosting platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Option A: Vercel (Recommended)](#option-a-vercel-recommended)
4. [Option B: GitHub Pages](#option-b-github-pages)
5. [Option C: Netlify](#option-c-netlify)
6. [Option D: Azure Static Web Apps](#option-d-azure-static-web-apps)
7. [Custom Domain Configuration](#custom-domain-configuration)
8. [SEO Optimization Checklist](#seo-optimization-checklist)
9. [Performance Optimization](#performance-optimization)
10. [Analytics Setup](#analytics-setup)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

- [ ] Git installed and configured
- [ ] GitHub account (for most deployment options)
- [ ] Landing page files ready (index.html, styles.css)
- [ ] Social preview image (1200x630px, recommended)
- [ ] Google Analytics tracking ID (optional but recommended)

---

## Deployment Options

### Quick Comparison

| Platform | Setup Time | Custom Domain | SSL/HTTPS | CDN | Analytics | Best For |
|----------|------------|---------------|-----------|-----|-----------|----------|
| **Vercel** | 2 min | ✅ Free | ✅ Auto | ✅ Global | ✅ Built-in | Modern apps, Next.js |
| **GitHub Pages** | 5 min | ✅ Free | ✅ Auto | ✅ GitHub | ❌ Manual | Static sites, OSS projects |
| **Netlify** | 3 min | ✅ Free | ✅ Auto | ✅ Global | ✅ Built-in | JAMstack, Forms |
| **Azure** | 10 min | ✅ Free | ✅ Auto | ✅ Global | ✅ Azure Monitor | Enterprise, Azure ecosystem |

---

## Option A: Vercel (Recommended)

Vercel provides the fastest deployment with excellent performance and built-in analytics.

### Step 1: Prepare Your Repository

```bash
# Navigate to your landing page directory
cd E:\TORQ-CONSOLE\landing-page

# Initialize git repository if not already initialized
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: TORQ-CONSOLE Phase 5 landing page"

# Create a new repository on GitHub
# Then push your code
git remote add origin https://github.com/YOUR_USERNAME/torq-console-landing.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Vercel

**Method 1: Vercel CLI (Fastest)**

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel

# Follow the prompts:
# - Set up and deploy? Yes
# - Which scope? Your account/team
# - Link to existing project? No
# - What's your project's name? torq-console
# - In which directory is your code located? ./
# - Want to override settings? No

# Deploy to production
vercel --prod
```

**Method 2: Vercel Dashboard (Easiest)**

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure project:
   - **Framework Preset**: Other
   - **Root Directory**: ./
   - **Build Command**: (leave empty for static sites)
   - **Output Directory**: ./
5. Click "Deploy"

### Step 3: Configure Custom Domain (Optional)

1. In Vercel dashboard, go to your project
2. Navigate to "Settings" → "Domains"
3. Add your custom domain (e.g., `torq-console.com`)
4. Follow Vercel's DNS configuration instructions
5. SSL certificate is automatically provisioned

### Vercel Configuration File

Create `vercel.json` for advanced configuration:

```json
{
  "version": 2,
  "name": "torq-console",
  "builds": [
    {
      "src": "index.html",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        }
      ]
    },
    {
      "source": "/(.*)\\.(css|js|jpg|png|svg|woff|woff2)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

---

## Option B: GitHub Pages

GitHub Pages is perfect for open-source projects and provides free hosting with HTTPS.

### Step 1: Prepare Repository

```bash
# Create a new repository on GitHub
# Name it: torq-console-landing (or YOUR_USERNAME.github.io for personal site)

# Navigate to landing page directory
cd E:\TORQ-CONSOLE\landing-page

# Initialize and push to GitHub
git init
git add .
git commit -m "Initial commit: TORQ-CONSOLE landing page"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/torq-console-landing.git
git push -u origin main
```

### Step 2: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click "Settings" → "Pages"
3. Under "Source", select:
   - **Branch**: main
   - **Folder**: / (root)
4. Click "Save"
5. Wait 2-3 minutes for deployment
6. Your site will be available at: `https://YOUR_USERNAME.github.io/torq-console-landing/`

### Step 3: Custom Domain Configuration

1. Create `CNAME` file in repository root:
   ```bash
   echo "torq-console.com" > CNAME
   git add CNAME
   git commit -m "Add custom domain"
   git push
   ```

2. Configure DNS at your domain registrar:
   ```
   Type: CNAME
   Name: www (or @)
   Value: YOUR_USERNAME.github.io
   ```

3. In GitHub repository settings → Pages:
   - Enter your custom domain
   - Wait for DNS check
   - Enable "Enforce HTTPS"

### GitHub Actions Deployment (Automated)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

---

## Option C: Netlify

Netlify offers excellent features including form handling and edge functions.

### Step 1: Deploy via Netlify CLI

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Initialize and deploy
cd E:\TORQ-CONSOLE\landing-page
netlify init

# Follow the prompts:
# - Create & configure a new site
# - Team: Your team
# - Site name: torq-console
# - Deploy path: ./

# Deploy to production
netlify deploy --prod
```

### Step 2: Deploy via Netlify Dashboard

1. Go to [netlify.com](https://netlify.com)
2. Click "Add new site" → "Import an existing project"
3. Connect to GitHub and select your repository
4. Configure build settings:
   - **Build command**: (leave empty)
   - **Publish directory**: ./
5. Click "Deploy site"

### Step 3: Netlify Configuration

Create `netlify.toml` in repository root:

```toml
[build]
  publish = "."
  command = "echo 'No build command required'"

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"

[[headers]]
  for = "/*.css"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/*.js"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

# Performance optimizations
[build.processing]
  skip_processing = false

[build.processing.css]
  bundle = true
  minify = true

[build.processing.js]
  bundle = true
  minify = true

[build.processing.images]
  compress = true
```

---

## Option D: Azure Static Web Apps

Ideal for enterprise deployments with Azure ecosystem integration.

### Step 1: Install Azure CLI

```bash
# Windows (using winget)
winget install Microsoft.AzureCLI

# Or download from: https://aka.ms/installazurecliwindows
```

### Step 2: Deploy via Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Search for "Static Web Apps" and create new resource
3. Configure:
   - **Resource group**: Create new or select existing
   - **Name**: torq-console
   - **Plan type**: Free
   - **Region**: Choose nearest
   - **Source**: GitHub
   - **Organization**: Your GitHub account
   - **Repository**: torq-console-landing
   - **Branch**: main
   - **Build Presets**: Custom
   - **App location**: /
   - **Output location**: (leave empty)
4. Click "Review + create" → "Create"

### Step 3: Azure Configuration

Create `staticwebapp.config.json`:

```json
{
  "routes": [
    {
      "route": "/*",
      "serve": "/index.html",
      "statusCode": 200
    }
  ],
  "navigationFallback": {
    "rewrite": "/index.html",
    "exclude": ["/images/*.{png,jpg,gif}", "/css/*"]
  },
  "responseOverrides": {
    "404": {
      "rewrite": "/index.html",
      "statusCode": 200
    }
  },
  "globalHeaders": {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin"
  },
  "mimeTypes": {
    ".json": "application/json",
    ".css": "text/css",
    ".js": "text/javascript"
  }
}
```

### Step 4: Custom Domain on Azure

1. In Azure Portal, navigate to your Static Web App
2. Go to "Custom domains"
3. Click "Add" and follow domain verification steps
4. Azure automatically provisions SSL certificate

---

## Custom Domain Configuration

### DNS Configuration

For most hosting providers, configure these DNS records:

**For CNAME (subdomain)**:
```
Type: CNAME
Name: www
Value: your-deployment-url (e.g., torq-console.vercel.app)
TTL: 3600
```

**For A Record (apex domain)**:
```
Type: A
Name: @
Value: [Provider's IP address]
TTL: 3600
```

**For ALIAS (CloudFlare/Route53)**:
```
Type: ALIAS
Name: @
Value: your-deployment-url
TTL: Auto
```

### SSL/HTTPS

All recommended platforms automatically provide free SSL certificates:
- **Vercel**: Automatic via Let's Encrypt
- **GitHub Pages**: Automatic after DNS verification
- **Netlify**: Automatic via Let's Encrypt
- **Azure**: Automatic via Azure-managed certificates

---

## SEO Optimization Checklist

### Before Deployment

- [ ] Update meta tags in `index.html`:
  - [ ] Update `og:url` with actual domain
  - [ ] Update `twitter:url` with actual domain
  - [ ] Update `og:image` and `twitter:image` URLs
  - [ ] Replace `G-XXXXXXXXXX` with real Google Analytics ID

- [ ] Create social preview image:
  - [ ] Size: 1200x630px (for Open Graph)
  - [ ] Format: PNG or JPG
  - [ ] File name: `og-image.png`
  - [ ] Upload to repository root

- [ ] Update links in `index.html`:
  - [ ] Replace `https://torq-console.vercel.app/` with your actual domain
  - [ ] Replace `https://github.com/yourusername/torq-console` with actual repo
  - [ ] Update Twitter handle in meta tags
  - [ ] Update Discord invite link

### After Deployment

- [ ] Test all links and buttons
- [ ] Verify social media previews:
  - [ ] Facebook: [Sharing Debugger](https://developers.facebook.com/tools/debug/)
  - [ ] Twitter: [Card Validator](https://cards-dev.twitter.com/validator)
  - [ ] LinkedIn: [Post Inspector](https://www.linkedin.com/post-inspector/)
- [ ] Submit sitemap to search engines:
  - [ ] Google Search Console
  - [ ] Bing Webmaster Tools
- [ ] Test mobile responsiveness
- [ ] Check Core Web Vitals

### Create `sitemap.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://torq-console.com/</loc>
    <lastmod>2025-10-17</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
```

### Create `robots.txt`

```txt
User-agent: *
Allow: /

Sitemap: https://torq-console.com/sitemap.xml
```

---

## Performance Optimization

### Image Optimization

1. **Create optimized social preview image**:
   ```bash
   # Using ImageMagick
   convert og-image-original.png -resize 1200x630 -quality 85 og-image.png
   ```

2. **Add images to repository**:
   ```
   landing-page/
   ├── index.html
   ├── styles.css
   ├── og-image.png (1200x630px)
   └── favicon.ico (optional)
   ```

### Font Optimization

The landing page uses Google Fonts with optimal loading:
- `font-display: swap` for immediate text rendering
- Preconnect to Google Fonts for faster loading
- Only necessary font weights loaded

### CSS Optimization

For production, consider minifying CSS:

```bash
# Using clean-css-cli
npm install -g clean-css-cli
cleancss -o styles.min.css styles.css

# Update index.html to reference styles.min.css
```

### Performance Budget

Target metrics:
- **First Contentful Paint (FCP)**: < 1.8s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Total Blocking Time (TBT)**: < 200ms
- **Cumulative Layout Shift (CLS)**: < 0.1
- **Speed Index**: < 3.0s

### Test Performance

```bash
# Using Lighthouse CLI
npm install -g lighthouse
lighthouse https://your-domain.com --view
```

---

## Analytics Setup

### Google Analytics 4

1. Create GA4 property at [analytics.google.com](https://analytics.google.com)
2. Get your Measurement ID (format: `G-XXXXXXXXXX`)
3. Replace in `index.html`:
   ```javascript
   gtag('config', 'G-XXXXXXXXXX'); // Replace with your ID
   ```

### Event Tracking

The landing page includes pre-configured event tracking:
- **Navigation clicks**: Hero CTA, navbar buttons
- **Feature engagement**: Feature cards, demo interactions
- **Conversion tracking**: Get Started buttons, pricing clicks

### Custom Events

Add custom tracking:

```javascript
// Example: Track scroll depth
window.addEventListener('scroll', () => {
  const scrollPercent = (window.scrollY / document.documentElement.scrollHeight) * 100;
  if (scrollPercent > 50 && !window.scrollTracked50) {
    trackEvent('Engagement', 'scroll', '50%');
    window.scrollTracked50 = true;
  }
});
```

### Vercel Analytics

If using Vercel, enable built-in analytics:

1. Go to Vercel dashboard → Project → Analytics
2. Enable "Web Analytics"
3. Add script to `index.html`:
   ```html
   <script defer src="/_vercel/insights/script.js"></script>
   ```

---

## Troubleshooting

### Issue: Page Not Loading

**Solution**:
1. Check deployment logs in hosting platform
2. Verify all files are committed and pushed
3. Check file paths are relative (not absolute Windows paths)
4. Clear browser cache and try incognito mode

### Issue: Styles Not Applying

**Solution**:
1. Verify `styles.css` is in the same directory as `index.html`
2. Check browser console for 404 errors
3. Ensure file names match exactly (case-sensitive on Linux servers)
4. Clear CDN cache if using custom domain

### Issue: Images Not Displaying

**Solution**:
1. Verify image files are committed to repository
2. Check image paths in HTML
3. Use relative paths (e.g., `./og-image.png` not `E:\...\og-image.png`)
4. Ensure image formats are web-compatible (PNG, JPG, WebP)

### Issue: Social Preview Not Working

**Solution**:
1. Verify Open Graph meta tags are present
2. Check image URL is absolute (not relative)
3. Image must be publicly accessible
4. Clear social media cache using debugging tools
5. Ensure image meets size requirements (1200x630px)

### Issue: Slow Loading

**Solution**:
1. Enable compression on hosting platform
2. Minify CSS and JavaScript
3. Optimize images (compress and resize)
4. Enable CDN (most platforms do this automatically)
5. Use browser caching headers

### Issue: Google Analytics Not Tracking

**Solution**:
1. Verify Measurement ID is correct
2. Check Ad Blocker isn't blocking GA
3. Wait 24-48 hours for data to appear
4. Test in real-time view in GA dashboard
5. Check browser console for GA errors

---

## Maintenance & Updates

### Regular Tasks

- **Weekly**: Monitor analytics for traffic and conversions
- **Monthly**: Review Core Web Vitals and fix performance issues
- **Quarterly**: Update content, features, and screenshots
- **As Needed**: Update dependencies and framework versions

### Update Workflow

```bash
# Pull latest changes
git pull origin main

# Make updates to files
# (edit index.html, styles.css, etc.)

# Test locally
# Open index.html in browser

# Commit and push
git add .
git commit -m "Update landing page content"
git push origin main

# Deployment happens automatically via CI/CD
```

---

## Support & Resources

### Documentation
- [Vercel Documentation](https://vercel.com/docs)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Netlify Documentation](https://docs.netlify.com/)
- [Azure Static Web Apps Documentation](https://docs.microsoft.com/en-us/azure/static-web-apps/)

### Testing Tools
- [Google PageSpeed Insights](https://pagespeed.web.dev/)
- [GTmetrix](https://gtmetrix.com/)
- [WebPageTest](https://www.webpagetest.org/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)

### Validation Tools
- [W3C HTML Validator](https://validator.w3.org/)
- [W3C CSS Validator](https://jigsaw.w3.org/css-validator/)
- [Open Graph Debugger](https://www.opengraph.xyz/)

---

## Quick Start Scripts

### Deploy to Vercel (One-liner)

```bash
cd E:\TORQ-CONSOLE\landing-page && git init && git add . && git commit -m "Initial commit" && vercel
```

### Deploy to Netlify (One-liner)

```bash
cd E:\TORQ-CONSOLE\landing-page && git init && git add . && git commit -m "Initial commit" && netlify init && netlify deploy --prod
```

### Deploy to GitHub Pages (Script)

Create `deploy-gh-pages.bat`:

```batch
@echo off
echo Deploying to GitHub Pages...

cd E:\TORQ-CONSOLE\landing-page

git init
git add .
git commit -m "Deploy landing page"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/torq-console-landing.git
git push -u origin main

echo.
echo Deployment initiated! Visit:
echo https://YOUR_USERNAME.github.io/torq-console-landing/
echo.
echo Go to GitHub repository settings to enable GitHub Pages.
pause
```

---

## Success Criteria

Your deployment is successful when:

- ✅ Page loads in <2 seconds
- ✅ All links and buttons work correctly
- ✅ Mobile responsive design functions properly
- ✅ Social media previews display correctly
- ✅ HTTPS/SSL certificate is active
- ✅ Google Analytics is tracking visits
- ✅ Lighthouse score > 90 for all categories
- ✅ No console errors in browser dev tools

---

**Congratulations!** Your TORQ-CONSOLE Phase 5 landing page is now live and ready to showcase your real-time AI research platform to the world! 🚀

For questions or issues, please open an issue on the GitHub repository or contact the development team.
