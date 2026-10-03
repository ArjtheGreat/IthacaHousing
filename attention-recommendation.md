# Attention recommendation

Written 2026-10-01. Nothing here has been built.

## The current direction will not get attention

The Fair Rent Map and its student-first redesign are a utility. Nothing on the site can be shared today:

- There are no per-address or per-listing URLs. Every link preview is the Maitrix Labs logo with the line "Ithaca's Premier Real Estate Intelligence Platform."
- The homepage sells "rental pricing inefficiencies" to students, landlords and policymakers at once.
- The headline number, predicted fair rent, cannot carry a public claim. The model's R² is 0.355 under spatial cross-validation, and it predicts $271 a person for a 14-bedroom house that lists at $1,195 a person.

A better map makes the site more useful. It does not give anyone a reason to screenshot it.

## The one idea: The Deed

Every rental house in Collegetown gets one mock property deed, rendered as a tall image, that states how long it takes the tenants to pay the full value of the house.

> If the fourteen of you sign 125 Highland Pl, you will pay $200,760 a year for a house the county values at $930,000. That is the whole house every 4 years 8 months.

The deed is about the house, not the person. It carries no tenant names. It is aimed first at sophomores, who are in dorms right now comparing houses for 2027-28 in group chats, and second at the juniors and seniors who already live in those houses. Below the headline it adds the owner of record, the last purchase when it is recent, floor space per person, who lived at the address in 1940 and what they paid, and the house's rank on a public board of every house in Collegetown ordered by how fast its tenants pay it off.

One sentence for the whole campaign: every four and a half years, the students of a Collegetown house buy it again, and they have never owned it.

## Why this spreads

**The line is true, checkable, and covers every parcel.** Assessed value exists for 100% of parcels and is current to the 2024 roll. The house-file investigator built eight real cards and found the rent-against-assessed-value line "lands every time", while four other planned fields failed on real data.

**The number is large and human-sized.** Clean whole-house listings cluster between 4 years 1 month and 5 years 5 months. That is roughly one undergraduate degree, which is what makes it repeatable in conversation.

**Recent sales back it up.** A debunker who checks will find the assessments track real prices:

| House | Bought | Price | Assessed | Asking rent per year |
|---|---|---|---|---|
| 109 Williams St | 2022 | $830,000 | $850,000 | $176,400 |
| 711 E Seneca St | 2022 | $775,000 | $800,000 | $192,360 |
| 710 Stewart Ave | 2023 | $1,036,250 | $1,200,000 | $244,080 |
| 306 Bryant Ave | 2019 | $635,000 | $660,000 | $129,600 |

**It fits the chats that are active this month.** Cornell requires first- and second-year students to live on campus, so the people signing leases now are sophomores comparing several addresses and pasting listing links. A deed for a house nobody in the chat lives in yet needs no personal disclosure, and each group is weighing several houses, so it crosses group boundaries. The skeptic found this, not the investigators.

**It can be posted anonymously.** With no name on it, the image works on Sidechat, where posts naming students are reportedly removed, and can be sent by someone who does not live there. The Sidechat rule comes from press reports the skeptic found in search summaries, not from a page we read.

**The format matches what has spread before.** The precedents that spread took one input and returned one image: Receiptify reached a million users in a day, and The Pudding's Spotify roast drew millions of views. The ones that stayed niche returned a results page about someone else: JustFix Who Owns What sits at about 33,000 visitors a month.

**It does not depend on anyone's cooperation.** The core artifact needs an assessment roll and a rent figure. It does not need landlord reviews, ambassadors, or a partner.

## The artifact, with real data

Every figure below is from the repo's county file, the live listings, or the 1940 census file.

### 125 Highland Pl

