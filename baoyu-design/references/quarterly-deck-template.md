# Quarterly Business Review Deck Template

Proven 15-slide structure for quarterly business reviews, status reports, and team updates.

## Slide Structure (10-minute default)

| # | Slide | Purpose | Key Elements |
|---|-------|---------|--------------|
| 1 | **Cover** | Title + context | Title, subtitle, date, presenter name, department |
| 2 | **Agenda** | Set expectations | 4-5 sections with time allocations |
| 3 | **Section Header** | Part 01: Performance | Big number "01", label, subtitle |
| 4 | **Key Metrics** | KPI snapshot | 4-6 data cards: large gradient number + label + change indicator |
| 5 | **Trend Chart** | Show progression | Bar chart or line chart, monthly/quarterly data |
| 6 | **Section Header** | Part 02: Achievements | Big number "02", label, subtitle |
| 7 | **Achievements** | Major wins | 2-4 cards: icon, title, 3-4 bullet points each |
| 8 | **Section Header** | Part 03: Team | Big number "03", label, subtitle |
| 9 | **Team Members** | Core team | 3-4 profile cards: avatar, name, role, one-line bio |
| 10 | **Team Growth** | Headcount & culture | Headcount, satisfaction, training metrics |
| 11 | **Section Header** | Part 04: Next Quarter | Big number "04", label, subtitle |
| 12 | **Goals** | Targets | 3 big-number targets + timeline/milestone track |
| 13 | **Initiatives** | Projects | 2-4 project cards with deliverables |
| 14 | **Summary** | Key takeaways | Two-column: "Done Well / Improve Next" or highlights |
| 15 | **Thank You** | Close | Thank you + contact info + Q&A prompt |

## Scaling

- **5 minutes**: Drop slides 5 (trend) and 10 (team growth). Keep 12 slides.
- **20 minutes**: Add detail slides under each section (e.g., per-product breakdown, per-team breakdown).
- **Always ask for real data** — the template uses placeholder numbers that must be replaced.

## CSS Patterns

Use these reusable patterns for consistency across quarterly decks:

### Data Card
```css
.data-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 2.5rem;
  text-align: center;
}
.data-value {
  font-size: calc(var(--type-title) * 1.3);
  font-weight: 900;
  background: var(--gradient-hero);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.data-change {
  display: inline-flex;
  padding: 0.4rem 1rem;
  background: rgba(34,197,94,0.1);
  border-radius: 100px;
  font-size: var(--type-caption);
  color: var(--success);
}
```

### Section Header
```css
.section-num {
  font-size: calc(var(--type-display) * 1.2);
  font-weight: 900;
  background: var(--gradient-hero);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  opacity: 0.3;
}
```

### Timeline
```css
.timeline {
  display: flex;
  justify-content: space-between;
  position: relative;
}
.timeline::before {
  content: '';
  position: absolute;
  top: 24px; left: 2rem; right: 2rem;
  height: 2px;
  background: var(--gradient-hero);
}
.timeline-dot {
  width: 48px; height: 48px;
  background: var(--gradient-hero);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  position: relative;
  z-index: 1;
}
```
