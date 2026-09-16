# AV Evidence

A reproducible explorer of California DMV autonomous-vehicle disengagement rates.

Build in progress. Public dashboard target: https://vivaran.news/waymo-project

## Design decisions
- The user's current request authorizes GitHub pushes and Cloudflare deployment, superseding the older Claude-only no-deploy note.
- Python/SciPy/statsmodels provide the tested statistical reference implementation; Streamlit remains a runnable companion.
- A lightweight custom HTML/CSS/JavaScript dashboard adds the requested polished UI and Cloudflare hosting without a Python server.
- Historical reporting years 2020–2024, as specified in the provided execution prompt; this is a versioned historical dataset, not a live feed.
- Disengagements are not crashes. No safety rankings or causal release claims.
- Driverless and safety-driver permit reports remain separate.
- Planner overdispersion is a dimensionless quasi-Poisson design effect, not the NB2 alpha parameter.
- No invented personal name or affiliation; this is an independent portfolio project.
