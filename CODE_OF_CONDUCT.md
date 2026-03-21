# Code of Conduct

## Our Pledge

In the interest of fostering an open and welcoming environment, we as contributors and maintainers pledge to making participation in our project and our community a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

## Contribution Guidelines & Rules

To ensure high-quality code and a smooth contribution process, all contributors must adhere to the following rules:

### 1. Mandatory Lint Checking
Before submitting a Pull Request (PR), you **must** run the following linting and type-checking tools. PRs that fail these checks will not be merged:
- `black`: Code formatting
- `ruff`: Linting and fixing
- `mypy`: Static type checking
- `deptry`: Dependency analysis

### 2. Synchronization & Rebasing
- Always verify if a **rebase** is required before starting work or pushing your PR.
- It is highly recommended to rebase onto the main branch regularly to avoid merge conflicts.
- Even if not merging immediately, do not create unnecessary merge conflicts.

### 3. AI Disclosure (AI-Vibe Coded)
- AI-aided coding is allowed and welcomed.
- For clarity and transparency, if your PR contains AI-generated or "AI-Vibe coded" logic, you **must** disclose this in the PR description.

### 4. PR Documentation
- Every PR **must** mention all the issue numbers that it intends to close (e.g., "Closes #86").
- Clear descriptions of *what* changed and *why* are required.

### 5. Priority Testing for Core Changes
- If your work involves **Underlying Web Selectors** (Playwright-based or JS Injection-based), these changes must be tested on high priority.
- These components are the foundation of CamouChat and should not be submitted for review without thorough local testing.
- You must clearly state the reason for the change and what problem it intends to solve.

## Our Standards

Examples of behavior that contributes to creating a positive environment include:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

Examples of unacceptable behavior by participants include:
- The use of sexualized language or imagery and unwelcome sexual attention or advances
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information, such as a physical or electronic address, without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

## Enforcement

Responsibilities of project maintainers include clarifying standards of acceptable behavior and taking appropriate and fair corrective action in response to any instances of unacceptable behavior.

Maintainers have the right and responsibility to remove, edit, or reject comments, commits, code, wiki edits, issues, and other contributions that are not aligned to this Code of Conduct.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant](https://www.contributor-covenant.org), version 1.4, available at [https://www.contributor-covenant.org/version/1/4/code-of-conduct.html](https://www.contributor-covenant.org/version/1/4/code-of-conduct.html)
