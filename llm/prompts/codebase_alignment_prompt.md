# Codebase Alignment Analysis Prompt

**Objective:** Analyze this codebase against the attached report and produce a prioritized task list to resolve issues and align the code with the project's goals.

**Analysis Steps:**

1. **Gap Analysis:** Compare current code features and architecture against the report. Identify what is complete, in-progress, or missing.
2. **Issue Identification:** Scan the code for bugs, architectural deviations, and technical debt.
3. **Testing Gaps:** Briefly note critical areas that lack sufficient testing.

**Output:**

* **Alignment Score (0-100):** Rate how closely the current codebase aligns with the report’s requirements.
* **Task List (Markdown):** Group tasks by priority into these categories:
  * **Critical Fixes & Bugs**
  * **Architectural Refactoring**
  * **New Features**
  * **Code Quality & Testing**

# User-provided custom instructions

Run Tests and linters for every code change but not when changing code comments and documentation.
