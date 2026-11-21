# Social-service text pipeline

A Python prototype for turning a social-service conversation into a response and structured triage signals. Built for the Dell InnovateDash 2026 hackathon, the project explores AI guardrails around personal data, distress signals, and generated advice.

The exploration draws on public lessons about moderation and escalation on TikTok and YouTube. It is independent of those platforms. The implemented service accepts plain text through FastAPI or a command-line entry point and returns JSON. Speech recognition, a frontend, a database, and a human follow-up service are outside this repository.

[Processing flow](#processing-flow) · [Run locally](#run-locally) · [Configuration](#configuration) · [Prototype boundaries](#prototype-boundaries)

## Processing flow

1. Presidio detects supported personal-data entities locally. The anonymiser replaces them with numbered placeholders such as `[PERSON_1]`.
2. Local sentiment and natural-language-inference models analyse the original text for sentiment and escalation signals.
3. For a high-severity signal, the pipeline skips the external LLM request and returns a holding response with classification results.
4. For other inputs, the LLM receives anonymised text. The pipeline restores recognised placeholders in its response and appends support text for medium-severity signals.
5. The classifier assigns social-service categories. The output module assembles the response and signals into one JSON object.

The sequence is explicit in [pipeline/run.py](pipeline/run.py). Stages exchange the dataclasses in [pipeline/models.py](pipeline/models.py), so entity mappings, sentiment results, and response fields have separate contracts.

## Stack and design

| Technology | Role in this prototype |
| --- | --- |
| Python 3.11, FastAPI, and Pydantic | Keep the processing stages in one runtime and validate the API's text request. The CLI calls the same processing function. |
| Presidio and spaCy `en_core_web_lg` | Detect supported entities before the external request. A local entity map supports response restoration. |
| Hugging Face Transformers and Sentence Transformers | Run `cardiffnlp/twitter-roberta-base-sentiment-latest` for sentiment and `cross-encoder/nli-deberta-v3-small` for inference-based signals and categories. |
| OpenAI Python client | Call an OpenAI-compatible endpoint directly. Environment variables select the provider URL and model. |
| Docker Compose | Package the Python dependencies and model downloads together, with one API container and no database service. |

Local analysis and external response generation remain distinct. The current medium escalation threshold is `0.97`; the category threshold is `0.15`. These are prototype rules, not validated service outcomes.

## Run locally

Install Docker with Compose, then clone the project:

```sh
git clone https://github.com/Neonat/social-service-text-pipeline.git
cd social-service-text-pipeline
cp .env.example .env
```

Set the provider values described below, then start the service:

```sh
docker compose up --build
```

The initial build installs the dependencies in [requirements.txt](requirements.txt) and downloads the local language models. Compose maps host port `8005` to container port `8000`.

Send a request:

```sh
curl -X POST http://localhost:8005/process \
	-H 'Content-Type: application/json' \
	-d '{"text":"I need help understanding the available community services."}'
```

For command-line use in the running container:

```sh
docker compose exec app python -m pipeline.run \
	--text "I need help understanding the available community services."
```

## Configuration

Keep your values in the git-ignored `.env` file.

| Variable | Purpose |
| --- | --- |
| `LLM_API_KEY` | Required provider credential. The client is initialised at startup, including for requests that later bypass generation. |
| `LLM_BASE_URL` | OpenAI-compatible base URL. The template contains the original Groq development endpoint. |
| `MODEL` | Provider model identifier. Check that the template's historical value is available to your account. |

## Response contract

| Field | Meaning |
| --- | --- |
| `text` | Generated response or the high-severity holding response |
| `sentiment` | Sentiment label, score, and keyword-derived emotion |
| `escalated` | Whether an escalation signal was detected |
| `escalation_severity` | `high`, `medium`, or `null` |
| `problem_classes` | Matched social-service categories |
| `special_case` | A short input extract when no category matches |

## Development guide

| Location | Responsibility |
| --- | --- |
| [pipeline/server.py](pipeline/server.py) | `POST /process` request handling |
| [pipeline/redactor.py](pipeline/redactor.py) and [pipeline/anonymiser.py](pipeline/anonymiser.py) | Entity detection, placeholder numbering, and restoration |
| [pipeline/sentiment.py](pipeline/sentiment.py) | Sentiment, keyword rules, escalation thresholds, and holding response |
| [pipeline/classifier.py](pipeline/classifier.py) | Category descriptions and matching threshold |
| [tests/](tests/) | Component and regression checks |

Run the tests in the configured container:

```sh
docker compose exec app pytest -v
```

Some tests load language models and require their dependencies and downloads. The output-assembly check can run separately with `pytest tests/test_output.py -v` in a Python environment with pytest installed. Model quality and live LLM responses need separate evaluation.

The original [pipeline design](docs/pipeline.md) and [escalation notes](docs/escalation.md) explain the stage contracts. They contain historical examples and thresholds. Use the source files above for current behaviour. When changing an entity rule or threshold, add a synthetic regression case without real personal data.

## Prototype boundaries

Entity detection can miss sensitive content. Restored response text and `special_case` can contain original input. Local redaction therefore does not establish that every external request is free of personal data.

The holding response describes follow-up that this repository does not implement. The prototype has not been established as a clinical or emergency-response service. It has no API authentication or durable case tracking.

## License

No project license is included. Dependency licenses remain with their respective packages.
