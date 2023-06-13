from flask import Flask, render_template, request, redirect, url_for, Response

import sys
import os
import time

from spimi import *



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
    

if __name__ == '__main__':
    app.run(debug=True)