> **DEED OF NOTHING**
> **125 Highland Pl, Ithaca**
>
> If the fourteen of you sign: $16,730 a month. $200,760 a year.
> The county values the house at $930,000.
> You will pay for the whole house every **4 years 8 months**.
>
> 265 square feet each.
> Owner of record: 125 Highland Place LLC, c/o a management company at PO Box 218. That mailbox receives mail for 24 single-address LLCs.
> Last sold: 2004, $500,000.
> 1940: Anna Foyle, 47, owned it. The census valued it at $12,000. Her daughter Teresa, 20, was a secretary at Thermo Electric on $900 a year.
>
> Gross rent. The owner pays tax, upkeep and any mortgage out of it. Sources: Tompkins County 2024 assessment roll, asking rent for 2027-28, 1940 US Census.

### 306 Bryant Ave

> If the eight of you sign: $129,600 a year for a house the county values at $660,000.
> The whole house every **5 years 1 month**.
> Bought in 2019 for $635,000.
> The county says 1,740 square feet. The listing says 3,000.
> 1940: five households, ten people. Michael Golomb, 30, a research associate born in Germany, paid $30 a month. Homer A. Jack, 23, paid $33.

### 109 Williams St

> If the twelve of you sign: $176,400 a year.
> Bought in November 2022 for $830,000. Assessed at $850,000.
> The whole house every **4 years 10 months**.
> 1940: Charles and Ethel Hill, 69 and 61, from Kentucky, rented the whole house for $65 a month.

### 202 Williams St

> If the twelve of you sign: $172,080 a year for a house the county values at $760,000.
> The whole house every **4 years 5 months**.
> Owner of record: 202 Williams Street, LLC, c/o the same PO Box 218.
> 1940: John C. Kelly, 42, an insurance agent, owned it. Value $10,000. He lived there with his wife and four children.

### The board

> **COLLEGETOWN, RANKED BY HOW FAST THE TENANTS BUY THE HOUSE**
> 404-406 University Ave, 13 beds: 4 years 1 month
> 711 E Seneca St, 14 beds: 4 years 2 months
> 208 Williams St, 11 beds: 4 years 5 months
> 202 Williams St, 12 beds: 4 years 5 months
> 125 Highland Pl, 14 beds: 4 years 8 months
> 109 Williams St, 12 beds: 4 years 10 months
> 710 Stewart Ave, 18 beds: 4 years 11 months
> 306 Bryant Ave, 8 beds: 5 years 1 month
> 308 Stewart Ave, 16 beds: 5 years 5 months

### Honest limits of these examples

- The board shows nine houses, not the full ranking. I computed it from 29 whole-house listings joined to parcels, after converting per-person prices that the listing site labels per unit. The five fastest results, at 2 to 4 years, look like join errors, where a listing spans several parcels or the reverse. I left them off. The full build needs a parcel-accurate join before the board is published.
- I cross-checked five of the nine against their unit-by-unit listings: 125 Highland, 202 Williams, 208 Williams, 306 Bryant and 109 Williams. The other four rest on the price conversion alone.
- Smaller houses run 9 to 15 years. Large apartment buildings need a per-unit version, which is assessed value divided by the county's unit count, because the building's rent roll is unknown.
- 43% of 1940 matches are unremarkable. A typical one reads: "Fred Thornton, 62, sheet-metal worker, and his wife Jennie. Rent $30."
- 1940 rents look 40 to 70 times lower. Adjusted for inflation the real increase is 1.7 to 3 times. The deed shows 1940 as a fact about the house, not as the outrage line.

## The strongest alternative I rejected: Who Owns Collegetown

A map and leaderboard that groups one-LLC-per-building parcels into the landlord groups behind them. It has the best real headline after The Deed: 328 apartment parcels, 116 owner groups, and ten of them hold 52% of the assessed value. It would get a news story.

It lost for four reasons:

- **The reveal is a PO box.** 79% of apartment parcels mail to an Ithaca address, and the market is unconcentrated by antitrust convention.
- **There is no villain.** The largest groups list below the Collegetown median of $1,250 a bed, at $925 and $1,195.
- **It has been done.** The Cornell Daily Sun reported in 2013 that eight landlords held 4,013 of an estimated 6,110 bedrooms, a bigger number than records alone give us.
- **It carries the highest risk for a one-hop loop.** The investigator hit four kinds of false grouping in one afternoon, and a wrong link is the real legal exposure.

