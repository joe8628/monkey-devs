# Docstring Writing

Add Google-style docstrings to every public function, class, and module that lacks one.

Format:
```python
def function(param: Type) -> ReturnType:
    """One-sentence summary.

    Args:
        param: Description of the parameter.

    Returns:
        Description of the return value.

    Raises:
        ErrorType: When this error is raised.
    """
```

Rules:
- One-sentence summary on the first line
- Include Args, Returns, Raises sections only when they add information not obvious from the signature
- Do not add docstrings to private functions (prefixed with `_`) unless they are complex
- Edit source files in place using filesystem_write
