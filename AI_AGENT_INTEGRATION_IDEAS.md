# AI Agent Integration Ideas — HR, Finance & CMS

A catalogue of practical AI agent features that can be added to the three apps.
Each idea lists **what it does**, **where it goes**, **what data it needs**, and a
**suggested approach** that follows the pattern already used in HR
(`apps/hr/src/app/api/ai/suggest-events/route.ts`):

> Server-side Next.js route → native `fetch` to OpenAI → typed mutation hook
> (`useMutation`) → button/component injected into the existing modal/form.
> Never import the `openai` npm package, never expose `OPENAI_API_KEY` to the
> browser.

---

## 1. HR App (`apps/hr`)

The HR app already has the **"Suggest from Events"** AI button in the email/SMS
compose modals. The remaining ideas extend that same pattern across staff,
training, awards and reviews.

### 1.1 Smart Email/SMS Composer (extend existing)
- **What** — Beyond event-based suggestions, let users type a short prompt
  ("remind staff about timesheet submission") and AI drafts both an email
  version (HTML) and an SMS version (≤160 chars) at once.
- **Where** — `apps/hr/src/components/modal/email/Content.tsx` and
  `apps/hr/src/components/modal/sms/SmsComposeContent.tsx`.
- **Data** — recipient list, sender (selectedFromUser), tone preset
  (formal / friendly / urgent).
- **Approach** — `/api/ai/draft-message` route, returns `{ subject, html, sms }`.
  Dispatch into existing `emailSmsComposeSlice`.

### 1.2 Staff Announcement Tone Rewriter
- **What** — One-click "Make more formal / friendlier / shorter / translate to
  Malay" on any drafted message.
- **Where** — Toolbar above the `ContentEditor` in compose modals.
- **Data** — current draft text + chosen action.
- **Approach** — `/api/ai/rewrite` route, single OpenAI call with a system
  prompt per action.

### 1.3 Award Citation Generator
- **What** — When creating an award, AI drafts a 2–3 sentence citation from
  the recipient's name, role, achievement bullet points.
- **Where** — Award create/edit modal under `apps/hr/src/app/(dashboard)/award`.
- **Data** — staff profile (name, position, department), achievement bullets.
- **Approach** — `/api/ai/award-citation` route.

### 1.4 Training Description Writer
- **What** — Given a training title and 2–3 keywords, generate a full course
  description, learning objectives, and target audience.
- **Where** — Training create/edit modal under `apps/hr/src/app/(dashboard)/training`.
- **Data** — title, keywords, duration.
- **Approach** — `/api/ai/training-description` returning structured JSON
  (`description`, `objectives[]`, `audience`).

### 1.5 Performance Review Narrative Assistant
- **What** — Convert reviewer rating sliders + bullet notes into a polished
  prose review.
- **Where** — Performance review form (new feature).
- **Data** — ratings, KPI scores, free-form notes.
- **Approach** — `/api/ai/review-narrative` route, returns
  `{ summary, strengths, improvements, goals }`.

### 1.6 Leave / HR Reply Drafts
- **What** — When approving/denying a leave request, AI drafts a context-aware
  reply ("Approved — please coordinate handover with X").
- **Where** — Leave management screen.
- **Data** — leave type, dates, requester, approval decision.
- **Approach** — `/api/ai/leave-reply` route.

### 1.7 Recurring "Daily Stand-up Digest" Agent
- **What** — Scheduled agent that scans events, leave, and announcements and
  drafts a single morning digest email for managers.
