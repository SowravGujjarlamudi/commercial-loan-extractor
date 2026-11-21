\# Loan Field Extraction – Implementation Prompt



> \*\*Note:\*\* This is a reconstructed implementation prompt based on the implemented schema rules and project requirements. It is not claimed to be the verbatim original Claude Code prompt.



\## Objective



Implement a Python-based validation layer for extracting structured commercial loan terms from loan agreements.



Use Python 3.11+ and Pydantic v2. Ensure the extracted loan data follows the required field-level validation rules.



\## Required loan fields



1\. \*\*Borrower name\*\*

&#x20;  - Required string.

&#x20;  - Must not be empty.

&#x20;  - Maximum length: 200 characters.



2\. \*\*Commitment amount\*\*

&#x20;  - Must be a positive Decimal value.

&#x20;  - Maximum two decimal places.



3\. \*\*Effective date\*\*

&#x20;  - Represented as a date.



4\. \*\*Maturity date\*\*

&#x20;  - Represented as a date.

&#x20;  - Must be later than the effective date when both dates are available.



5\. \*\*Maximum leverage covenant\*\*

&#x20;  - Optional Decimal value.

&#x20;  - If provided, must be positive.

&#x20;  - Missing values must remain `None`, not be converted to zero.



6\. \*\*Minimum interest coverage covenant\*\*

&#x20;  - Optional Decimal value.

&#x20;  - If provided, must be positive.

&#x20;  - Missing values must remain `None`, not be converted to zero.



\## Margin structure



Implement margin using a discriminated union with two supported types.



\### Flat margin

\- Store the margin in `flat\_margin\_bps`.

\- `pricing\_grid` must be `None`.



\### Pricing grid

\- `flat\_margin\_bps` must be `None`.

\- `pricing\_grid` must contain at least two tiers.

\- Each tier must include a leverage threshold and margin in basis points.

\- Leverage thresholds must be strictly increasing.



\## Validation requirements



\- Use Pydantic v2 models and validators.

\- Use Decimal for financial values to avoid floating-point precision issues.

\- Reject invalid or inconsistent data.

\- Preserve missing optional covenant values as `None`.

\- Ensure the margin structure is internally consistent.



\## Testing requirements



Create automated tests covering:

\- Valid flat margin records.

\- Valid pricing grid records.

\- Invalid commitment amounts.

\- Invalid borrower names.

\- Invalid covenant values.

\- Invalid margin configurations.

\- Duplicate or non-increasing pricing grid thresholds.

\- Invalid maturity and effective date relationships.



\## Answer-key validation



Implement an answer-key loader and validation utility.



The utility should:

\- Read the hand-checked CSV answer key.

\- Validate each record against the Pydantic schemas.

\- Report valid and invalid records.

\- Identify flat margins and pricing grids.

\- Identify missing optional covenant values.

\- Detect duplicate agreement IDs.

\- Generate JSON and Markdown validation reports.



Do not include the original answer-key CSV or confidential agreement data in the Git repository.



\## Expected outcome



The implementation should be maintainable, testable, and reproducible, with clear documentation of validation rules and known data limitations.

