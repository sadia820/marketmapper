# MarketMapper — Business Research Agent

Give it a list of **businesses** (name and website). For each one it:

1. Reads the company's public website: home page plus up to 3 key pages (about, services, contact, careers, shop…). It respects robots.txt and waits between requests.
2. Works out what the business does: industry, services, rough size and location.
3. Spots gaps and opportunities, such as no HTTPS, not mobile-friendly, no online booking, no online shop, hiring, or expanding.
4. Recommends up to 3 offers from **your** catalog (`offers.yaml`) and explains why.
5. Writes a short outreach angle addressed to the business.

The output is `results.csv` (opens in Excel), `results.json` and a readable `report.md` sorted by priority.

**Scope:** companies only. The tool reads only these columns: `business_name, website, city, country, notes`. It ignores any other columns, such as personal phone or email, and does not look up individuals.

---

## Setup

```bash
pip install -r requirements.txt
```

For AI mode (much better summaries and matching), set your Anthropic API key:

```bash
# macOS / Linux
export ANTHROPIC_API_KEY=sk-ant-...
# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

## Input file

CSV or Excel with at least a `business_name` column. `website` is strongly recommended.

| business_name | website | city | country | notes |
|---|---|---|---|---|
| Green Valley Landscaping | greenvalleyland.com | Austin | USA | |
| Sunrise Bakery | | Lahore | Pakistan | No website known |

If the website is empty, the business is still analyzed. Having no website is itself a useful signal.

## Run

```bash
python agent.py sample/businesses.csv              # AI mode
python agent.py sample/businesses.csv --offline    # rule-based, no API key
python agent.py my_list.xlsx -o results_nov --max-pages 5
```

Optional: choose the model with `AGENT_MODEL` (default `claude-sonnet-5-5`).

## Customize the offers

Edit `offers.yaml` to list what your clients actually sell. Each offer has:

- `id`: a short code
- `name`: what appears in the report
- `fits`: plain-English description of which businesses it suits (used by AI mode)
- `signals`: keywords used by offline mode (see `analyze_offline` in `agent.py`)

## Output columns

`business_name, website, city, country, status, industry, summary, services, size_estimate, observed_gaps, recommended_offers, offer_reasons, priority, outreach_angle, confidence, pages_read, mode`

## Good practice for outreach

- Contact businesses through their **published business channels**, such as the contact form, business email or main phone line.
- In the US, B2B cold email must follow CAN-SPAM: a real sender, an honest subject line, a physical address and a working unsubscribe. Automated calls or texts to mobile numbers need prior consent under the TCPA, even for business numbers.
- Check `confidence` before acting. Low means the site had little to go on.
