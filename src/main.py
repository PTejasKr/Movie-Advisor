"""
main.py

Entry point for the CineMatch AI project (Movie-Advisor).

This file provides a lightweight, developer-friendly entrypoint that:
- Documents the Product Requirements Document (PRD) high-level notes.
- Checks required environment variables (`ANTHROPIC_API_KEY`, `TMDB_API_KEY`).
- Offers a simple CLI mode to run the existing `movie_advisor.main` function.
- Optionally exposes a tiny Flask server with two endpoints (`/` and `/recommend`) if `flask` is installed.

Notes for developers:
- Frontend (React/Vite) and full AI integration live in the PRD; this file provides a minimal bridge for local testing and development.
- Environment variables expected: ANTHROPIC_API_KEY, TMDB_API_KEY

See README_USAGE.txt and the project PRD for full implementation details.
"""

import os
import sys
import logging
import argparse
import json
from typing import Any

sep_line = "-" * 60

# try to import local components; handle gracefully if missing
movie_advisor_main = None
try:
    from movie_advisor import main as movie_advisor_main
except Exception:
    movie_advisor_main = None

# optional import of similarity engine for non-interactive queries
MovieSimilarityEngine = None
try:
    from similarity_engine import MovieSimilarityEngine
except Exception:
    MovieSimilarityEngine = None

# optional pretty terminal colors
try:
    from termcolor import colored
except Exception:
    def colored(text, _color=None):
        return text

# optional Flask server
FLASK_AVAILABLE = True
try:
    from flask import Flask, jsonify, request
except Exception:
    FLASK_AVAILABLE = False


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def check_env_keys():
    keys = ["ANTHROPIC_API_KEY", "TMDB_API_KEY"]
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        logging.warning(
            "Missing environment variables: %s. Add them to your environment or .env file.",
            ", ".join(missing),
        )
    else:
        logging.info("All recommended environment variables are present.")


def create_app() -> Any:
    if not FLASK_AVAILABLE:
        raise RuntimeError("Flask is not installed. Install it with 'pip install flask'.")

    app = Flask(__name__)

    @app.route("/", methods=["GET"])
    def home():
        data = {
            "app": "CineMatch AI (developer preview)",
            "description": "Minimal backend stub for the PRD: accepts movie queries and returns recommendations (stub).",
            "endpoints": ["/recommend (POST JSON {\"query\": \"Inception\"})"],
        }
        return jsonify(data)

    @app.route("/recommend", methods=["POST"])  # simple stub
    def recommend():
        payload = request.get_json(silent=True) or {}
        query = payload.get("query") or payload.get("movie")
        if not query:
            return jsonify({"error": "Provide a 'query' field in JSON payload."}), 400

        # Attempt to call movie_advisor_main if available
        if movie_advisor_main:
            try:
                # movie_advisor_main might expect no args; try both patterns
                try:
                    result = movie_advisor_main(query)
                except TypeError:
                    result = movie_advisor_main()
                # If result isn't JSON serializable, wrap it
                return jsonify({"status": "ok", "result": result})
            except Exception as e:
                logging.exception("Error while running movie_advisor_main: %s", e)
                return jsonify({"error": "Internal recommendation error"}), 500

        # Fallback stub response following PRD output format
        stub = {
            "status": "success",
            "query_movie": {"title": query, "understood": False},
            "recommendations": [],
            "additional_context": "Recommendation engine not implemented yet. Run the local movie_advisor module to process queries.",
        }
        return jsonify(stub)

    return app


def run_cli_query(query: str):
    logging.info(sep_line)
    logging.info("CineMatch AI — CLI query: %s", query)
    check_env_keys()
    # Prefer a non-interactive similarity engine for CLI queries
    if MovieSimilarityEngine:
        db_path = os.path.join(os.path.dirname(__file__), "../database/MovieDude.db")
        db_path = os.path.normpath(db_path)
        if not os.path.exists(db_path):
            logging.warning("Database not found at %s", db_path)
        else:
            try:
                engine = MovieSimilarityEngine(db_path)
                results = engine.comprehensive_similarity_search(query, 5)
                print(colored(json.dumps({"status": "ok", "query": query, "recommendations": results}, indent=2), "green"))
                return 0
            except Exception as e:
                logging.exception("Similarity engine failed: %s", e)
                print(json.dumps({"status": "error", "message": str(e)}))
                return 2

    # If similarity engine not available, fall back to interactive module if present
    if movie_advisor_main:
        try:
            try:
                out = movie_advisor_main(query)
            except TypeError:
                out = movie_advisor_main()
            print(colored(json.dumps({"status": "ok", "result": out}, indent=2), "green"))
            return 0
        except Exception as e:
            logging.exception("movie_advisor_main failed: %s", e)
            print(json.dumps({"status": "error", "message": str(e)}))
            return 2

    logging.warning("No recommendation engine available. Returning stub.")
    print(json.dumps({
        "status": "stub",
        "query": query,
        "message": "Recommendation engine not available in this environment."
    }, indent=2))
    return 0


def main(argv=None):
    setup_logging()
    parser = argparse.ArgumentParser(description="CineMatch AI - lightweight entrypoint for development")
    parser.add_argument("--serve", action="store_true", help="Run a tiny Flask server (requires Flask)")
    parser.add_argument("--host", default="127.0.0.1", help="Host for server")
    parser.add_argument("--port", default=5000, type=int, help="Port for server")
    parser.add_argument("--query", help="Run a single CLI query and print result")

    args = parser.parse_args(argv)

    check_env_keys()

    if args.serve:
        if not FLASK_AVAILABLE:
            logging.error("Flask not installed. Install with: pip install flask")
            return 3
        app = create_app()
        logging.info("Starting development server at http://%s:%s", args.host, args.port)
        app.run(host=args.host, port=args.port, debug=True)
        return 0

    if args.query:
        return run_cli_query(args.query)

    # default behavior: run movie_advisor_main if available
    if movie_advisor_main:
        logging.info(colored("Starting Simple Movie Advisor (module)...", "green"))
        try:
            try:
                movie_advisor_main()
            except TypeError:
                movie_advisor_main()
        except Exception:
            logging.exception("Error running movie_advisor_main")
            return 2
        return 0

    # nothing else to do — print helpful message
    print(colored("CineMatch AI — developer stub. Use --serve or --query. See README_USAGE.txt.", "yellow"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
