#!/usr/bin/env python

import sys
import json
import csv
import os
import os.path
import types
from elasticsearch import Elasticsearch

es = Elasticsearch()

import logging
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':

	whoami = os.path.abspath(sys.argv[0])

	bindir = os.path.dirname(whoami)
	rootdir = os.path.dirname(bindir)
	collectiondir = os.path.join(os.path.dirname(rootdir), 'collection')

	datadir = os.path.join(collectiondir, 'objects')

	# delete the objects index
	try:
		es.indices.delete(index='objects')
	except:
		print('first time running!')
	
	# recreate index

	# tell ES not to analyze accession numbers as they are to be taken literally
	# 
	indexParams = {
		'mappings': {
			'object': {
				'properties': {
					'accession_number': {
						'type': 'string',
						'index': 'not_analyzed'
					}
				}
			}
		}
	}

	es.indices.create(index='objects', body=indexParams)

	# loop through CSVs and add to index
	for root, dirs, files in os.walk(datadir):

		for f in files:

			path = os.path.join(root, f)
			logging.info("processing %s" % path)
	
			data = json.load(open(path, 'r'))

			es.index(index='objects', doc_type='object', id=data.get('id'), body=data)

	logging.info("done");
			
