# ledgerly-api

A small expense-tracking API (Flask + SQLite).

## Run

```bash
pip install -r requirements.txt
flask --app app run
```

## Endpoints

| method | path | what |
|---|---|---|
| POST | `/signup` | create a user (`username`, `password`) |
| POST | `/login` | returns a session token |
| POST | `/expenses` | add an expense (`amount`, `note`) - needs `Authorization: Bearer <token>` |
| GET | `/expenses` | list your expenses - needs the token |

## Test

```bash
pytest
```
