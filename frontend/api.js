
$(document).ready(function () {
    var progressbar = $("#progressbar");

    // --------------- Species ---------------
    var suggested_species_list = {};

    $("#species-input").autocomplete({
        source: (request, response) => {
            $.get(APP.api.search.species, { query: APP.species.name })
                .done(function (data) {
                    data.forEach((e) => {
                        suggested_species_list[e.species_name] = {ncbi_id: e.ncbi_id, kegg_id: e.kegg_id};
                    });
                    response(data.map(x => x.species_name));
                });
        },
        select: (event, ui) => {
            species_name = ui["item"]["value"];
            
            // Vue.js
            APP.species = suggested_species_list[species_name];
            APP.species.name = species_name;
            APP.wait = false;
        }
    });

    // --------------- Protein ---------------
    var suggested_protein_list = {};

    $("#protein-input").autocomplete({
        source: (request, response) => {
            if (!APP.species.ncbi_id) {
                alert("Select the species first!")
                return;
            }

            $.get(APP.api.search.protein, { query: APP.protein.name, species_id: APP.species.ncbi_id })
                .done(function (data) {
                    data.forEach((e) => {
                        suggested_protein_list[e.protein_name] = {id: e.protein_id};
                    });
                    response(data.map(x => x.protein_name));
                });
        },
        select: (event, ui) => {
            protein_name = ui["item"]["value"];

            // Vue.js
            APP.protein = suggested_protein_list[protein_name];
            APP.protein.name = protein_name;
        }
    });

    $("#protein-btn").click(() => {
        // wait
        progressbar.progressbar("option", "value", false);


        var threshold = parseFloat(APP.threshold.value);
        $.get(APP.api.subgraph.protein, { protein_id: APP.protein.id, threshold: threshold })
            .done(function (subgraph) {
                var data = protein_subgraph_to_visjs_data(subgraph);
                visualize_visjs_data(data, false);

                // Vue.js
                APP.visualization.title = APP.protein.name;

                // wait is over
                progressbar.progressbar("option", "value", 0);
                APP.wait = false;
            });
    });

    // --------------- Pathway ---------------
    var suggested_pathway_list = {};

    $("#pathway-input").autocomplete({
        source: (request, response) => {
            if (!APP.species.ncbi_id) {
                alert("Select the species first!")
                return;
            }

            $.get(APP.api.search.pathway, { query: APP.pathway.name, species_id: APP.species.ncbi_id })
                .done(function (data) {
                    data.forEach((e) => {
                        suggested_pathway_list[e.pathway_name] = {id: e.pathway_id};
                    });
                    response(data.map(x => x.pathway_name));
                });
        },
        select: (event, ui) => {
            pathway_name = ui["item"]["value"];

            // Vue.js
            APP.pathway = suggested_pathway_list[pathway_name];
            APP.pathway.name = pathway_name;
        }
    });

    $("#pathway-btn").click(() => {
        // wait
        progressbar.progressbar("option", "value", false);

        var threshold = parseFloat(APP.threshold.value);
        $.get(APP.api.subgraph.pathway, { pathway_id: APP.pathway.id, threshold: threshold })
            .done(function (subgraph) {
                var data = pathway_subgraph_to_visjs_data(subgraph);
                visualize_visjs_data(data, false);

                // Vue.js
                APP.visualization.title = APP.pathway.name;

                // wait is over
                progressbar.progressbar("option", "value", 0);
                APP.wait = false;
            });
    });

    // --------------- Protein list ---------------
    $("#protein-list-btn").click(() => {
        if (!APP.species.ncbi_id) {
            alert("Select the species first!")
            return;
        }

        // Vue.js
        APP.visualization.title = "";

        // wait
        progressbar.progressbar("option", "value", false);

        $.get(APP.api.search.protein_list, { query: APP.protein_list.value.split('\n').join(';'), species_id: APP.species.ncbi_id })
                .done(function (data) {
                    APP.protein_list.ids = data.map(x => x.protein_id);

                    var threshold = parseFloat(APP.threshold.value);
                    $.get(APP.api.subgraph.protein_list, { protein_ids: APP.protein_list.ids.join(';'), threshold: threshold })
                        .done(function (subgraph) {
                            var data = protein_list_subgraph_to_visjs_data(subgraph);
                            visualize_visjs_data(data, false);

                            // wait is over
                            progressbar.progressbar("option", "value", 0);
                            APP.wait = false;
                        });
                });
    });

});