Its best piece survives as one line on each deed: the owner of record and how many other parcels share its mailing address.

## Every other idea considered

Each has the pitch, the screenshot, who shares it, what sharing signals, and why it lost.

1. **The file on your house (roast).** A per-address roast card. Screenshot: a card mocking your house. Housemates in the house chat. Signals "look what we put up with." Lost because four of eight fields failed on real data and it roasts a landlord, not the sharer. The Deed is what was left after cutting it down.
2. **Ghosts of your house.** Who lived at your address in 1940 and what they paid. Screenshot: "A future Nobel winner paid $25 for my apartment." Alumni, locals, some residents. Signals curiosity. Lost because HistoryForge has offered this lookup for ten years without spreading, and students are not in the data. It survives as one line per deed and about 20 curated stories.
3. **College Rent Index.** Every campus ranked by rent per bedroom. Screenshot: a leaderboard with your school highlighted. Students and press. Signals pride in suffering. Lost because Cornell is 6th of 18, the "more than Columbia" headline is false, and only 3 of 8 Ivies are readable.
4. **Rent verdict card.** Type your rent, get a percentile. Screenshot: "You pay more than 81% of Collegetown." Individuals on Instagram. Signals a brag or a complaint. Lost because rents bunch between $1,100 and $1,400, so most cards say "average", and it means publishing your own rent.
5. **Payback clock on purchase price.** Months of rent to repay what the owner paid. Screenshot: "This house repaid its price in 9 months." Lost because 48% of recorded sales are before 2010, so the number measures the sale date. The Deed uses assessed value instead and shows purchase price only when recent.
6. **Collegetown Wrapped.** A swipeable year-in-review of your house. Instagram stories. Signals belonging. Lost because it is a format, not a claim, and the data fills two or three slides.
7. **Lease rush tracker.** A live count of next year's units disappearing. Screenshot: "62% of four-bedrooms are gone." Sophomore group chats. Signals urgency. Lost because we have no inventory history and the Cornell site is not the whole market. The timing insight is kept.
8. **Rent hike receipts.** Same unit, last year against this year. Sidechat and r/Cornell. Signals outrage. Lost because 168 unit histories show a median change of 0% a year.
9. **Landlord reviews and tier list.** Crowdsourced ratings. Lost on cold start: it needs other people to write, CUAPTS already exists, and the UCSB version had "a few reviews" after a month.
10. **Price per minute to class.** What each minute closer costs, by college. Screenshot: "Engineers pay $42 a minute." Signals college rivalry. Lost because the data shows no relationship: median rent is $1,195 at 7, 13 and 16 minutes.
11. **Absurd listing of the day.** A daily meme feed. Screenshot: "129 square feet for $950." Sidechat. Signals humor. Lost because only two floorplans beat Manhattan per square foot and one is a data error. The median is 42% of Manhattan.
12. **Rent stock ticker.** Streets as tickers. Finance students. Signals an in-joke. Lost because rents barely move, so the ticker would sit flat.
13. **Fair split calculator.** Split house rent by room. House chats, by necessity. Lost because it is useful rather than shareable, and nothing in our data makes it ours.
14. **Which Collegetown street are you.** A personality quiz. Instagram stories. Signals identity. Lost because it does not need our data and reads as generic quiz content.
15. **Door posters only.** A stunt with facts posted outside each house. Lost as a standalone idea, kept as the launch step for The Deed.
16. **Negotiation letter generator.** A data-backed email to your landlord. Lost because it is private by nature.
17. **1940 walking map.** Walk Collegetown in 1940. Locals and alumni. Lost for the same reasons as idea 2.

## The skeptic's best objection, and my answer

**The objection.** The number is mechanical and the reply writes itself: "You paid 100% of your Uber and own none of the car." Every whole house grosses about 20 to 23% of its assessed value a year, so every deed says nearly the same thing and a friend's deed gives you no reason to want your own. The figure is gross, before property tax, mortgage and repairs. The skeptic put the original per-person version at a 65% chance of failing, and noted that a per-person share collapses to 0.08% in a large building.

**My answer.**

