
env:
	conda env create -f environment.yml

test:
	# Check the syntax
	find . -name "*.py" | xargs pylint -E

	# Load the toy database
	psql -U postgres -h localhost -p 5432 -c "DROP DATABASE string;"
	psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE string;"
	psql -U postgres -h localhost -p 5432 string < sql/dump.schema.psql
	psql -U postgres -h localhost -p 5432 string < sql/dump.test.psql

	# Run the unit tests
	python tests/test_kegg.py
	python tests/test_sql_queries.py
	python build_graph_db.py --species_name "Mus musculus"
	python tests/test_fuzzy_search.py
	python tests/test_cypher_queries.py
