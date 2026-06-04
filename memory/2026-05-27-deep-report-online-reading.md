# Deep Report Online Reading Debug Report

- Symptom: Mini program users saw a generic request failure when choosing online reading from the deep report download page.
- Root cause: Online reading still used the paid-report path. The mini program called `ensureMembership()` before opening a report, `/api/reports/deep/view-token` required commerce auth plus active membership, and `/reports/deep/view/:token` rechecked membership before rendering HTML.
- Fix: Online reading now mints and serves short-lived signed reader links without membership. PDF download remains behind commerce auth, active membership, and download quota.
- Evidence: `python3 -m unittest tests/test_deep_report_download_flow.py` passed. The broader membership/download suite also passed.
- Regression test: `tests/test_deep_report_download_flow.py` asserts that the reader route is not auth-gated, the open-reader frontend path does not call membership checks, and signed reader tokens can be public.
- Status: DONE.
