
def add_compound(graph, params):

    query = """
        UNWIND {batch} as entry
        CREATE (compound:Compound {
            id: entry.id,
            name: entry.name
        })
    """
    graph.run(query, params)

def add_disease(graph, params):

    query = """
        UNWIND {batch} as entry
        CREATE (disease:Disease {
            id: entry.id,
            name: entry.name
        })
    """
    graph.run(query, params)

def add_drug(graph, params):

    query = """
        UNWIND {batch} as entry
        CREATE (drug:Drug {
            id: entry.id,
            name: entry.name
        })
    """
    graph.run(query, params)

def add_class_parent_and_child(graph, params):

    query = """
        UNWIND {batch} as entry
        MERGE (parent:Class {
            name: entry.name_parent
        })
        MERGE (child:Class {
            name: entry.name_child
        })
        MERGE (child)-[:IN]->(parent)
    """
    graph.run(query, params)

def add_pathway(graph, params):

    query = """
        UNWIND {batch} as entry
        MATCH (class:Class {
            name: entry.class
        })
        CREATE (pathway:Pathway {
            id: entry.id,
            name: entry.name,
            description: entry.description
        })-[:IN]->(class)
    """

    graph.run(query, params)

def add_protein(graph, params):
    """
    Create a protein with the specified id, external id,
    preferred name and annotation.
    """

    query = """
        UNWIND {batch} as entry
        CREATE (protein:Protein {
            id: entry.id,
            external_id: entry.external_id,
            name: toUpper(entry.preferred_name),
            description: entry.annotation
        })
    """
    graph.run(query, params)

def add_action(graph, params):
    """
    For an existing protein - protein pair, create / update (merge) the given
    action associated with the given pathway.

    If the action's "mode" is the same, the action is updated only if the current
    provided score is higher than the previous.
    """
    
    query = """
        UNWIND {batch} as entry
        MATCH (protein1:Protein {
            id: entry.id1
        })

        MATCH (protein2:Protein {
            id: entry.id2
        })

        MERGE (protein1)-[action:ACTION {
            mode: entry.mode
        }]->(protein2)
            ON CREATE SET action.score = entry.score
            ON MATCH SET action.score = CASE action.score
                                       WHEN entry.score > action.score
                                       THEN action.score = entry.score
                                       ELSE action.score
                                       END
    """
    graph.run(query, params)

def add_association(graph, params):
    """
    For an existing protein - protein pair, create the association
    between them.
    """

    query = """
        UNWIND {batch} as entry

        MATCH (protein1:Protein {
            id: entry.id1
        })

        MATCH (protein2:Protein {
            id: entry.id2
        })

        CREATE (protein1)-[a:ASSOCIATION {
            experiments: entry.experiments,
            database: entry.database,
            textmining: entry.textmining,
            coexpression: entry.coexpression,
            neighborhood: entry.neighborhood,
            fusion: entry.fusion,
            cooccurence: entry.cooccurence,
            combined: entry.combined_score
        }]->(protein2)
    """
    graph.run(query, params)

def connect_protein_and_pathway(graph, params):

    query = """
        UNWIND {batch} as entry

        MATCH (protein:Protein {
            external_id: entry.protein_external_id
        })

        MATCH(pathway:Pathway {
            id: entry.pathway_id
        })

        CREATE (protein)-[:IN]->(pathway)
    """
    graph.run(query, params)

def connect_compound_and_pathway(graph, params):

    query = """
        UNWIND {batch} as entry

        MATCH (compound:Compound {
            id: entry.compound_id
        })

        MATCH (pathway:Pathway {
            id: entry.pathway_id
        })

        CREATE (compound)-[:IN]->(pathway)
    """
    graph.run(query, params)

def connect_disease_and_pathway(graph, params):

    query = """
        UNWIND {batch} as entry

        MATCH (disease:Disease {
            id: entry.disease_id
        })

        MATCH (pathway:Pathway {
            id: entry.pathway_id
        })

        CREATE (disease)-[:IN]->(pathway)
    """
    graph.run(query, params)

