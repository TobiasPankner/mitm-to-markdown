# MITM to Markdown

[![Run Script](https://simple-script.com/api/badge/mitmproxy-to-markdown)](https://simple-script.com/app/mitmproxy-to-markdown)


Convert mitmdump flow files to well-formatted markdown documentation with example requests.

## Description

This tool processes captured HTTP traffic from [mitmproxy](https://mitmproxy.org/) and generates comprehensive markdown documentation. It's useful for:
- Documenting API endpoints
- Creating HTTP request examples
- Generating cURL commands from captured traffic
- Analyzing HTTP flows
- Providing AI context for API interactions and debugging

## Requirements

- Python 3.x
- mitmproxy

## Installation

1. Clone or download this repository

2. Install mitmproxy:
```bash
pip install mitmproxy
```

## Usage

### Basic Usage

Convert all requests from a flow file:
```bash
python flow_to_markdown.py flows.mitm output.md
```

### Filtering Requests

Include only specific paths:
```bash
python flow_to_markdown.py flows.mitm output.md --filter "/api/*"
```

Include multiple patterns:
```bash
python flow_to_markdown.py flows.mitm output.md --filter "/api/users/*" "/api/posts/*"
```

Exclude certain paths:
```bash
python flow_to_markdown.py flows.mitm output.md --exclude "/health" "/metrics"
```

Combine include and exclude patterns:
```bash
python flow_to_markdown.py flows.mitm output.md --filter "/api/*" --exclude "*/internal/*"
```

### Pattern Syntax

Patterns support three formats:

1. **Wildcards**: Use `*` to match any characters, `?` to match a single character
   - `/api/*` matches `/api/users`, `/api/posts/123`, etc.
   - `/api/user?` matches `/api/users`, `/api/user1`, etc.

2. **Regex**: Use regular expressions for complex patterns
   - `^/api/v[0-9]+/` matches `/api/v1/`, `/api/v2/`, etc.
   - `/users/[0-9]+$` matches paths ending with `/users/123`

3. **Substring**: Simple text matching
   - `/api/` matches any path containing `/api/`

## Output Format

The generated markdown includes:

- **Request details**: Method, URL, host, headers, query parameters, and body
- **Response details**: Status code, headers, and body
- **cURL example**: Ready-to-use cURL command for each request
- **Syntax highlighting**: Automatic detection for JSON, XML, JavaScript, etc.

## Example Output

The tool generates markdown documentation like:

```markdown
## GET https://api.example.com/users/123

### Request

**GET** `/users/123`

**Host:** `api.example.com:443`

**Headers:**
```
authorization: Bearer token123
content-type: application/json
```

### Response

**Status:** `200 OK`

**Body:**
```json
{
  "id": 123,
  "name": "John Doe"
}
```

### cURL Example

```bash
curl -X GET 'https://api.example.com/users/123' \
  -H 'authorization: Bearer token123' \
  -H 'content-type: application/json'
```
```

## License

This project is open source and available for use and modification.
