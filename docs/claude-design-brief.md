# Claude Design brief: Temple Beth Israel website (tbiport.org)

Paste **Prompt 0** first, then one page prompt at a time. Before Prompt 0, upload:
- the TBI logo (https://www.tbiport.org/dashboard/images/logo.png, or the original file)
- 4–6 real photos (sanctuary, Shabbat, preschool, religious school, community event, clergy)
- screenshots of the current homepage on desktop and phone (for reference only)

---

## Prompt 0: context and constraints (paste first)

> We're redesigning the website for Temple Beth Israel (TBI), a synagogue in Port Washington, NY, at 118 Murray Ave. The site runs on **ShulCloud**, a synagogue management platform with a section-based page builder. Mockups must be buildable inside ShulCloud, so follow these constraints exactly:
>
> **Page building blocks (the only layouts allowed):** full-width sections stacked vertically. Each section uses one of these column layouts: full width; 2, 3, 4, 5 or 6 equal columns; 1/3 + 2/3; 2/3 + 1/3; 1/4 + 3/4; 3/4 + 1/4; 1/4 + 1/2 + 1/4; 1/3 + 1/6 + 1/3 + 1/6. A section can have a background color or a full-bleed background image (parallax allowed). Content inside columns is rich text (H2/H3, paragraphs, lists, links, buttons) and images. Optional right sidebar on interior pages; landing pages have none.
>
> **Available section styles:** Welcome (photo + text), Events (auto list of upcoming calendar events), Donation Teaser, Full Width Teaser, Parallax Teaser, Rounded Images (circle-cropped photo cards), Funds/Donate sections.
>
> **Header and footer are set by the theme:** logo left, horizontal menu with dropdowns or mega menus, a slim utility bar above it, and two highlighted buttons (Join, Give). Footer: address, office hours, phone, newsletter sign-up, Facebook. Keep these conventional so they map to a ShulCloud theme.
>
> **Hero:** a single-slide image slider with headline, one sentence and up to two buttons. No rotating carousels.
>
> **Avoid:** custom interactive widgets, animations beyond simple hover, overlapping or layered layouts, text set in images, tabs and accordions. If something really needs a custom component, label it "Needs ShulCloud support".
>
> **Brand and tone:** warm, welcoming, rooted in Jewish tradition, family-centered, community-minded. Take the primary colors from the uploaded logo. Use one accent, plenty of white space, and real photography of people. Use one serif for headings and one clean sans-serif for body text, both from Google Fonts. Hebrew words may appear (Shabbat, Kehillah, Tikkun Olam) but the site is in English. Text must meet WCAG AA contrast, tap targets must be at least 44px, and every image needs alt text.
>
> **Audiences, in priority order:** (1) families looking at the preschool or religious school, (2) prospective members, (3) members checking this week's services or the livestream, (4) people marking a life event or a loss, (5) donors.
>
> **Main menu:** About · Pray · Learn · Community · Life Events · [Join] [Give]. **Utility bar:** Calendar · Watch online · Member login · Contact · Search.
>
> Design desktop (1440px) and mobile (390px) for every page.

---

## Prompt 1: Homepage

> Design the TBI homepage with these sections in order:
> 1. **Header**: logo, the main menu, Join and Give buttons, and the utility bar.
> 2. **Hero** (single slide): congregation photo. Headline "A welcoming home for Jewish life in Port Washington" (placeholder). One sentence about the community. Buttons "Plan a visit" and "Explore membership".
> 3. **This week at TBI** (4 equal columns, tinted background): Shabbat evening service (Friday, time), Shabbat morning service (Saturday, time), Weekday minyan (days, time), Watch online (link). Use placeholder times like "6:30 pm".
> 4. **Find your place** (4 equal columns, Rounded Images style): Preschool ("Tour our preschool"), Religious School ("See grades and registration"), Prayer ("Find a service"), Adult Learning ("Browse classes"). Each card has a photo, a title, one sentence and one descriptive link. No "Read more".
> 5. **Upcoming at TBI** (Events style): 4–6 event cards with date block, title, time and category tag, plus a "See the full calendar" link.
> 6. **Welcome from our clergy** (1/3 + 2/3): clergy photo, 3–4 sentence welcome, link "Meet our clergy and staff".
> 7. **New to TBI?** (full-width Parallax Teaser over a photo): one sentence, buttons "Plan a visit" and "Membership and dues".
> 8. **Support our community** (Donation Teaser): Donate · Honor or remember someone · Kol Nidre Appeal.
> 9. **Footer**: 118 Murray Ave, Port Washington, NY; map link; office hours; phone; newsletter sign-up; Facebook.

## Prompt 2: Section landing page (use "Learn" as the example)

> Design a section landing page for **Learn**. No sidebar.
> - Full-width intro: H1 "Learning at TBI", two sentences, light background.
> - 2 Columns Equal: Preschool and Religious School as large photo cards, each with a short description and a link.
> - 2 Columns Equal: Teens (TBI High and Madrichim) and Adult Learning.
> - Full-width strip: "Questions about learning at TBI?" with a contact button.
> Keep the same header and footer as the homepage.

## Prompt 3: Program page (use "Preschool" as the example)

> Design the **Preschool** program page, with an optional right sidebar listing the preschool sub-pages (About, Programs, First Friends, Extended Care, Summer Camp, Parents Association).
> - 1/3 + 2/3: classroom photo and an overview paragraph.
> - 3 Columns Equal "At a glance": Ages, Schedule, Tuition (placeholders).
> - Full width: H2 sections covering Our approach, A typical day, and Jewish values in the classroom.
> - 4 Columns Equal: photo strip.
> - Full-width call to action: "Schedule a tour" and "Apply for next year" buttons.

## Prompt 4: People grid (Clergy, Staff and Leadership)

> Design a **Clergy, Staff & Leadership** page. It replaces 40+ separate bio pages.
> - Full-width intro.
> - "Clergy": 2 Columns Equal with large photos, name, title and a 3-sentence bio.
> - "Staff": 4 Columns Equal in Rounded Images style with photo, name, role and a "Contact" link (a form, not a raw email address).
> - "Board of Trustees": 4 Columns Equal, smaller cards with name and role, photos optional.

## Prompt 5: Give page

> Design the **Give** page.
> - Full-width impact statement over a photo.
> - 3 Columns Equal "Ways to give": Make a donation, Honor or remember someone (tributes), Sponsor a Kiddush or event.
> - 2 Columns Equal: Kol Nidre Appeal (seasonal) and Leave a legacy (will planning).
> - Full width: a simple donation form (amount buttons, fund dropdown, "in honor or memory of" field, Donate button). Note on the form that it maps to ShulCloud's built-in donation form.
> - Full-width strip: "Questions about giving?" with a contact button.

## Prompt 6: Mobile pass

> Show the homepage and the Preschool page at 390px. Use a hamburger menu that keeps Join and Give visible, columns stacked in source order, the "This week at TBI" strip as a 2×2 grid, and tap targets of at least 44px.

---

### After the mockups
- Check every section against the allowed layouts list. Anything labeled "Needs ShulCloud support" becomes a ticket to ShulCloud.
- Build order in ShulCloud: theme colors and logo → navigation → homepage → the landing pages → program pages → Give and Join.
- Copy for every page is in `audit/tbi-site-copy.md`. Recommendations for each page are in `audit/tbi-content-audit.xlsx`.
