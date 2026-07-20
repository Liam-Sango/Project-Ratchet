# AI Use Disclosure

## Overview

Given a constrained implementation timeline, large language models (LLMs) were used in a controlled and limited capacity throughout development. The primary roles were guidance, non-functional cleanup, testing support, and environment setup. Functional code generation was restricted to a small number of explicitly justified cases and is recorded below.

## Standard LLM Use

1. **Automated function testing**  
   An LLM assisted in exercising manually written code. Issues identified were corrected manually, without autonomous editing of production logic.

2. **Commit message generation**  
   An LLM drafted commit messages during development. Final messages reflect my intent for each change set.

3. **Code formatting and non-functional cleanup**  
   An LLM was used to clean non-functional aspects of the code (for example structure and formatting). Such use is noted in the relevant commit messages.

4. **Library and environment management**  
   LLMs assisted with dependency selection and Python environment setup.

5. **Implementation guidance**  
   An LLM was used in an advisory capacity (chat mode) to support design and sequencing decisions. Code was not applied autonomously under this mode; implementation decisions remained with me.

6. **File skeletons**  
   An LLM generated empty or stub file structures for later manual implementation. Such use is noted in the relevant commit messages.

## Functional Code Generation

In a limited set of cases, LLM assistance was judged justified for producing functional code. Each instance and its rationale is documented below.

1. **Commit `3a9f895f6080cdac760b96cda44bf9f72d2d905a` — Steganography implementation**  
   Early in development it became clear that general-purpose steganography libraries would not meet project requirements (keyed capacity layout, controlled length prefix contracts, and integration with the existing stack). An LLM was therefore used to produce a custom LSB-based implementation tailored to those requirements. The module was reviewed and integrated before use.

2. **Commit `2553b5f2ce088419b05d1895f7c9b40778fbe839` — `main.py` server path completion**  
   During late-stage work on `main.py`, a large block of existing code required mechanical reindentation (on the order of 50+ lines). That refactor was delegated to an LLM for speed. Without narrower prompting, the model also completed unfinished portions of the implementation rather than only reformatting. The resulting changes were retained after review so the unintentional completion would not need to be re-derived from scratch; residual risk is acknowledged and was mitigated by subsequent manual testing of the affected server path.

## Scope Commitment

Beyond the instances listed above, functional core logic was authored and revised solely by Liam Sango. Disclosure of LLM assistance is intended to support transparent assessment of process and ownership of the work.
