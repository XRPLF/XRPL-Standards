---
name: xls-amendment-patches
description: Write nested XLS amendment patches. Use when adding a fix* or feature amendment to an existing XLS, creating XLS-NNNN/N.k/ files, numbering 65.1.1-style feature patches, or documenting fixCleanup* changes in one file.
---

Read [XLS-1 §4.4.4 Subsequent amendments](../../../XLS-0001-xls-process/README.md#444-subsequent-amendments) and follow it. That section is the source of truth for patch layout, numbering, parent updates, and the fix-versus-feature split.

Cite rippled for every normative claim. Do not invent amendment names or behavior. Nested `N.k/` files are outside the `XLS-*/README.md` CI glob; still check preambles by hand and run `xls-template-conformity` on the parent `README.md`.
