import re
from typing import Tuple, List, Optional


class SQLSecurityException(Exception):
    """Exception raised when an analytical SQL query violates security constraints."""
    pass


FORBIDDEN_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "ATTACH", "DETACH", "PRAGMA", "TRUNCATE", "REINDEX", "VACUUM",
    "REPLACE", "EXEC", "EXECUTE", "UPSERT", "SAVEPOINT", "RELEASE",
    "ROLLBACK", "COMMIT", "BEGIN", "GRANT", "REVOKE", "INTO"
}

FORBIDDEN_INTERNAL_TABLES = {
    "SQLITE_MASTER", "SQLITE_SCHEMA", "SQLITE_TEMP_MASTER",
    "SQLITE_TEMP_SCHEMA", "SQLITE_SEQUENCE", "SQLITE_STAT1",
    "SQLITE_STAT2", "SQLITE_STAT3", "SQLITE_STAT4"
}


def strip_sql_comments(query: str) -> str:
    """
    Strips single-line (--) and multi-line (/* */) comments from SQL,
    while properly respecting string literals ('...' and "...").
    """
    output = []
    i = 0
    n = len(query)
    in_single_quote = False
    in_double_quote = False

    while i < n:
        char = query[i]

        # Handle quote toggling
        if char == "'" and not in_double_quote:
            # Check for escaped single quote '' inside single-quoted string
            if in_single_quote and i + 1 < n and query[i + 1] == "'":
                output.append("''")
                i += 2
                continue
            in_single_quote = not in_single_quote
            output.append(char)
            i += 1
            continue

        if char == '"' and not in_single_quote:
            if in_double_quote and i + 1 < n and query[i + 1] == '"':
                output.append('""')
                i += 2
                continue
            in_double_quote = not in_double_quote
            output.append(char)
            i += 1
            continue

        # If not inside quotes, check for comments
        if not in_single_quote and not in_double_quote:
            # Single-line comment --
            if char == '-' and i + 1 < n and query[i + 1] == '-':
                i += 2
                while i < n and query[i] not in ('\r', '\n'):
                    i += 1
                output.append(' ')
                continue

            # Multi-line comment /* */
            if char == '/' and i + 1 < n and query[i + 1] == '*':
                i += 2
                while i + 1 < n and not (query[i] == '*' and query[i + 1] == '/'):
                    i += 1
                i += 2  # skip */
                output.append(' ')
                continue

        output.append(char)
        i += 1

    return "".join(output)


def tokenize_sql(query: str) -> List[Tuple[str, str]]:
    """
    Tokenizes SQL text into (token_type, token_value) pairs.
    Token types:
      - 'WORD': keyword or identifier
      - 'STRING': literal string
      - 'PUNCT': punctuation (; , ( ) etc)
    """
    tokens = []
    i = 0
    n = len(query)

    while i < n:
        char = query[i]

        if char.isspace():
            i += 1
            continue

        # String literal (single quote)
        if char == "'":
            start = i
            i += 1
            while i < n:
                if query[i] == "'":
                    if i + 1 < n and query[i + 1] == "'":
                        i += 2  # escaped single quote
                    else:
                        i += 1
                        break
                else:
                    i += 1
            tokens.append(('STRING', query[start:i]))
            continue

        # Quoted identifier (double quote or backtick or square bracket)
        if char in ('"', '`'):
            quote_char = char
            start = i
            i += 1
            while i < n and query[i] != quote_char:
                i += 1
            if i < n:
                i += 1
            tokens.append(('WORD', query[start:i].strip(quote_char)))
            continue

        if char == '[':
            start = i
            i += 1
            while i < n and query[i] != ']':
                i += 1
            if i < n:
                i += 1
            tokens.append(('WORD', query[start:i].strip('[]')))
            continue

        # Punctuation
        if char in (';', '(', ')', ',', '.', '=', '<', '>', '+', '-', '*', '/', '%'):
            tokens.append(('PUNCT', char))
            i += 1
            continue

        # Word / Identifier
        start = i
        while i < n and not query[i].isspace() and query[i] not in (';', '(', ')', ',', '.', '=', '<', '>', '+', '-', '*', '/', '%', "'", '"', '`', '['):
            i += 1
        tokens.append(('WORD', query[start:i]))

    return tokens


def validate_and_sanitize_sql(raw_query: str) -> str:
    """
    Validates that a SQL query is strictly read-only, non-destructive,
    single-statement, and does not access internal SQLite metadata.
    Returns the cleaned sanitized query string ready for execution.
    Raises SQLSecurityException with specific diagnostic error on violation.
    """
    if not raw_query or not raw_query.strip():
        raise SQLSecurityException("SQL query cannot be empty.")

    # 1. Strip comments safely
    cleaned = strip_sql_comments(raw_query).strip()
    if not cleaned:
        raise SQLSecurityException("SQL query contains no executable statements.")

    # 2. Tokenize
    tokens = tokenize_sql(cleaned)
    if not tokens:
        raise SQLSecurityException("Failed to tokenize SQL query.")

    # 3. Check for multiple statements (semicolon check outside strings)
    # A trailing semicolon is acceptable, but not multiple statements
    semicolon_positions = [idx for idx, (ttype, val) in enumerate(tokens) if ttype == 'PUNCT' and val == ';']
    for pos in semicolon_positions:
        # If there are tokens after this semicolon, verify if any non-empty statements follow
        subsequent_tokens = [t for t in tokens[pos + 1:] if t[0] != 'PUNCT' or t[1] != ';']
        if subsequent_tokens:
            raise SQLSecurityException("Multi-statement execution is strictly prohibited.")

    # 4. Check initial keyword: must be SELECT or WITH
    word_tokens = [t for t in tokens if t[0] == 'WORD']
    if not word_tokens:
        raise SQLSecurityException("Query must begin with a valid SELECT or WITH statement.")

    first_word = word_tokens[0][1].upper()
    if first_word not in ("SELECT", "WITH"):
        raise SQLSecurityException(
            f"Query must begin with SELECT or WITH. Found prohibited start keyword: '{first_word}'."
        )

    # 5. Check all tokens for forbidden keywords & SQLite internal schemas
    for ttype, val in tokens:
        if ttype == 'WORD':
            val_upper = val.upper()
            if val_upper in FORBIDDEN_KEYWORDS:
                raise SQLSecurityException(
                    f"Prohibited SQL keyword detected: '{val}'. Only read-only analytical queries are permitted."
                )

            if val_upper in FORBIDDEN_INTERNAL_TABLES or val_upper.startswith("PRAGMA_"):
                raise SQLSecurityException(
                    f"Access to internal database catalog table '{val}' is strictly forbidden."
                )

    # 6. Return sanitized query without trailing semicolon
    final_query = cleaned.rstrip(';').strip()
    return final_query

