# TORQ-CONSOLE Landing Page - Quick Start Guide

Get your landing page live in 5 minutes or less!

## Choose Your Deployment Method

### Option 1: Vercel (Fastest - Recommended)

```bash
# 1. Navigate to landing page directory
cd E:\TORQ-CONSOLE\landing-page

# 2. Run deployment script
deploy-vercel.bat

# 3. Follow prompts and you're done!
# Your site will be live at: https://your-project.vercel.app
```

**Time: ~2 minutes**

---

### Option 2: GitHub Pages (Free for Open Source)

```bash
# 1. Create a GitHub repository at github.com
# Name: torq-console-landing

# 2. Run deployment script
deploy-github-pages.bat

# 3. Enter your repository URL when prompted

# 4. Enable GitHub Pages:
#    - Go to repository Settings > Pages
#    - Source: main branch, / (root)
#    - Click Save

# Your site will be live at: https://USERNAME.github.io/torq-console-landing/
```

**Time: ~5 minutes**

---

### Option 3: Netlify (Great for Forms & Functions)

```bash
# 1. Navigate to landing page directory
cd E:\TORQ-CONSOLE\landing-page

# 2. Run deployment script
deploy-netlify.bat

# 3. Follow prompts and you're done!
# Your site will be live at: https://your-project.netlify.app
```

**Time: ~3 minutes**

---

## Before You Deploy

### Required Updates (2 minutes)

1. **Create Social Preview Image**
   - Size: 1200x630 pixels
   - Format: PNG or JPG
   - Name: `og-image.png`
   - Place in: `E:\TORQ-CONSOLE\landing-page\`

2. **Update Google Analytics ID** in `index.html` (line 49):
   ```javascript
   // Find this line:
   gtag('config', 'G-XXXXXXXXXX');

   // Replace with your GA4 Measurement ID:
   gtag('config', 'G-YOUR-ACTUAL-ID');
   ```

3. **Update Domain URLs** in `index.html`:
   - Search for: `https://torq-console.vercel.app/`
   - Replace with: Your actual domain
   - Search for: `https://github.com/yourusername/torq-console`
   - Replace with: Your actual GitHub repo

### Optional Updates

- Update social media links in footer (Twitter, Discord)
- Customize pricing if needed
- Add your own screenshots to demo section

---

## Test Locally First

```bash
# Simply open in browser
start index.html          # Windows
open index.html           # macOS
xdg-open index.html      # Linux
```

Check:
- All sections display correctly
- Links work (even if they point to example URLs)
- Mobile responsive design works (use browser DevTools)
- No console errors

---

## Deployment Comparison

| Platform | Speed | Custom Domain | Setup Complexity | Best For |
|----------|-------|---------------|------------------|----------|
| **Vercel** | ⚡⚡⚡ | ✅ Free | Very Easy | Most projects |
| **GitHub Pages** | ⚡⚡ | ✅ Free | Easy | Open source |
| **Netlify** | ⚡⚡⚡ | ✅ Free | Very Easy | JAMstack |

---

## After Deployment

### Verify Your Site (5 minutes)

1. **Test the URL**
   - Open in browser
   - Check HTTPS works (green padlock)
   - Test on mobile device

2. **Test Social Sharing**
   - Facebook: [Sharing Debugger](https://developers.facebook.com/tools/debug/)
   - Twitter: [Card Validator](https://cards-dev.twitter.com/validator)
   - Enter your URL and check preview

3. **Check Performance**
   - Run [PageSpeed Insights](https://pagespeed.web.dev/)
   - Target: 90+ score in all categories
   - Fix any critical issues

### Configure Custom Domain (Optional)

**For Vercel:**
1. Go to project settings in Vercel dashboard
2. Click "Domains"
3. Add your domain
4. Follow DNS configuration instructions

**For GitHub Pages:**
1. Add `CNAME` file with your domain
2. Configure DNS at your registrar
3. Enable HTTPS in GitHub settings

**For Netlify:**
1. Go to "Domain settings" in Netlify dashboard
2. Add custom domain
3. Follow DNS configuration instructions

---

## Troubleshooting

### "Command not found: vercel"
```bash
# Install Vercel CLI
npm install -g vercel
```

### "Command not found: netlify"
```bash
# Install Netlify CLI
npm install -g netlify-cli
```

### "Page shows 404"
- Wait 2-3 minutes after deployment
- Clear browser cache (Ctrl+Shift+R)
- Check deployment status in platform dashboard

### "Styles not loading"
- Verify `styles.css` is in same directory as `index.html`
- Check file committed to repository
- Clear CDN cache

### "Images not showing"
- Check image files are committed
- Verify image paths are relative (not absolute)
- Ensure images are in correct directory

---

## Need Help?

### Documentation
- Full guide: See `DEPLOYMENT.md`
- Pre-deployment checklist: See `PRE-DEPLOYMENT-CHECKLIST.md`
- Project README: See `README.md`

### Platform Documentation
- [Vercel Docs](https://vercel.com/docs)
- [GitHub Pages Docs](https://docs.github.com/en/pages)
- [Netlify Docs](https://docs.netlify.com/)

### Testing Tools
- [PageSpeed Insights](https://pagespeed.web.dev/)
- [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)
- [Twitter Card Validator](https://cards-dev.twitter.com/validator)

---

## One-Liner Deployment

### Vercel
```bash
cd E:\TORQ-CONSOLE\landing-page && deploy-vercel.bat
```

### GitHub Pages
```bash
cd E:\TORQ-CONSOLE\landing-page && deploy-github-pages.bat
```

### Netlify
```bash
cd E:\TORQ-CONSOLE\landing-page && deploy-netlify.bat
```

---

## What's Included

Your landing page includes:

✅ Modern, responsive design
✅ Mobile-first approach
✅ SEO optimized (meta tags, structured data)
✅ Social media ready (Open Graph, Twitter Cards)
✅ Google Analytics integration
✅ Fast loading (<2s target)
✅ Security headers configured
✅ Sitemap and robots.txt
✅ Browser caching optimized
✅ Accessibility friendly

---

## Success Checklist

After deployment, verify:

- [ ] Site loads quickly (<2 seconds)
- [ ] HTTPS works (green padlock)
- [ ] Mobile responsive design works
- [ ] All links function correctly
- [ ] Social media previews look good
- [ ] Google Analytics tracking works
- [ ] Lighthouse score >90

---

**Ready to launch?** Pick your platform and run the deployment script!

**Questions?** Check `DEPLOYMENT.md` for detailed instructions.

**Good luck with your launch!** 🚀
