collection-elasticsearch
===========

Run your own [ElasticSearch](http://www.elasticsearch.org) search engine for the Cooper Hewitt's collection.

The indexing code assume that you have the [cooperhewitt/collection](https://github.com/cooperhewitt/collection/) repo checked out alongside this one. 

Setup
----------

1. Clone this repo: `git clone https://github.com/cooperhewitt/collection-elasticsearch.git`
* Alongside this repo, clone our collection (this might take a while!): `git clone https://github.com/cooperhewitt/collection.git`
* `brew install elasticsearch`
* `elasticsearch`
* `bin/index-objects.py`

That's it! Then try searching. In these cases, the JSON object containing the search terms is sent as the `source` url parameter.
* [individual object](http://localhost:9200/objects/_search?q=id:18109475&pretty=1)
* [description search](http://localhost:9200/objects/_search?pretty=1&source={"query":{"match":{"description":"cat"}}})
* [description, title and epitaph search](http://localhost:9200/objects/_search?pretty=1&source={"query":{"multi_match":{"query":"cat","fields":["description", "title", "tombstone.epitaph"]}}})
* [facet on department](http://localhost:9200/objects/_search?search_type=count&pretty=1&source={"facets":{"departments":{"terms":{"field":"department_id"}}}})
* [facet on participant (sub-array facet)](http://localhost:9200/objects/_search?search_type=count&pretty=1&source={"facets":{"participants":{"terms":{"field":"participants.person_id"}}}})
* [objects between 1990-2000 (inclusive)](http://localhost:9200/objects/_search?pretty=1&source={"query":{"filtered":{"filter":{"range":{"year_start":{"gte":1990,"lte":2000}}}}}})
* [most common media in objects between 1990-2000](http://localhost:9200/objects/_search?pretty=1&search_type=count&source={"query":{"filtered":{"filter":{"range":{"year_start":{"gte":1990,"lte":2000}}}}},"aggregations":{"roles":{"terms":{"field":"medium"}}}})
* reset index: `curl -XDELETE 'http://localhost:9200/*'`

ES Overview
----------
(This section just reflects what I've been learning about ES so I can't guarantee that anything in here is the right way to do anything...)

###Queries and Filters
*Queries* should be used for full-text search and whenever a relevance score is needed. Query results are not cachable.

[Read about queries in the ES Guide.](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl-queries.html)

*Filters* should be used for exact matches and yes/no searches. They do not return a score and some of them are cached automatically. Consequently, they are (according to the docs) faster than queries.

[Read about filters in the ES Guide.](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl-filters.html)

###Constructing a Query
All searches on ES are done through queries. A query is constructed as a JSON object. An empty query, which looks like `{}`, finds everything and returns the first 10 results.

There are many kinds of queries available, and this is where ES starts to get verbose. To search the description field for `cat`, one would use a `match` query:

```json
{
	"query": {
		"match": {
			"description": "cat"
		}
	}
}
```
This is saying: I am making a `query` which is a `match` type of query, and I want to match the `description` field for the string `cat`.

The results are also sorted automatically by relevance. An object whose decription is literally "cat" will be returned before an object whose description is literally "Cat", which in turn will be returned before an object whose description is literally "cat at piano". This actually means that objects with lengthy, full descriptions might be deemed less relevant because the string match isn't as close. So this might not be the best query method for the collection's all-purpose search. Of course, you are able to do [custom sorting](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/search-request-sort.html), which might be better. But I digress...

To query multiple fields, you can use a `multi_match` query, which looks like this:

```json
{
	"query": {
		"multi_match": {
			"query":"cat",
			"fields":["description", "title", "tombstone.epitaph"]
		}
	}
}
```

This is saying: I am making a `query` which is a `multi_match` type of query, and I want to match the `query` of `cat` across the `fields` of `description`, `title` and `tombstone.epitaph`.

You will notice that ES likes the word "query" a lot. This is a little confusing to read, but the parameters required by each different type of `query` are laid out clearly in the documentation. For example, [here is the page for `multi_match`](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl-multi-match-query.html).

To use a filter, you use the `filtered` query. Hang with me -

```json
{
	"query": {
		"filtered": {
			"query": {
				"match_all": {}
			},
			"filter": {
				"range": {
					"year_start": {
						"gte": 1990,
						"lte": 2000
					}
				}
			}
		}
	}
}
```

This is saying: I am making a `query` that is a `filtered` query. The `filtered` query takes two parameters: `query` and `filter`. The `query` is just to select everything using `match_all` - this is default and can be removed, but is included here for verbosity's sake ([you could stick any query here though](http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/_combining_queries_with_filters.html)). For the `filter` parameter, I use a [`range` filter](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl-range-filter.html) where the `year_start` value is >= 1990 and <= 2000.

###Analysis and Mappings
ES automatically analyzes all fields. Analysis includes tokenization [and more](http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/analysis.html). This is great for queries but bad for filters: because filters do exact matches, if the field you wish to match on has already been tokenized, the "exact match" might be different. I ran in to this problem doing filters on accession number. The accession numbers had been tokenized, so filtering for, say, `1967-45-180` came back empty. This is easily solved, though, with mappings. When we create an index, we can use a mapping to tell certain fields to not be analyzed by ES. In Python, that looks like this:

```python
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
```

However, adding this requires reindexing. Read more about that [here](http://www.elasticsearch.org/guide/en/elasticsearch/guide/current/_finding_exact_values.html#_term_filter_with_text).
