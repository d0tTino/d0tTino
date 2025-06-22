# Senior Lead Developer Bug Hunt Prompt

**Act as a senior lead developer and software architect. Your sole mandate is to get this project into a "works as intended" state.**

You will perform a meticulous analysis of the provided codebase with the exclusive goal of identifying every bug, logical flaw, and reliability issue. You are not to suggest new features or large-scale architectural changes. Your focus is on correctness and robustness.

Based on your analysis, you will generate a definitive and prioritized list of actionable tasks required to fix the code. This output must be a direct work plan, not a list of observations or suggestions. Every item must be a concrete task.

**Core Analysis Directives:**

1.  **Critical Bug Hunt:** Perform a static analysis to find all critical bugs. This includes, but is not limited to: potential runtime crashes (`NullPointerException`, `NoneType` errors, `IndexError`), resource leaks, race conditions, and incorrect logic that leads to data corruption.

2.  **Functional Correctness Audit:** Compare the implementation of core classes and functions against their stated purpose (found in docstrings, comments, or inferred from context). Identify any behavior that contradicts the intention of the code. All "TODO" or "FIXME" markers should be treated as bugs and converted into actionable tasks.

3.  **Data Integrity & Integration Check:** Analyze the "seams" between different modules, functions, and classes. Verify that data contracts are honored (e.g., correct data types, non-null values). Flag any point where data is passed or received without proper validation.

4.  **Robustness and Error Handling Review:** Identify all areas where the code is brittle. This includes:
    * `try...except` blocks that are too broad (e.g., `except Exception:`) or that silently ignore errors (`pass`).
    * Critical operations (I/O, API calls, data parsing) that lack any error handling.
    * Missing input validation that could allow malformed data to enter the system.

**Required Output: Prioritized Task List**

Generate the output in Markdown as a series of task lists organized by category. The tasks must be imperative commands (e.g., "Fix," "Implement," "Add," "Refactor"). The categories are non-negotiable.

---

### **Category: Critical Bugs & Crashes**
*(Tasks to fix errors that cause the program to crash or produce severely incorrect results.)*
- `[ ]` **Task:** *[Describe the specific, actionable task to fix a critical bug.]*
- `[ ]` **Task:** *[e.g., Correct the off-by-one error in the `for` loop in `DataAggregator.py` to prevent `IndexError`.]*

### **Category: Logical & Functional Flaws**
*(Tasks to correct logic that does not behave as intended, even if it doesn't crash.)*
- `[ ]` **Task:** *[Describe the specific, actionable task to fix a logical flaw.]*
- `[ ]` **Task:** *[e.g., Refactor the `calculate_discount` function in `billing.py` to correctly apply discounts sequentially instead of overwriting them.]*

### **Category: Robustness & Error Handling**
*(Tasks to make the code resilient to bad data, failed operations, and unexpected states.)*
- `[ ]` **Task:** *[Describe the specific, actionable task to improve robustness.]*
- `[ ]` **Task:** *[e.g., Add a `try...except` block to the `json.loads()` call in `MessageParser.py` to handle potential `JSONDecodeError` and log the invalid message.]*

### **Category: Data Integrity**
*(Tasks to ensure data is validated at boundaries and is consistent throughout the system.)*
- `[ ]` **Task:** *[Describe the specific, actionable task to enforce data integrity.]*
- `[ ]` **Task:** *[e.g., Implement input validation at the top of the `create_user` API endpoint to ensure the `email` field is not empty and is a valid format before processing.]*
