# Pre-Deployment Checklist for TORQ-CONSOLE Landing Page

Use this checklist to ensure your landing page is production-ready before deployment.

## Content Updates

### Meta Tags & SEO
- [ ] Update Google Analytics ID in `index.html` (line 49)
  - Replace: `G-XXXXXXXXXX`
  - With: Your actual GA4 Measurement ID

- [ ] Update domain URLs throughout `index.html`:
  - [ ] Line 12: `<meta property="og:url">`
  - [ ] Line 20: `<meta property="twitter:url">`
  - [ ] Update in `sitemap.xml`
  - [ ] Update in `robots.txt`

- [ ] Update social media preview image URLs:
  - [ ] Line 14: `<meta property="og:image">`
  - [ ] Line 22: `<meta property="twitter:image">`

### GitHub & Social Links
- [ ] Update GitHub repository URL (appears 6 times):
  - Hero section "GitHub" button
  - Hero section CTA buttons
  - Footer GitHub icon
  - CTA section buttons
  - README links

- [ ] Update social media links in footer:
  - [ ] Twitter handle/URL
  - [ ] Discord invite link
  - [ ] GitHub organization/user

### Company Information
- [ ] Update company name if different from "TORQ-CONSOLE"
- [ ] Update contact email addresses
- [ ] Update "About" and "Careers" links in footer
- [ ] Update privacy policy and terms of service links

## Visual Assets

