from flask import Flask, render_template, request, redirect, url_for, Response

import sys
import os

from InvertedIndex import *

jsonPath = "C:/PROYECTO-2-BD/data/data_no_filter.json"
dirPath = "C:/PROYECTO-2-BD/data/"

#test
#invertedIndex = InvertedIndex(dirPath+'index.json', dirPath+'data.json')
#invertedIndex.add_document('0704.0001', 'This is a test')
#invertedIndex.add_document('0704.0002', 'This is another test')

invertedIndex = init()


app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def buscador():
    return render_template('buscador.html')


@app.route('/resultados', methods=['POST', 'GET'])
def resultados():
    data = json.loads(open(dirPath + "data.json").read())
    query = request.args.get('query')
    topK = int(request.args.get('topK'))
    resultadostopK = invertedIndex.process_query(query, topK) 
    print(resultadostopK)
    return render_template('resultados.html', resultados=resultadostopK, data=data)
    

if __name__ == '__main__':
    app.run(debug=True)

