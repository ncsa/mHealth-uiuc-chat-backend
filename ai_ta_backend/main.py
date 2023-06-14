import json
import os
import re
from typing import Any, List

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
# from qdrant_client import QdrantClient
from sqlalchemy import JSON

from ai_ta_backend.vector_database import Ingest

app = Flask(__name__)
CORS(app)

# load API keys from globally-availabe .env file
load_dotenv(dotenv_path='../.env', override=True)


@app.route('/')
def index() -> JSON:
  """_summary_

  Args:
      test (int, optional): _description_. Defaults to 1.

  Returns:
      JSON: _description_
  """
  return jsonify({"Choo Choo": "Welcome to your Flask app 🚅"})

@app.route('/josh')
def second_index() -> JSON:
  """_summary_

  Args:
      test (int, optional): _description_. Defaults to 1.

  Returns:
      JSON: _description_
  """
  return jsonify({"JMinster": "Hello! 🚅"})


@app.route('/coursera', methods=['GET'])
def coursera() -> JSON:
  """_summary_

  Args:
      test (int, optional): _description_. Defaults to 1.

  Returns:
      JSON: _description_
  """
  ingester = Ingest()
  results = ingester.ingest_coursera_url("https://www.coursera.org/learn/automata", "automata")
  response = jsonify(results)
  response.headers.add('Access-Control-Allow-Origin', '*')

  return response


@app.route('/getTopContexts', methods=['GET'])
def getTopContexts():
  """Get most relevant contexts for a given search query.
  
  Return value

  ## GET arguments
  course name (optional) str
      A json response with TBD fields.
  search_query
  top_n
  
  Returns
  -------
  JSON
      A json response with TBD fields.
  Metadata fileds
  * pagenumber_or_timestamp
  * readable_filename
  * s3_pdf_path
  
  Example: 
  [
    {
      'readable_filename': 'Lumetta_notes', 
      'pagenumber_or_timestamp': 'pg. 19', 
      's3_pdf_path': '/courses/<course>/Lumetta_notes.pdf', 
      'text': 'In FSM, we do this...'
    }, 
  ]

  Raises
  ------
  Exception
      Testing how exceptions are handled.
  """
  # todo: best way to handle optional arguments?
  try:
    course_name: str = request.args.get('course_name')
    search_query: str = request.args.get('search_query')
    top_n: str = request.args.get('top_n')
  except Exception as e:
    print("No course name provided.")

  print("In /getTopContexts: ", search_query)
  if search_query is None:
    return jsonify({"error": "No parameter `search_query` provided. It is undefined."})

  ingester = Ingest()
  found_documents = ingester.getTopContexts(search_query, course_name, top_n)

  response = jsonify(found_documents)
  response.headers.add('Access-Control-Allow-Origin', '*')
  return response


@app.route('/ingest', methods=['GET'])
def ingest():
  """Recursively ingests anything from S3 filepath and below. 
  Pass a s3_paths filepath (not URL) into our S3 bucket.
  
  Ingests all files, not just PDFs. 
  
  args:
    s3_paths: str | List[str]

  Returns:
      str: Success or Failure message. Failure message if any failures. TODO: email on failure.
  """

  print("In /ingest")

  ingester = Ingest()
  s3_paths: List[str] | str = request.args.get('s3_paths')
  course_name: List[str] | str = request.args.get('course_name')
  success_fail_dict = ingester.bulk_ingest(s3_paths, course_name)

  response = jsonify(success_fail_dict)
  response.headers.add('Access-Control-Allow-Origin', '*')
  return response


@app.route('/getAll', methods=['GET'])
def getAll():
  """Get all course materials based on the course_name
  """

  print("In /getAll")

  ingester = Ingest()
  course_name: List[str] | str = request.args.get('course_name')
  distinct_dicts = ingester.getAll(course_name)
  response = jsonify({"all_s3_paths": distinct_dicts})

  response.headers.add('Access-Control-Allow-Origin', '*')
  return response


#Write api to delete s3 files for a course
@app.route('/delete', methods=['DELETE'])
def delete():
    """Delete all course materials based on the course_name
    """

    print("In /delete")

    ingester = Ingest()
    course_name: List[str] | str = request.args.get('course_name')
    s3_path: str = request.args.get('s3_path')
    success_or_failure = ingester.delete_data(s3_path, course_name)
    response = jsonify({"outcome": success_or_failure})

    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/log', methods=['GET'])
def log():
  """
  todo
  """

  print("In /log")

  ingester = Ingest()
  # course_name: List[str] | str = request.args.get('course_name')
  success_or_failure = ingester.log_to_arize('course_name', 'test', 'completion')
  response = jsonify({"outcome": success_or_failure})

  response.headers.add('Access-Control-Allow-Origin', '*')
  return response


@app.route('/DEPRICATED_S3_dir_ingest', methods=['GET'])
def DEPRICATED_S3_dir_ingest():
  """Rough ingest of whole S3 dir. Pretty handy.
  
  S3 path, NO BUCKET. We assume the bucket is an .env variable.

  Returns:
      str: Success or Failure message
  """

  ingester = Ingest()

  s3_path: List[str] | str = request.args.get('s3_path')
  # course_name: List[str] | str = request.args.get('course_name')
  ret = ingester.ingest_S3_directory(s3_path)
  if ret == 'success':
    response = jsonify({"ingest_status": "success"})
  else:
    response = jsonify({"ingest_status": ret})
  response.headers.add('Access-Control-Allow-Origin', '*')
  return response


if __name__ == '__main__':
  app.run(debug=True, port=os.getenv("PORT", default=8000))