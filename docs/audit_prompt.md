**Act as a senior DevOps engineer and FinOps specialist. Your mission is to conduct a rigorous cost and efficiency audit of the provided GitHub Actions workflow files.**

The primary goal is to eliminate or drastically reduce the metered usage costs, like those shown in the user's billing screenshot. You must analyze every workflow and provide a detailed, actionable optimization plan. The ideal outcome is a CI/CD setup that is both highly efficient and leverages all available free resources.

**Primary Directives:**

1.  **Identify & Eliminate Waste:**
    * Scan for and flag any workflow files (`.yaml`) that are effectively useless: those with no defined jobs, or triggers that can never run (e.g., `on: never`). Recommend their immediate removal or renaming to `.disabled.yaml`.

2.  **Optimize Triggers for Precision:**
    * For each workflow, analyze its `on:` block. If it's too broad (e.g., `on: push`), recommend tightening it to specific branches (`branches: [main, develop]`) and adding `paths:` filters to ensure it only runs when relevant code changes.
    * Scrutinize `schedule:` triggers. For each one, question its necessity and suggest removal or conversion to a manual `workflow_dispatch:` trigger if it's not critical.

3.  **Consolidate and Batch Workflows:**
    * Identify opportunities to merge multiple, redundant workflows (e.g., separate files for lint, test, and build) into a single, efficient CI pipeline. This reduces the overhead of spinning up multiple runners.

4.  **Implement Efficiency Best Practices:**
    * For every workflow that runs on pull requests or pushes to a feature branch, recommend adding the `concurrency` block to automatically cancel in-progress runs when a new commit is pushed.
    * For every job, recommend setting the most restrictive `permissions` possible to follow the principle of least privilege.

5.  **Propose a Self-Hosted Runner Strategy (Highest Impact):**
    * Identify the jobs that are the most resource-intensive or have the longest run times (e.g., builds, end-to-end tests).
    * Strongly recommend migrating these specific jobs to a self-hosted runner to leverage unlimited free minutes. Provide the exact `runs-on: self-hosted` change required.

**Required Output: A Detailed Optimization Plan**

Produce a comprehensive report in Markdown. Structure it to be a clear, step-by-step guide for me to implement.

---

### **1. Executive Summary & Strategy**
*(A brief overview of the current state of the workflows and a high-level strategy for reducing costs, leading with the recommendation for a self-hosted runner.)*

---

### **2. Global Configuration Changes**
*(Provide code snippets for changes that should be applied to most or all workflows.)*
* **Concurrency Control:**
    ```yaml
    concurrency:
      group: ${{ github.workflow }}-${{ github.ref }}
      cancel-in-progress: true
    ```
* **Default Permissions:**
    ```yaml
    permissions:
      contents: read
    ```

---

### **3. Workflow-by-Workflow Breakdown**
*(For each `.yaml` file provided, give specific, actionable recommendations with code examples.)*

**File: `ci.yaml`**
* **Issue:** The `build` job runs on every push to any branch.
* **Recommendation:** Restrict the trigger to the `main` branch and only when files in `src/**` change.
* **Suggested Change:**
    ```diff
    - on: push
    + on:
    +   push:
    +     branches:
    +       - main
    +     paths:
    +       - 'src/**'
    ```
* **Issue:** This job is a candidate for self-hosting.
* **Recommendation:** Change `runs-on: ubuntu-latest` to `runs-on: self-hosted`.
* **Suggested Change:**
    ```diff
    - runs-on: ubuntu-latest
    + runs-on: self-hosted
    ```

**(Repeat for each workflow file...)**

---

### **4. Workflow Consolidation Plan**
*(If applicable, outline a plan to merge multiple workflows.)*
* **Recommendation:** The `lint.yaml` and `test.yaml` workflows should be merged into `ci.yaml` as sequential jobs. This will save on runner startup time.
* **Proposed `ci.yaml` structure:**
    ```yaml
    jobs:
      lint:
        ...
      test:
        needs: lint
        ...
      build:
        needs: test
        ...
    ```
---
# User-provided custom instructions

Run Tests and linters for every code change but not when changing code comments and documentation.