def connect_drug_and_pathway(graph, params):

    query = """
        UNWIND {batch} as entry

        MATCH (drug:Drug {
            id: entry.drug_id
        })

        MATCH (pathway:Pathway {
            id: entry.pathway_id
        })

        CREATE (drug)-[:IN]->(pathway)
    """
    graph.run(query, params)

# def update_pathways(graph, params):
#     """
#     For each protein in the pathway collection, create / update (merge)
#     the pathway and associated classes, compounds, drugs and diseases.
#     """

#     query = """
#         UNWIND {batch} as entry

#         MATCH (protein1:Protein {
#             external_id: entry.external_id
#         })

#         FOREACH (p1 IN entry.pathways1 |
#             MERGE (pathway1:Pathway {
#                 id: p1.id,
#                 name: p1.name,
#                 description: p1.description
#             })
#             CREATE (protein1)-[:IN]->(pathway1)

#             MERGE (fClass:Class {
#                 name: p1.classes[length(p1.classes) - 1]
#             })
#             MERGE (pathway1)-[:IN]->(fClass)
#             FOREACH (i IN RANGE(length(p1.classes) - 1, 1) |
#                 MERGE (cClass:Class {
#                         name: p1.classes[i]
#                 })
#                 MERGE (nClass:Class {
#                         name: p1.classes[i - 1]
#                 })
#                 MERGE (cClass)-[:IN]->(nClass)
#             )

#             FOREACH (dis1 IN p1.diseases |
#                 MATCH (disease1:Disease {
#                     id: dis1.id
#                 })
#                 MERGE (disease1)-[:IN]->(pathway1)
#             )

#             FOREACH (dr1 IN p1.drugs |
#                 MATCH (drug1:Drug {
#                     id: dr1.id
#                 })
#                 MERGE (drug1)-[:IN]->(pathway1)
#             )

#             FOREACH (com1 IN p1.compounds |
#                 MATCH (compound1:Compound {
#                     id: com1.id
#                 })
#                 MERGE (compound1)-[:IN]->(pathway1)
#             )
#         )
#     """
#     graph.run(query, params)

def create_protein_index(graph):

    queries = [
        "CREATE INDEX ON :Protein(id)",
        "CREATE INDEX ON :Protein(external_id)",
        "CREATE INDEX ON :Protein(name)"
    ]

    for query in queries:
        graph.run(query)

def create_kegg_index(graph):

    queries = [
        "CREATE INDEX ON :Compound(id)",
        "CREATE INDEX ON :Drug(id)",
        "CREATE INDEX ON :Disease(id)",
        "CREATE INDEX ON :Pathway(id)",
        "CREATE INDEX ON :Pathway(name)"
    ]

    for query in queries:
        graph.run(query)

def search_protein(graph, name):
    """
    For the given protein, return the Neo4j subgraph
    of the protein, all other associated proteins and
    the common pathways.
    """

    query = """
        MATCH (pathway:Pathway)<-[:IN]-(protein:Protein)-[association:ASSOCIATION]-(other:Protein)
        WHERE toUpper(protein.name) =~ (".*" + toUpper({name}) + ".*")
        RETURN protein, association, other, pathway
    """

    param_dict = dict(name = name)
    return graph.run(query, param_dict)

def search_pathway(graph, name):
    """
    For the given pathway, return the Neo4j subgraph
    of the pathway, all contained proteins and
    the class hierarchy of the pathway.
    """

    query = """
        MATCH (class:Class)<-[:IN*]-(pathway:Pathway)<-[:IN]-(protein:Protein)
        WHERE toUpper(pathway.name) =~ (".*" + toUpper({name}) + ".*")
        RETURN pathway, COLLECT(DISTINCT class) AS classes, COLLECT(protein)
    """

    param_dict = dict(name = name)
    return graph.run(query, param_dict)

