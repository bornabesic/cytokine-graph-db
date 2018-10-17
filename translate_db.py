import sys
import psycopg2
import py2neo
import argparse

import sql_queries as SQL
import cypher_queries as Cypher
import database
from utils import pair_generator, rstrip_line_generator, read_table, batches

def main():
    # Parse CLI arguments
    args_parser = argparse.ArgumentParser(
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )

    args_parser.add_argument(
        "--credentials",
        type = str,
        help = "Path to the credentials JSON file that will be used",
        default = "credentials.json"
    )

    args_parser.add_argument(
        "--kegg_organism_id",
        type = str,
        help = "KEGG organism ID",
        default = "hsa"
    )

    args = args_parser.parse_args()
    KOID = args.kegg_organism_id

    # Parse the standard input (until EOF)
    input_stdin = sys.stdin.read()
    lines = input_stdin.split("\n")
    lines.remove("")

    only_species = (len(lines) == 1)

    if not only_species and len(lines) < 3:
        print(
            """
            Expected format (species and optionally at least two proteins):
            <species name>
            [<protein> ...]
            """
        )
        sys.exit(1)

    species = lines[0]
    proteins = lines[1:]

    # Useful functions
    score_channel_map = {
        6: "coexpression",
        8: "experiments",
        10: "database",
        12: "textmining",
        14: "neighborhood",
        15: "fusion",
        16: "cooccurence"
    }

    # Maps evidence channel ids to channel names (score_channel_map values)
    def decode_evidence_scores(evidence_scores):
        params = { channel: None for channel in score_channel_map.values()}
        for score_id, score in evidence_scores:
            if score_id not in score_channel_map:
                continue

            score_type = score_channel_map[score_id]
            params[score_type] = score
        return params

    # Connect to the databases
    postgres_connection, neo4j_graph = database.connect(credentials_path = args.credentials)

    # Read KEGG data
    # Compounds
    compounds = dict()
    for id, name in read_table("KEGG/data/kegg_compounds.{}.tsv".format(KOID), (str, str), delimiter = "\t", header = True):
        compounds[id] = {
            "id": id,
            "name": name
        }

    print("Writing compounds...")
    num_compounds = 0
    for batch in batches(compounds.values(), batch_size = 1024):
        num_compounds += len(batch)
        print("{}".format(num_compounds), end = "\r")
        Cypher.add_compound(neo4j_graph, {
            "batch": batch
        })
    print()

    # Diseases
    diseases = dict()
    for id, name in read_table("KEGG/data/kegg_diseases.{}.tsv".format(KOID), (str, str), delimiter = "\t", header = True):
        diseases[id] = {
            "id": id,
            "name": name
        }

    print("Writing diseases...")
    num_diseases = 0
    for batch in batches(diseases.values(), batch_size = 1024):
        num_diseases += len(batch)
        print("{}".format(num_diseases), end = "\r")
        Cypher.add_disease(neo4j_graph, {
            "batch": batch
        })
    print()

    # Drugs
    drugs = dict()
    for id, name in read_table("KEGG/data/kegg_drugs.{}.tsv".format(KOID), (str, str), delimiter = "\t", header = True):
        drugs[id] = {
            "id": id,
            "name": name
        }

    print("Writing drugs...")
    num_drugs = 0
    for batch in batches(drugs.values(), batch_size = 1024):
        num_drugs += len(batch)
        print("{}".format(num_drugs), end = "\r")
        Cypher.add_drug(neo4j_graph, {
            "batch": batch
        })
    print()

    # Create KEGG data index
    Cypher.create_kegg_index(neo4j_graph)

    # Pathways
    pathways = dict()

    gene2pathways = dict()
    for id, name, description, classes, genes_external_ids, diseases_ids, drugs_ids, compounds_ids in read_table(
        "KEGG/data/kegg_pathways.{}.tsv".format(KOID),
        (str, str, str, str, str, str, str, str),
        delimiter = "\t",
        header = True
    ):
        pathways[id] = {
            "id": id,
            "name": name,
            "description": description,
            "classes": classes.split(";"),
            "diseases": list(map(lambda did: diseases[did], diseases_ids.split(";"))) if len(diseases_ids) > 0 else [],
            "drugs": list(map(lambda did: drugs[did], drugs_ids.split(";"))) if len(drugs_ids) > 0 else [],
            "compounds": list(map(lambda cid: compounds[cid], compounds_ids.split(";")))  if len(compounds_ids) > 0 else []
        }

        for gene_external_id in genes_external_ids.split(";"):
            if gene_external_id not in gene2pathways:
                gene2pathways[gene_external_id] = list()

            gene2pathways[gene_external_id].append(id)

    # Get the species id
    species_id = SQL.get_species_id(postgres_connection, species)
    if species_id is None:
        print("Species not found!")
        sys.exit(1)

    # Clean the Neo4j database
    print("Cleaning the old data from Neo4j database...")
    neo4j_graph.delete_all()

    # Translate the database for all species proteins
    if only_species:
        # STRING
        # Get all proteins
        proteins = SQL.get_proteins(
            postgres_connection,
            species_id = species_id
        )
        # Get protein - protein association
        associations = SQL.get_associations(
            postgres_connection,
            species_id = species_id
        )
        # Get protein - protein functional prediction
        actions = SQL.get_actions(
            postgres_connection,
            species_id = species_id
        )

        # Neo4j
        print("Writing proteins...")
        num_proteins = 0
        for batch in batches(proteins, batch_size = 1024):
            num_proteins += len(batch)
            print("{}".format(num_proteins), end = "\r")
            Cypher.add_protein(neo4j_graph, {
                "batch": batch
            })
        print()
        # Create protein index
        Cypher.create_protein_index(neo4j_graph)

        print("Writing associations...")
        num_associations = 0
        for batch in batches(associations, batch_size = 16384):
            num_associations += len(batch)
            print("{}".format(num_associations), end = "\r")

            def map_batch_item(item):
                item = {**item, **decode_evidence_scores(item["evidence_scores"])}
                del item["evidence_scores"]
                return item

            batch = list(map(map_batch_item, batch))

            Cypher.add_association(neo4j_graph, {
                "batch": batch
            })
        print()

        print("Writing actions...")
        num_actions = 0
        for batch in batches(actions, batch_size = 16384):
            num_actions += len(batch)
            print("{}".format(num_actions), end = "\r")
            Cypher.add_action(neo4j_graph, {
                "batch": batch
            })
        print()

    # Translate the database only for specified proteins
    else:
        # For each pair of proteins...
        for protein1, protein2 in pair_generator(proteins):
            print("{} <---> {}".format(protein1, protein2))
            # STRING
            # Get protein - protein association
            associations = SQL.get_associations(
                postgres_connection,
                species_id = species_id,
                protein1 = protein1, protein2 = protein2
            )
            # Get protein - protein functional prediction
            actions = SQL.get_actions(
                postgres_connection,
                species_id = species_id,
                protein1 = protein1, protein2 = protein2
            )

            # Neo4j
            print("Writing proteins...")
            for idx, item in enumerate(proteins):
                print("{}".format(idx + 1), end = "\r")
                Cypher.add_protein(neo4j_graph, item)
            print()

            print("Writing associations...")
            for idx, item in enumerate(associations):
                print("{}a".format(idx + 1), end = "\r")
                item = {**item, **decode_evidence_scores(item["evidence_scores"])}
                del item["evidence_scores"]

                Cypher.add_association(neo4j_graph, item)
            print()

            print("Writing actions...")
            for idx, item in enumerate(actions):
                print("{}".format(idx + 1), end = "\r")
                Cypher.add_action(neo4j_graph, item)
            print()

    print("Writing pathways...")
    num_pathways = 0
    for batch in batches(gene2pathways, batch_size = 1024):
        num_pathways += len(batch)
        print("{}".format(num_pathways), end = "\r")

        def map_batch_item(gene_external_id):
            item = {
                "external_id": gene_external_id
            }
            pathways_ids1 = gene2pathways[gene_external_id]
            item["pathways1"] = list(map(lambda pid: pathways[pid], pathways_ids1))
            return item

        batch = list(map(map_batch_item, batch))
        Cypher.update_pathways(neo4j_graph, {
                "batch": batch
            })
    print()

    print("Done!")

    # Close the PostgreSQL connection
    postgres_connection.close()

if __name__ == "__main__":
    main()