- I took the skeptic's fix. The unit is the house, the number is years rather than a small percentage, and the first name is gone.
- The sameness is the story. The board's point is that a packed Collegetown house repays its value in about one degree, almost regardless of which house. Variation comes from building type, where small houses run 9 to 15 years, and from the 1940 household and the owner line.
- The Uber reply is fair, so the deed prints its own caveat and, in the full build, the actual property tax bill. Recent purchase prices sit within a few percent of assessments, so the base number holds up.
- An argument about whether the number is fair still circulates the image.

I did not fully answer one part. Residents of large apartment buildings get a weaker deed, and that is a large share of students.

## Risks, and what we cannot know until it is live

**Risks**

- **Listing terms.** Pre-filled asking rents come from scraping the Cornell listing site, run by Rent College Pads and StarRez, whose terms forbid robots and republishing. The existing pipeline already does this daily. A product that embarrasses landlords who pay to list there makes enforcement more likely. Typed rent avoids the problem but costs the three-second experience. This is a decision for you.
- **Wrong owner claims.** A shared mailbox is not proof of common ownership. The wording must stay "owner of record" and "shares a mailing address with". Each deed needs a visible evidence trail and a corrections form.
- **Private homes.** 2,379 of 4,515 city residential parcels look owner-occupied. Those get no deed and no owner name.
- **Fake entries.** Typed rents with no verification invite joke values. Typed rents must be bounded and must never overwrite the public board.
- **Census.** The 1940 records are public, but the transcription is HistoryForge's and has no stated data licence. Credit them and ask The History Center. Show heads of household only, since children in the 1940 census may be alive.
- **Retaliation.** These are the landlords students rent from next year. Suits over criticism are mostly dismissed, but defendants carry costs until then. I am not a lawyer, and this plan has not had legal review.
- **Reach beyond Ithaca.** The deed needs full-value assessments. That holds in Ithaca but not in California or many other states, so it does not work in any college town as is.

**Unknown until live**

- Whether "4 years 8 months" reads as outrage or as a shrug.
- Whether sophomores forward a deed across housing groups, or it stays in one chat.
- Whether anyone posts it publicly on Sidechat or Instagram.
- Whether it lasts beyond one lease season. The investigators and the skeptic all expect a spike, not a loop.
- How landlords, Cornell, and the listing vendor react.

My own estimate is that this is the only one of the five likely to produce a real campus spike, and that leaving Ithaca on its own is unlikely.

## The full build, in order

1. **Records foundation.** Rebuild the address-to-parcel join with range expansion, which lifts listing matches from 131 to 174 of 207. Load the current assessment roll with owner names, actual tax bills, state sales records with arm's-length flags, and unit counts. Classify every parcel as rental or owner-occupied.
2. **Rent layer.** Clean asking rents: relabel the 98 per-person prices marked per unit, and remove whole-house double counts at 24 addresses. Add typed rent with plausibility bounds. Build the per-unit version for apartment buildings.
3. **Deed generator.** Templated lines keyed to verified fields, each footnoted to its source, with no free-form generated claims. Render tall and square images. Give every house a URL whose link preview is its deed.
4. **Compare mode.** A group pastes two to four addresses and gets the deeds side by side. This is the artifact for sophomore group chats.
5. **1940 layer.** All three censuses, heads of household only, a flag for whether the original building survives, and about 20 verified stories such as George Beadle at 209 College Ave in 1930.
6. **Owner layer.** Owner of record, mailbox count, evidence panel, corrections form, right of reply. No home addresses.
7. **The board.** Every Collegetown house ranked by its clock, with street pages and a house-against-house view.
8. **New front door.** Replace the homepage with one address box. Move the map and analytics behind it.
9. **Lease-season launch.** Print each house's deed and leave it at that house's door with a QR code. Post the board image on Sidechat and r/Cornell. Send the board and method to the Cornell Daily Sun and Ithaca Voice. The door drop is the one step people must do by hand.
10. **After launch.** Publish a dated annual Rent Report from typed rents. Extend to Syracuse and Binghamton after checking how those towns assess.
