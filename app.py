from flask import Flask, render_template, request, redirect, url_for, Response
from database import connector
from sqlalchemy import text

import sys
import os
import time

from spimi import *

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
    
    start_time = time.time()

    resultadostopK = spimi.process_query(query, topK) 
    
    elapsed_time = time.time() - start_time
    print("Tiempo de ejecucion: %s segundos", elapsed_time)
    return render_template('resultados.html', resultados=resultadostopK, data=data, elapsed_time=elapsed_time)


@app.route('/resultados_sql', methods = ['POST', 'GET'])
def resultados_sql():
    query = request.args.get('query')
    topK = request.args.get('topK')

    db_session = db.getSession(engine)
    sql = text(f'''
    select id, abstract, ts_rank_cd(abstract_idx, query) as rank
    from papers, plainto_tsquery('english', '{query}') query
    where query @@ abstract_idx
    order by rank desc
    limit {topK};
    ''')
    start_time = time.time()
    respuesta = db_session.execute(sql)
    elapsed_time = time.time() - start_time
    db_session.close()
    
    return render_template('resultados_sql.html', resultados_sql=respuesta, elapsed_time=elapsed_time)


if __name__ == '__main__':
    app.run(debug=True)

