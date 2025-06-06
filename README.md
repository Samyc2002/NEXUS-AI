# NEXUS AI

This is my personal AI powered assistant. As of now, it can simply serach up the web and answer basic queries.
However, it is enabled by speech and keeps track of the conversation that has happened till now in a log file, which it then uses to recall everything from the past, even if the session is closed.

## Features as of today

* Search up the web to show results
* Get date, time and weather
* Get news based on topics
* Retain memory across sessions
* Fully configurable using a `config.yaml` file

## Usage

1. Clone the repository.
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Add environment variables for the Gemini API key Tavily API key, LangSmith API key, Open Weather API key and News Api Key.
4. Run the script:

```bash
python src
```

## Prerequisites

* Python 3.x
* pip
* Git (for cloning the repository)
* A Gemini API key
* A Tavily API key
* A LangSmith API key
* A Open Weather API key
* A News Api Key
