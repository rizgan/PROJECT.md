---
spec_version: 0.2
id: PROJECT-hosts
name: Distributed pipeline (ext:hosts)
topic: nightly news digest
---

## Hosts
- scraper:     ssh://bot@worker-02.local
- scraper_bk:  ssh://bot@worker-03.local
- gpu_box:     ssh://ml@10.0.0.5
- gpu_backup:  ssh://ml@10.0.0.6
- local:       local

## Agents

### collector
wave: 1
host: [scraper, scraper_bk, local]
Collect raw items about: {{ topic }}.

### summarizer
wave: 2
after: collector
host: [gpu_box, gpu_backup]
Summarize the collector's output into 5 bullet points.

### publisher
wave: 3
after: summarizer
host: local
Format the summary as Markdown and write it to disk.