- **Where** — Cron / scheduled API route.
- **Data** — today's events, on-leave staff, pending approvals.
- **Approach** — Server cron → `/api/ai/digest` → store as draft for manager
  review (don't auto-send).

---

## 2. Finance App (`apps/finance`)

Finance has no AI integration yet. The biggest wins are around customer/supplier
communication and reducing copy-paste in document creation.

### 2.1 Payment Reminder Composer
- **What** — Generate polite, escalating payment reminder emails based on how
  overdue an invoice is (3, 14, 30 days).
- **Where** — Invoice/receipt list rows under
  `apps/finance/src/app/.../collection/invoices`.
- **Data** — customer name, invoice amount, due date, days overdue, prior
  reminders sent.
- **Approach** — `/api/ai/payment-reminder` returning `{ subject, body, tone }`,
  feed into existing email compose modal.

### 2.2 Quotation & Invoice Description Drafter
- **What** — From a few line-item keywords, AI expands into professional line
  descriptions and suggests payment terms boilerplate.
- **Where** — Create-quotation / create-invoice forms.
- **Data** — line items (name, qty), customer type, project context.
- **Approach** — `/api/ai/quotation-text` route returning per-line descriptions
  plus a `terms` block.

### 2.3 Purchase Order Description from Procurement Request
- **What** — Paste a vendor's quote text → AI extracts and structures it into a
  PO with item list, totals, expected delivery clause.
- **Where** — Purchase order create form (`apps/finance/src/app/.../payment/purchase-orders`).
- **Data** — pasted vendor quote text.
- **Approach** — `/api/ai/parse-quote` returns structured JSON the form
  pre-fills.

### 2.4 Account Categorisation Helper
- **What** — When adding a new ledger entry, suggest the correct Chart-of-Accounts
  category (sales / expense / cost-of-sales / etc.) based on description.
- **Where** — COA / journal entry forms under
  `apps/finance/src/app/.../administration`.
- **Data** — entry description, amount, existing COA list.
- **Approach** — `/api/ai/coa-suggest` returns `{ categoryId, confidence,
  reasoning }`. Show as a suggestion chip, never auto-apply.

### 2.5 Project Report Narrative
- **What** — Turn raw project numbers (budget vs. actual, variance, milestones)
  into an executive-summary paragraph for the project report PDF.
- **Where** — `apps/finance/src/app/.../settings/project-report`.
- **Data** — project ID → backend computes metrics → AI summarises.
- **Approach** — `/api/ai/project-summary` returns multi-section text.

### 2.6 Reconciliation Variance Explainer
- **What** — When closing an accounting period, AI looks at unreconciled lines
  and suggests likely explanations ("FX difference", "bank fee", "duplicate").
- **Where** — Period-close screen.
- **Data** — unreconciled transactions with amounts, dates, counter-parties.
- **Approach** — `/api/ai/reconcile-suggest` — strictly suggestions, all
  classifications require human confirmation.

### 2.7 Vendor / Customer Communication Tone Rewriter
- **What** — Same as HR 1.2 but for finance contexts (chasing payment, polite
  decline of credit terms, etc.).
- **Where** — Email/SMS compose modals in finance.
- **Approach** — Reuse the shared `/api/ai/rewrite` route (see §4).

---

## 3. CMS App (`apps/cms`)

CMS is content-heavy and benefits the most from AI-generated copy. Each
content-creation modal is a potential AI insertion point.

### 3.1 News Headline & Summary Generator
- **What** — Given the news body, AI suggests 3 headline options and a
  meta-description summary.
- **Where** — `AddNewsContentModal`.
- **Data** — body text, target audience.
- **Approach** — `/api/ai/news-meta` returns `{ headlines: string[], summary,
  slug }`.

### 3.2 Static Page Copy Drafter
- **What** — Given a page title and a few bullet points, AI drafts the full
  page content respecting the chosen layout (full / grid / sidebar).
- **Where** — `AddStaticContentModal`.
- **Data** — title, bullet outline, layout type.
- **Approach** — `/api/ai/static-page` route.

### 3.3 Banner Caption & CTA Suggester
- **What** — Upload a banner image + product/campaign context → AI suggests 3
  headline + sub-headline + button-text combos optimised for the banner type
  (header / promo / side).
- **Where** — Header/promo/side banner modals.
- **Data** — image (base64 or URL), campaign keywords, banner slot.
- **Approach** — `/api/ai/banner-copy` using GPT-4o-mini with vision input.

### 3.4 Image Auto-Captioner for Galleries
- **What** — When uploading gallery images, AI generates an alt-text and
  caption for each.
- **Where** — Gallery upload modal.
- **Data** — image file(s).
- **Approach** — `/api/ai/image-caption` (vision model), batched.

### 3.5 Product Description Writer
- **What** — Given a product name + 3 attribute bullets, AI writes a marketing
  description and bullet-point feature list.
- **Where** — Product create/edit modal.
- **Data** — name, attributes, target market.
- **Approach** — `/api/ai/product-copy` route.

### 3.6 FAQ Answer Drafter
- **What** — Type the question, AI drafts an answer based on existing FAQs and
  static content for tone consistency.
- **Where** — FAQ create modal.
- **Data** — question text, optional category.
- **Approach** — `/api/ai/faq-answer` route. (Optionally: pass last N FAQs as
  few-shot examples for tone matching.)

### 3.7 Menu Item Description Helper
- **What** — Auto-write short, SEO-friendly descriptions for menu items based
  on the menu name and parent context.
- **Where** — Menus management page.
- **Data** — menu name, parent menu, link target.
- **Approach** — `/api/ai/menu-copy` route.

### 3.8 Donation Page Copy Generator
- **What** — Given the cause/mission, AI drafts an emotionally resonant
  donation landing-page copy: headline, story, suggested amounts rationale.
- **Where** — Donation page editor.
- **Data** — mission statement, target amount, beneficiary info.
- **Approach** — `/api/ai/donation-copy` route returning structured sections.

---

## 4. Cross-App Shared Components

To avoid copying the AI plumbing into three apps, lift the shared pieces into
`packages/`:

### 4.1 `packages/ai` — shared AI primitives
- `callOpenAI(prompt, opts)` — thin wrapper around `fetch` to OpenAI.
- `useAiSuggestMutation` — generic hook (currently HR-specific).
- `<AiSuggestButton />` — currently HR-specific, generalise to accept any route
  + payload.
- `<AiToneRewriter />` — drop-in toolbar for any rich text editor.

### 4.2 Shared route utilities
- A common `aiRouteHandler({ system, user, schema })` helper in `packages/ai`
  so each app's `/api/ai/*` route is just a one-line wrapper.
- Standard error shape `{ error, retryable }` so all `useMutation` callers can
  use `crudErrorToast` consistently.

### 4.3 Shared safety rules
- All AI output is **draft-only** — never auto-send, never auto-save without
  user confirmation.
- Strip PII (NRIC, full bank numbers, salary figures) before sending to OpenAI.
  Add a `sanitisePromptInput()` util in `packages/ai`.
- Log every AI call (user, app, route, token usage) for cost auditing.
- Per-user / per-day rate limit enforced at the route layer.

---

## 5. Suggested Rollout Order

1. **Generalise HR's existing pattern** into `packages/ai` (small refactor).
2. **CMS quick wins** — News headline (§3.1) and Product description (§3.5)
   give visible value fast and are low risk.
3. **Finance Payment Reminders** (§2.1) — highest immediate ROI.
4. **HR Tone Rewriter** (§1.2) — small, reusable, demos cross-app value.
5. Iterate based on which features users actually keep using.

---

## 6. Environment & Setup Notes

- Each app's `.env`: `OPENAI_API_KEY=sk-...` (server-only, never `NEXT_PUBLIC_*`).
- Default model: `gpt-4o-mini` (fast & cheap). Reserve `gpt-4o` for vision
  features (banner copy, image captions) and complex narratives (review,
  project summary).
- Add a feature flag (`NEXT_PUBLIC_AI_ENABLED`) so the buttons can be hidden
  per-environment without code changes.
- Track token usage per route to keep cost visibility.
