# 🚊 Stochastic Modelling for Bogotá's BRT System

This is a sibling repo to [OSLTM](https://github.com/este6an13/osltm) but will contain only a set of handpicked algorithms I really need. OSLTM repo will be treated as a sandbox to generate and run experiments and new ideas, but the core set of algorithms to generate robust and justified statistical findings will live in this repo.

### Currently I have:

#### Data Pipeline: Downloads and Stores the Data

The data pipeline is design so that user can download a representative subset of the data. Check-ins and check-outs data in TM Open Data website is huge, so it makes sense to work with a subset, specially in these first development and exploratory phases.

- `sampling/dates.py`: A script to run a stratified sampling on dates. A startum is a `(year, month, day_type)` combination, and the purpose of it is to get a handful of dates to work on in the pipeline downstream, since it would be too heavy to use all the available dates, and also, it needs to be stratified to guarantee I have a minimal number of samples per combination.

- `download.py`: A script to download check-ins and check-outs data from TM open data portal. The idea is to only download files for the sampled dates. It removes unused columns at the end, which saves disk space.

- `sampling/stations.py`: A script to read the available stations in the available sampled dates files. Once loaded, we parse them to get a unified structure `(code, name)`, and finally perform the sampling.

- DB setup: I've been adding the main models and their repo layers, which now allows me to start persisting and reading data. I use SQLite engine and SQLAlchemy as ORM.

- `populate.py`: This is the step that persist the pipeline data to the database. I store stations, and counts in this step. Counts are computed in aggregate based on the specified window in minutes.
I also keep track of processed files, just to not re-compute on every run unless the users wants so.
In earlier steps of the pipeline we store the sampling runs params and results for reproducibility

> Why sampling stations? This is to speed-up the pipeline in the experimentation stages. We may not want to run experiments on the +100 stations in the beginning, and also, if we use a subset of stations, the database will have less data liberating disk space. At some point we may want to analyze all stations, since we may be interested in classifying them based on their profiles, but that will be a future step, if I decide going that route.

#### Exploratory Data Analysis:

My first hypothesis is that check-ins and check-outs time series can be grouped in 3 groups for all stations: weekdays, saturdays and sundays/holidays. That's tested in `src\eda\day_type.py` script. I want to show, for almost all stations, time series are similar every weekday, every sunday and every sunday/holiday, but behave differently across groups. I mean, the pattern of a weekday is different from the pattern of a saturday, and a sunday/holiday. Everyone that has used TM in these days in Bogotá, knows that this seems to be true for the majority of the stations. The analysis of this script should show that a Tuesday shouldn't be too different from a Friday, so that's why I go with a full weekday group instead of splitting by day of week.

### Artifacts Reference

Artifacts are just data and plots the scripts generate that could be reported. I use a naming convention for them to maintains everything organzied.

- `sg_r_ci_table_`: Table, each row a station, day type (g) combination. Includes the R score calculated as between/within group distances. If greater than 1, it means groups are different as hypothesized. I include a confidence interval calculated after a bootstrap procedure.

- `g_mr_ci_p_table_`: Table, each row a day type (g). Using the data from the previous artifact, it aggregates all stations and reports one row per day type. I report median R score, percentiles and the proportion of stations whose score is greater than 1.

### What's next:

- Day Type Groups: in progress, some plots missing
- Stations Patterns: Are stations time series of the same day type different, are they similar in shape in magnitude, can we define groups?
- Seasonality: check if one month behaves different to another. I won't check between years really.

### Note:

I'm writing these scripts by hand, without autocompletion or agentic assistance, as a deliberate practice.

If I eventually present these findings as a research project, I want to ensure that I understand every line of code.

The algorithms are handpicked from the OSLTM repo, where most of them were generated with AI assitance. However, the scripts in this repository are my own implementations. They may be clumsy, buggy and suboptimal, but they reflect my own coding style and understanding.

Every line represents code that I can explain, debug, and improve myself and that's the goal of this project.

> Update (8/23/2026): Ok, I'm using AI (specifically Claude Opus 5 in Claude Desktop) to help me write the matplotlib plots scripts though. I just know it would take me so much time doing it myself manually, and they wouldn't look good. But I'm not letting any agent make edits. I copy and paste snippets and tailor them. And all the input data computation is done manually just like the rest of the codebase.
