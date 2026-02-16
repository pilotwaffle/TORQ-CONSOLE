# Firebase Risk Register

| Severity | Area | Finding | Evidence | Fix | Validate |
|---|---|---|---|---|---|
| Critical | Rules | Example: Public read/write on all collections | `allow read, write: if true;` in firestore.rules | Restrict to authenticated users with ownership checks | Deploy rules, test anon access returns permission-denied |
| High | Auth | Example: No email verification required | Auth config allows unverified sign-in | Enable email verification in Firebase Console | Sign up flow requires email link click |
| Medium | Functions | Example: No rate limiting on callable | No middleware or App Check on callable functions | Add App Check enforcement + rate limiting | Test burst calls are throttled |
| Low | Indexes | Example: Missing composite index | Query warning in console logs | Add index via firestore.indexes.json | Query executes without warning |