### Images
- [ ] Create Open Graph image (1200x630px)
  - File name: `og-image.png`
  - Format: PNG or JPG
  - Max size: 300KB recommended
  - Place in: `E:\TORQ-CONSOLE\landing-page\`

- [ ] Create favicon (optional but recommended)
  - File name: `favicon.ico`
  - Sizes: 16x16, 32x32, 48x48
  - Place in: `E:\TORQ-CONSOLE\landing-page\`

- [ ] Add screenshot images (optional)
  - Replace placeholder visuals in demo section
  - Optimize for web (<500KB each)

### Brand Assets
- [ ] Update logo emoji if using custom logo
- [ ] Verify color scheme matches brand
- [ ] Check font choices align with brand guidelines

## Technical Configuration

### Analytics
- [ ] Create Google Analytics 4 property
- [ ] Copy Measurement ID
- [ ] Replace in `index.html` (2 locations)
- [ ] Test tracking in GA Real-Time view after deployment

### Domain & DNS
- [ ] Purchase/configure custom domain (if using)
- [ ] Plan DNS configuration:
  - A records or CNAME
  - TTL settings
  - Email MX records (if applicable)

### Repository Setup
- [ ] Create GitHub repository for landing page
- [ ] Note repository URL for deployment scripts
- [ ] Configure repository settings:
  - [ ] Public or private
  - [ ] Description
  - [ ] Topics/tags

## Content Review

### Text Content
- [ ] Proofread all text for typos
- [ ] Verify technical accuracy of features
- [ ] Check pricing information is current
- [ ] Ensure all links are correct and working

### Features Section
- [ ] Verify feature list is accurate
- [ ] Update any changed capabilities
- [ ] Check technical specifications
- [ ] Validate model names (Claude, DeepSeek, etc.)

### Pricing Section
- [ ] Confirm pricing tiers are correct
- [ ] Update feature inclusions per tier
- [ ] Verify call-to-action buttons
- [ ] Check pricing currency

### Comparison Table
- [ ] Update phase comparisons if needed
- [ ] Verify feature availability per phase
- [ ] Check performance metrics accuracy

## Testing

### Local Testing
- [ ] Open `index.html` in multiple browsers:
  - [ ] Chrome/Edge
  - [ ] Firefox
  - [ ] Safari (if available)

- [ ] Test responsive design:
  - [ ] Desktop (1920x1080)
  - [ ] Tablet (768x1024)
  - [ ] Mobile (375x667)

- [ ] Verify all interactive elements:
  - [ ] Navigation menu
  - [ ] CTA buttons
  - [ ] Mobile menu toggle
  - [ ] Smooth scrolling
  - [ ] Form submissions (if any)

### Performance Testing
- [ ] Check page load time (target: <2s)
- [ ] Verify no console errors
- [ ] Test with slow 3G network simulation
- [ ] Check resource sizes:
  - [ ] HTML < 100KB
  - [ ] CSS < 50KB
  - [ ] Images < 500KB each

### Accessibility Testing
- [ ] Test keyboard navigation
- [ ] Check screen reader compatibility
- [ ] Verify color contrast ratios
- [ ] Test with browser zoom (150%, 200%)
- [ ] Check ARIA labels

## Deployment Preparation

### File Organization
- [ ] Verify all files are in correct location
- [ ] Check file naming (lowercase, no spaces)
- [ ] Ensure relative paths (not absolute Windows paths)
- [ ] Remove any test/temporary files

### Security
- [ ] Remove any sensitive information
- [ ] Check no API keys in code
- [ ] Verify no debug code left in
- [ ] Ensure security headers configured

### Version Control
- [ ] Initialize git repository
- [ ] Create `.gitignore` file
- [ ] Make initial commit
- [ ] Verify all necessary files committed

## Platform-Specific Setup

### For Vercel
- [ ] Install Vercel CLI: `npm install -g vercel`
- [ ] Login: `vercel login`
- [ ] Review `vercel.json` configuration

### For GitHub Pages
- [ ] Repository is public (required for free tier)
- [ ] Main branch exists
- [ ] Files in root directory or docs/ folder

### For Netlify
- [ ] Install Netlify CLI: `npm install -g netlify-cli`
- [ ] Login: `netlify login`
- [ ] Review `netlify.toml` configuration

### For Azure
- [ ] Azure account created
- [ ] Azure CLI installed
- [ ] Resource group planned
- [ ] Review `staticwebapp.config.json`

## Post-Deployment Validation

### Immediate Checks (First 5 minutes)
- [ ] Site loads correctly
- [ ] HTTPS/SSL certificate active
- [ ] All links work
- [ ] Images display
- [ ] Mobile responsive design works

### SEO Validation (First hour)
- [ ] Test Open Graph preview:
  - [ ] Facebook Sharing Debugger
  - [ ] Twitter Card Validator
  - [ ] LinkedIn Post Inspector

- [ ] Verify meta tags in page source
- [ ] Check robots.txt accessible
- [ ] Verify sitemap.xml accessible

### Analytics Validation (First 24 hours)
- [ ] Google Analytics tracking working
- [ ] Real-time view showing visitors
- [ ] Event tracking functional
- [ ] No tracking errors in console

### Performance Validation (First week)
- [ ] Run Lighthouse audit (target: 90+ all categories)
- [ ] Check Core Web Vitals:
  - [ ] LCP < 2.5s
  - [ ] FID < 100ms
  - [ ] CLS < 0.1

- [ ] Test from multiple locations
- [ ] Monitor page load times

### Search Engine Submission
- [ ] Submit to Google Search Console
- [ ] Submit to Bing Webmaster Tools
- [ ] Request indexing
- [ ] Monitor search appearance

## Marketing Preparation

### Social Media
- [ ] Prepare launch announcement
- [ ] Create social media graphics
- [ ] Schedule announcement posts
- [ ] Notify team/community

### Documentation
- [ ] Link to landing page from main repo
- [ ] Update README with landing page URL
- [ ] Add to project documentation
- [ ] Update package.json homepage field

### Monitoring
- [ ] Set up uptime monitoring
- [ ] Configure error tracking
- [ ] Set up performance monitoring
- [ ] Create alerts for downtime

## Launch Day Checklist

### Pre-Launch (1 hour before)
- [ ] Final content review
- [ ] Test all functionality one more time
- [ ] Clear CDN cache if applicable
- [ ] Notify team of launch time

### Launch
- [ ] Execute deployment
- [ ] Verify deployment successful
- [ ] Test from different devices/locations
- [ ] Monitor error logs

### Post-Launch (First 24 hours)
- [ ] Monitor analytics for traffic
- [ ] Check for error reports
- [ ] Review user feedback
- [ ] Monitor social media mentions
- [ ] Address any issues immediately

## Maintenance Schedule

### Daily (First week)
- [ ] Check analytics
- [ ] Monitor error logs
- [ ] Review user feedback

### Weekly
- [ ] Review performance metrics
- [ ] Check uptime reports
- [ ] Update content if needed

### Monthly
- [ ] Run full performance audit
- [ ] Review and optimize based on analytics
- [ ] Update dependencies if any
- [ ] Backup configuration files

## Quick Reference

### Important Files
```
landing-page/
├── index.html              # Main page (update meta tags, links)
├── styles.css              # Styles (usually no changes needed)
├── og-image.png           # Social preview (create this!)
├── favicon.ico            # Browser icon (optional)
├── robots.txt             # Update domain
├── sitemap.xml            # Update domain
├── vercel.json            # Vercel config
├── netlify.toml           # Netlify config
└── DEPLOYMENT.md          # Full deployment guide
```

### Key URLs to Update
1. `https://torq-console.vercel.app/` → Your domain
2. `https://github.com/yourusername/torq-console` → Your repo
3. `G-XXXXXXXXXX` → Your GA4 ID
4. Social media URLs (Twitter, Discord)

### Priority Actions
**Must Do Before Deployment:**
1. Create og-image.png (1200x630px)
2. Update Google Analytics ID
3. Update all domain URLs
4. Update GitHub repository URLs

**Should Do Before Deployment:**
5. Test on mobile devices
6. Proofread all content
7. Verify pricing information
8. Test all links

**Nice to Have:**
9. Custom favicon
10. Screenshot images
11. Video demo
12. Additional analytics

---

## Deployment Commands Quick Reference

```bash
# Vercel
vercel                    # Preview
vercel --prod            # Production

# GitHub Pages
# Use deploy-github-pages.bat or follow DEPLOYMENT.md

# Netlify
netlify deploy --prod --dir=.

# Test locally
start index.html         # Windows
open index.html          # macOS
```

---

**Ready to Deploy?**

If you've checked all items in the "Must Do" section, you're ready to deploy!

Choose your deployment method:
1. Run `deploy-vercel.bat` for Vercel
2. Run `deploy-github-pages.bat` for GitHub Pages
3. Run `deploy-netlify.bat` for Netlify
4. Follow `DEPLOYMENT.md` for detailed instructions

Good luck with your launch! 🚀
