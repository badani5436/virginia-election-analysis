# Virginia's 2024 Presidential Shift

A reproducible, locality-level analysis of how Virginia's presidential election
results changed between 2020 and 2024. The interactive article compares the
Democratic-minus-Republican vote margin across all 133 counties and independent
cities, with a closer look at five selected Northern Virginia localities.

## Interactive article

Once GitHub Pages is enabled for this repository, the article will be at:

**https://badani5436.github.io/virginia-election-analysis/**

The site files are in `docs/`, which is also the GitHub Pages publishing folder.

## Method and code

- `analyze.py`: parses the downloaded official election returns, selects the
  locality totals (not the precinct rows), and calculates changes in vote
  counts and Democratic-minus-Republican margins.
- `verify.py`: independently reconciles the output with the original files.
- `data/`: unmodified source CSVs and the derived locality table.
- `docs/`: the published HTML, CSS, JavaScript, analysis output and a complete
  reproducibility download.

Python 3.9+ is required; no third-party packages are needed. To reproduce the
data outputs from the raw CSVs:

```bash
python3 analyze.py
python3 verify.py
```

The first command writes regenerated data files to `docs/`; the second checks
those results. The website's downloadable ZIP is a snapshot of the complete
reproducibility package and is not automatically rebuilt by these commands.

## Official sources

- [Virginia 2020 presidential results](https://historical.elections.virginia.gov/contest/144567)
- [Virginia 2024 presidential results](https://historical.elections.virginia.gov/contest/161256)
- [Virginia's 2024 certification announcement](https://www.elections.virginia.gov/news-releases/archive/2024/2024-election-results-certified-1.html)

Source CSVs were downloaded on October 28, 2026. For reference, the source
SHA-256 hashes are:

```text
e3289bba8e9e0fce24cd06de2c4f9dbe091e14d3c3c710eee560aec145cae84a  data/virginia_2020_president_official.csv
f4e54c7fc691cc253ba2026cc37eb81945513600ad0fdef5fde50a3de50671c8  data/virginia_2024_president_official.csv
```

## How to interpret the findings

The Democratic-minus-Republican margin is the difference between each party's
candidate vote counts; its percentage-point form divides by **votes recorded
for president**, which are not the same as all ballots cast or registered-voter
turnout. Geographic changes do not identify individual voter behavior or prove
why results changed. The five-locality grouping is a chosen analytical subset,
not an official definition of Northern Virginia.

This is an independent portfolio project and is not affiliated with The New
York Times or the Virginia Department of Elections.

## Publish to GitHub Pages

1. On GitHub, create a **public** repository called
   `virginia-election-analysis` under `badani5436`.
2. Upload all files and folders **inside the extracted package** to the root of
   the repository, keeping `docs/` and `data/` as folders.
3. Commit the upload to the `main` branch.
4. Open **Settings → Pages → Build and deployment**.
5. Choose **Deploy from a branch**, select branch **main**, folder **/docs**,
   and click **Save**.
6. After the build finishes, check the address above in a private/incognito
   browser window. Make sure both the charts and download links work.

This GitHub Pages setup uses no paid hosting and no custom domain.
