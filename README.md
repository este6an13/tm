# 🚊 Stochastic Modelling for Bogotá's BRT System

This is a sibling repo to [OSLTM](https://github.com/este6an13/osltm) but will contain only a set of handpicked algorithms I really need. OSLTM repo will be treated as a sandbox to generate and run experiments and new ideas, but the core set of algorithms to generate robust and justified statistical findings will live in this repo.

### Currently I have:

- `sampling.py`: A script to run a stratified sampling on dates. A startum is a `(year, month, date_type)` combination, and the purpose of it is to get a handful of dates to work on in the pipeline downstream, since it would be too heavy to use all the available dates, and also, it needs to be stratified to guarantee I have a minimal number of samples per combination.

- `download.py`: A script to download check-ins and check-outs data from TM open data portal. The idea is to only download files for the sampled dates. It removes unused columns at the end, which saves disk space.

### What's next:

- A script to perform sampling on stations
- DB setup: downloaded data should be persisted in a local DB for better management

### Note:

I'm writing these scripts by hand, without autocompletion or agentic assistance, as a deliberate practice.

If I eventually present these findings as a research project, I want to ensure that I understand every line of code.

The algorithms are handpicked from the OSLTM repo, where most of them were generated with AI assitance. However, the scripts in this repository are my own implementations. They may be clumsy, buggy and suboptimal, but they reflect my own coding style and understanding.

Every line represents code that I can explain, debug, and improve myself and that's the goal of this project.
