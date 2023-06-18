import os
import sys
import time

import nltk
from flask import Flask, render_template, request
from sqlalchemy import text

import spimi
from database import connector
from util import read_json_at_offset, unpickle_file

# Comentar si ya esta instalado.
# -----------
nltk.download("punkt")
nltk.download("stopwords")
# -----------

json_offsets = unpickle_file("json_offsets.ind")

db = connector.Manager()
engine = db.createEngine()

query = spimi.Query(
    "index.ind",
    unpickle_file("offsets.ind"),
    unpickle_file("idfs.ind"),
    unpickle_file("norms.ind"),
)

app = Flask(__name__)


@app.route("/", methods=["POST", "GET"])
def buscador():
    return render_template("buscador.html")


@app.route("/resultados", methods=["POST", "GET"])
def resultados():
    q = request.args.get("query")
    topK = int(request.args.get("topK"))

    # Resultados de SPIMI
    start_time = time.time()
    resultados_spimi = query.query(q, topK)
    elapsed_time_spimi = time.time() - start_time

    # Resultados de PostgreSQL
    db_session = db.getSession(engine)
    sql = text(
        f"""
    select id, abstract, ts_rank_cd(abstract_idx, query) as rank
    from papers, plainto_tsquery('english', '{query}') query
    where query @@ abstract_idx
    order by rank desc
    limit {topK};
    """
    )
    start_time = time.time()
    resultados_sql = db_session.execute(sql)
    elapsed_time_sql = time.time() - start_time
    db_session.close()

    # Renderiza la plantilla
    return render_template(
        "resultados.html",
        resultados_spimi=resultados_spimi,
        resultados_sql=resultados_sql,
        elapsed_time_spimi=elapsed_time_spimi,
        elapsed_time_sql=elapsed_time_sql,
        json_offsets=json_offsets,
        json_file='arxiv-metadata-oai-snapshot.json',
        read_json_at_offset=read_json_at_offset,
    )


if __name__ == "__main__":
    app.run(debug=True)
