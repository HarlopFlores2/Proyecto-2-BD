from flask import Flask, render_template, request
from database import connector
from sqlalchemy import text

import sys
import os
import time
import nltk

from spimi import *

#Comentar si ya esta instalado.
#-----------
nltk.download('punkt')
nltk.download('stopwords')
#-----------


db = connector.Manager()
engine = db.createEngine()

spimi = SPIMI(10000000)
#spimi.build_index()

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def buscador():
    return render_template('buscador.html')

@app.route('/resultados', methods=['POST', 'GET'])
def resultados():
    data = spimi.data
    query = request.args.get('query')
    topK = int(request.args.get('topK'))

    # Resultados de SPIMI
    start_time = time.time()
    resultados_spimi = spimi.process_query(query, topK)
    elapsed_time_spimi = time.time() - start_time

    # Resultados de PostgreSQL
    db_session = db.getSession(engine)
    sql = text(f'''
    select id, abstract, ts_rank_cd(abstract_idx, query) as rank
    from papers, plainto_tsquery('english', '{query}') query
    where query @@ abstract_idx
    order by rank desc
    limit {topK};
    ''')
    start_time = time.time()
    resultados_sql = db_session.execute(sql)
    elapsed_time_sql = time.time() - start_time
    db_session.close()

    # Renderiza la plantilla
    return render_template(
        'resultados.html',
        resultados_spimi=resultados_spimi,
        resultados_sql=resultados_sql,
        data=data,
        elapsed_time_spimi=elapsed_time_spimi,
        elapsed_time_sql=elapsed_time_sql
    )

if __name__ == '__main__':
    app.run(debug=True)
