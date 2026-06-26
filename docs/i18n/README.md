# Translation Workflow

English is the canonical source language for code comments, docstrings,
documentation, and Django `msgid` strings. Russian is the first maintained
translation.

When interface strings change:

1. Update the English source string.
2. Update the Russian translation catalog.
3. Rebuild the compiled `.mo` files in the same change set.
4. Synchronize the related English and Russian documentation.
