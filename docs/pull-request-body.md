The diploma repository had no runnable prototype or approbation package. This adds TransferLens, a local application for filtering historical transfer candidates, inspecting dated model inputs, comparing Random Forest forecasts, saving a shortlist and exporting CSV.

The research foundation is the team's existing RMT experiment on 781 real transfers. Its source hashes and original outputs are retained. The diploma adds the interface, read-only inference API, application tests, editable architecture diagrams, a unified report and a separate task screenshot PDF.

Validation: the original individual and formation RF benchmark was reproduced from the raw snapshot; all 11 core/HTTP tests passed; browser filtering, profiles, shortlist persistence and alternative destination disclosure were exercised. Thirty warm local requests gave p95 about 73 ms. Formation context did not improve the held-out result, and individual RF is practically tied with persistence; these limitations are visible in the UI and report.

Refs #1, #2, #3, #4, #5. The issues remain open for team review. Actual interviews, confirmed personal task owners, each member's own contributions, peer review and substantive supervisor feedback are still required. This draft does not claim a completed academic submission or a reviewed pre-defense tag.

Frontend refinements on 23 October add safe shortlist recovery, undo after removal, consistent loading/export state, search reset, clearer keyboard feedback and contained table scrolling on narrow screens. Six JavaScript regression checks supplement the 11 Python checks. The filter/reset, profile toggle, clear/undo and keyboard flows were checked in the browser; at a 390 px viewport the table scrolled without widening the document. The submission tag `prob-period-1` is preserved. These changes were prepared and technically checked with AI assistance; another student's authorship or peer approval is not claimed.

Review the scope, model input chronology, saved-model provenance, setup instructions and the report's explicit evidence gaps. Do not merge until another team member has reviewed the changes.
